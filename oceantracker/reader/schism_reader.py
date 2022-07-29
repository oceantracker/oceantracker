import numpy as np
from numba import  njit
from datetime import  datetime, timedelta
from oceantracker.reader.generic_unstructured_reader import GenericUnstructuredReader
from oceantracker.fields.util.fields_util import  depth_aver_SlayerLSC_in4D

from copy import  copy
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util import time_util
from oceantracker.fields._base_field import _BaseField


class SCHSIMreaderNCDF(GenericUnstructuredReader):
    # loads a standard SCHISM netcdf output file with nodal data
    # variable names can be tweaked via maps in shared_params, if non-standard names used

    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({  # if be used along side 3D vel
                        'hgrid_file_name': PVC(None, str),
                        'field_variables': {'water_velocity': PLC(['hvel'], [str], fixed_len=2),
                                              'water_depth': PVC('depth', str),
                                              'tide': PVC('elev', str),
                                              'water_temperature': PVC(None, str),
                                               'water_salinity': PVC(None, str)},
                                               'water_velocity_depth_average': PVC(None, str),


                        'dimension_map': {'node': PVC('nSCHISM_hgrid_node', str),
                                                                     'z': PVC('nSCHISM_vgrid_layers', str),
                                                                     'time': PVC('time', str),
                                                                      'vector2Ddim': PVC('two', str)
                                                                    },
                        'grid_variables': {'time':PVC('time',str),
                                    'x':PLC(['SCHISM_hgrid_node_x', 'SCHISM_hgrid_node_y'], [str], fixed_len= 2),
                                    'zlevel': PVC('zcor',str),
                                    'bottom_cell_index': PVC('node_bottom_index',str),
                                     'triangles': PVC('SCHISM_hgrid_face_nodes',str),                                                                      },
                                               })
        self.class_doc(description='Reads SCHISM netCDF output files')

    def _file_checks(self, file_name, msg_list):
        # sort out which velocity etc are there and adjust field variables
        nc = NetCDFhandler(file_name, 'r')
        params = self.params
        fv= params['field_variables']

        if not nc.is_var('hvel') or params['depth_average']:
            # run in depth averaged mode if only a 2D schsim run
            params['depth_average']= True
            fv['water_velocity'] = ['dahv'] # one vector component

        if 'water_velocity' in self.params['field_variables_to_depth_average'] and nc.is_var('dahv'):
            # used depth average vel in fil instead of doing depth average
            self.params['field_variables_to_depth_average'].remove('water_velocity')
            fv['water_velocity_depth_average'] = ['dahv']

        if  nc.is_var('minimum_depth'):
            # use schism min depth times 1.5 to allow for diff due to interp cell tide to nodes in schisms output
            params['minimum_total_water_depth']= 1.5*float(nc.read_a_variable('minimum_depth'))

        nc.close()

        msg_list= super()._file_checks(file_name,msg_list)
        return msg_list

    def read_time(self, nc, file_index=None):
        vname=self.params['grid_variables']['time']
        if file_index is None : file_index =np.arange(nc.get_var_shape(vname)[0])

        time = nc.read_a_variable(vname,file_index)
        base_date=  [ int(float(x)) for x in nc.get_var_attr('time','base_date').split()]

        d0= datetime(base_date[0], base_date[1], base_date[2], base_date[3], base_date[4])
        time = time + time_util.date_to_seconds(d0)

        if self.params['time_zone'] is not None:
            time += self.params['time_zone']*3600.
        return time

    def read_triangles(self, nc):
        # schism has 1 based index
        data = super().read_triangles(nc)
        data  -=1 # reserve zeros in 4th colum
        return data

    def read_bottom_cell_index(self, nc, num_tri=None):
        si= self.shared_info
        data = super().read_bottom_cell_index(nc, num_tri=num_tri)
        if nc.is_var(self.params['grid_variables']['bottom_cell_index']):
            # if read from file, then need to make zero based
            data -= 1
        return data

    def read_open_boundary_data(self, grid):
        # read hgrid file for open boundary data
        grid['grid_outline']['open_boundary_nodes'] = []
        if self.params['hgrid_file_name'] is  None: return grid

        with open(self.params['hgrid_file_name']) as f:lines = f.readlines()

        id = []
        for i, elem in enumerate(lines):
            if 'Number of nodes for open boundary' in elem:
                id.append(i)
        if len(id) > 0:
            tri_open_bound_node_list=   [ [] for _ in range( grid['triangles'].shape[0]) ]
            for i in id:
                n_nodes = int(lines[i].split('=')[0])
                nodes=[]
                for n in range(n_nodes):
                    l = lines[i+1+n].strip('\n')
                    nodes.append(int(l))
                ob_nodes = np.asarray(nodes, dtype=np.int32)-1
                grid['node_type'][ob_nodes] = 3 # mark as open nodes
                grid['grid_outline']['open_boundary_nodes'].append(ob_nodes) # get zero based node number

                # build triangle to open nodes map
                for node in ob_nodes:
                    for tri in grid['node_to_tri_map'][node]:
                        tri_open_bound_node_list[tri].append(node)
                    a=1

            # find triangles with 2 open nodes, and adjust adjacency from -1 to -2 for those faces
            for n, l in enumerate(tri_open_bound_node_list):
                if len(l) > 1:
                    # look at each boundary face in this triangle and see if it has two open boundary node, so is open
                    for nface in np.flatnonzero(grid['adjacency'][n,:] == -1):
                        face_nodes= grid['triangles'][n,(nface + 1+ np.arange(2) ) % 3]
                        if face_nodes[0] in tri_open_bound_node_list[n] and face_nodes[1] in tri_open_bound_node_list[n] :
                            grid['adjacency'][n, nface] = -2 # mark as open
        grid['has_open_boundary_data'] = True
        return grid

@njit
def patch_bottom_velocity_to_make_it_zero(vel_data, bottom_cell_index):
    # ensure velocity vector at bottom is zero, as patch LSC vertical grid issue with nodal values spanning change in number of depth levels
    for nt in range(vel_data.shape[0]):
        for node in range(vel_data.shape[1]):
            bottom_node= bottom_cell_index[node]

            for component in range(vel_data.shape[3]):
                vel_data[nt, node, bottom_node, component] = 0.



