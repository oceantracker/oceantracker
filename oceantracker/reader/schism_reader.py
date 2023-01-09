import numpy as np
from numba import  njit
from datetime import  datetime, timedelta
from oceantracker.reader.generic_unstructured_reader import GenericUnstructuredReader
from copy import  copy
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util import time_util
from oceantracker.fields.reader_field import ReaderField
from oceantracker.util.triangle_utilities_code import split_quad_cells
from oceantracker.util.triangle_utilities_code import append_split_cell_data

class SCHSIMreaderNCDF(GenericUnstructuredReader):
    # loads a standard SCHISM netcdf output file with nodal data
    # variable names can be tweaked via maps in shared_params, if non-standard names used

    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({  # if be used alongside 3D vel
                        'hgrid_file_name': PVC(None, str),
                        'field_variables': {'water_velocity': PLC(['hvel'], [str], fixed_len=2),
                                            'water_depth': PVC('depth', str),
                                            'tide': PVC('elev', str)},
                                })
        self.class_doc(description='Reads SCHISM netCDF output files')
        self.clear_default_params(['grid_variables', 'one_based_indices','dimension_map']) # only used in generic reader

    def is_hindcast3D(self, nc): return  nc.is_var('hvel')

    def get_number_of_z_levels(self, nc):  return nc.get_dim_size('nSCHISM_vgrid_layers')

    def is_var_in_file_3D(self, nc, var_name_in_file):  return nc.is_var_dim(var_name_in_file, 'nSCHISM_vgrid_layers')

    def is_file_variable_time_varying(self, nc, var_name_in_file):  return nc.is_var_dim(var_name_in_file, 'time')

    def get_num_vector_components_in_file_variable(self,nc,file_var_name):
        if nc.is_var_dim(file_var_name, 'two'):
            n_comp = 2
        elif nc.is_var_dim(file_var_name, 'three'):
            n_comp = 3
        else:
            n_comp = 1
        return  n_comp

    def read_zlevel_as_float32(self, nc, file_index, zlevel_buffer, buffer_index):
        # read in place
        zlevel_buffer[buffer_index,:] = nc.read_a_variable('zcor', sel=file_index).astype(np.float32)

    def read_dry_cell_data(self,nc,file_index, is_dry_cell_buffer, buffer_index):
        # calculate dry cell flags, if any cell node is dry
        grid = self.grid
        # get dry cells for each triangle allowing for splitting of quad cells
        data_added_to_buffer = nc.read_a_variable('wetdry_elem', file_index)
        is_dry_cell_buffer[buffer_index, :] = append_split_cell_data(grid, data_added_to_buffer, axis=1)

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
            # use schism min depth times 1.2 to allow for diff due to interp cell tide to nodes in schisms output
            params['minimum_total_water_depth']= 1.2*float(nc.read_a_variable('minimum_depth'))

        nc.close()

        msg_list= super()._file_checks(file_name,msg_list)
        return msg_list

    def make_non_time_varying_grid(self,nc, grid):
        grid =super().make_non_time_varying_grid(nc, grid)
        return grid


    def read_time(self, nc, file_index=None):
        if file_index is None:
            time = nc.read_a_variable('time', sel=None) # read all times
        else:
            time = nc.read_a_variable('time', sel=file_index)

        base_date=  [ int(float(x)) for x in nc.get_var_attr('time','base_date').split()]

        d0= datetime(base_date[0], base_date[1], base_date[2], base_date[3], base_date[4])
        time = time + time_util.date_to_seconds(d0)

        if self.params['time_zone'] is not None:
            time += self.params['time_zone']*3600.
        return time

    def read_bottom_cell_index_as_int32(self, nc):
        # time invariant bottom cell index, which varies across grid in LSC vertical grid
        grid = self.grid
        if nc.is_var('node_bottom_index'):
            data = nc.read_a_variable('node_bottom_index')
            data -= 1
            grid['vertical_grid_type'] = 'LSC'
        else:
            # Slayer grid, bottom cell index = zero
            data = np.zeros((self.grid['x'].shape[0],),dtype=np.int32)
            grid['vertical_grid_type'] = 'Slayer'

        return data.astype(np.int32)

    def read_nodal_x_float32(self, nc):
        x = np.stack((nc.read_a_variable('SCHISM_hgrid_node_x'), nc.read_a_variable('SCHISM_hgrid_node_y')), axis=1).astype(np.float32)
        if self.params['cords_in_lat_long']:
            x  = self.convert_lat_long_to_meters_grid(x)
        return x

    def read_triangles_as_int32(self, nc):
        data = nc.read_a_variable('SCHISM_hgrid_face_nodes')

        # flag quad cells for spliting
        if data.shape[1] == 4 and np.any(data > 0):
            # split quad grids buy making new triangles
            quad_cells_to_split = data[:, 3] > 0
            data = split_quad_cells(data, quad_cells_to_split)
        else:
            quad_cells_to_split = np.full((data.shape[0],),False,dtype=bool)
            
        data -= 1 # make index zero based
        
        return data.astype(np.int32), quad_cells_to_split

    def read_open_boundary_data(self, grid):
        # todo rewrite to read boundary dat and create int matrix , for open boundary and land boundary nodes and cells. flaged ass 1/2
        # and make this part of the read grid method

        # read hgrid file for open boundary data
        open_boundary_nodes = np.full((grid['x'].shape[0]),0,np.int8)
        open_boundary_adjacency= np.full_like(grid['triangles'],0,dtype=np.int8)

        if self.params['hgrid_file_name'] is  None:
            return open_boundary_nodes,open_boundary_adjacency

        with open(self.params['hgrid_file_name']) as f:lines = f.readlines()

        vals= lines[1].split()
        n_nodes= int(vals[0])
        n_tri = int(vals[1])

        n_line_open= n_nodes+n_tri+3 -1 # line with number of open boundries
        n_open= int(lines[n_line_open].split()[0])

        if n_open > 0:
            open_boundary_nodes =[]
            tri_open_bound_node_list= [ [] for _ in range(grid['triangles'].shape[0]) ]
            nl = n_line_open+1
            for n in range(n_open):
                nl += 1 # move to line with number of nodes in this open boundary
                n_nodes = int(lines[nl].split()[0])
                nodes=[]
                for n in range(n_nodes):
                    nl += 1
                    l = lines[nl].strip('\n')
                    nodes.append(int(l))
                ob_nodes = np.asarray(nodes, dtype=np.int32)-1
                open_boundary_nodes  = 1
                grid['node_type'][ob_nodes] = 3 # mark as open nodes
                open_boundary_nodes.append(ob_nodes) # get zero based node number

                # build triangle to open nodes map
                for node in ob_nodes:
                    for tri in grid['node_to_tri_map'][node]:
                        tri_open_bound_node_list[tri].append(node)


            # find triangles with 2 open nodes, and adjust adjacency from -1 to -2 for those faces
            for n, l in enumerate(tri_open_bound_node_list):
                if len(l) > 1:
                    # look at each boundary face in this triangle and see if it has two open boundary node, and  mark as  open
                    for nface in np.flatnonzero(grid['adjacency'][n,:] == -1):
                        face_nodes= grid['triangles'][n,(nface + 1+ np.arange(2) ) % 3]
                        if face_nodes[0] in tri_open_bound_node_list[n] and face_nodes[1] in tri_open_bound_node_list[n] :
                            open_boundary_adjacency[n, nface] = 1 # mark as open

        return open_boundary_nodes,open_boundary_adjacency



    def preprocess_field_variable(self, nc,name, data):

        if name =='water_velocity' and data.shape[2] > 1:
            # for 3D schism velocity partial fix for  non-zero hvel at nodes where cells in LSC grid span a change in bottom_cell_index
            data = patch_bottom_velocity_to_make_it_zero(data, self.grid['bottom_cell_index'])

        return data

@njit
def patch_bottom_velocity_to_make_it_zero(vel_data, bottom_cell_index):
    # ensure velocity vector at bottom is zero, as patch LSC vertical grid issue with nodal values spanning change in number of depth levels
    for nt in range(vel_data.shape[0]):
        for node in range(vel_data.shape[1]):
            bottom_node= bottom_cell_index[node]
            for component in range(vel_data.shape[3]):
                vel_data[nt, node, bottom_node, component] = 0.
    return vel_data



