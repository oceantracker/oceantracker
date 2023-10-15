from oceantracker.reader._base_reader import _BaseReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util

import numpy as np
from datetime import datetime
from oceantracker.reader.util import hydromodel_grid_transforms

from oceantracker.reader.util import reader_util

#todo add required variables and dimensions lists to sensure
#todo friction velocity from bottom stress magnitude, tauc if present
#todo use A_H and A_V fields in random walk
#todo implement depth average mode using depth average variables in the file

class unstructured_FVCOM(_BaseReader):
    # loads a standard SCHISM netcdf output file with nodal data
    # variable names can be tweaked via maps in shared_params, if non-standard names used

    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({ 'field_variable_map': {'water_velocity': PLC(['u','v'], [str], fixed_len=2),
                                                          'water_depth': PVC('h', str,doc_str='maps standard internal field name to file variable name'),
                                                          'tide': PVC('zeta', str,doc_str='maps standard internal field name to file variable name')},

                                  'dimension_map': {'time': PVC('time', str),
                                                    'node': PVC('node', str),
                                                    'triangle': PVC('nele', str),
                                                    'z': PVC('siglev', str, doc_str='name of dim for vertical layer boundaries'),
                                                    'z_mid_layer': PVC('siglay', str, doc_str=' name of dimension for middle of layers'),
                                                    },

                                  'grid_variable_map': {'time': PVC('time', str),
                                                        'x': PLC(['x', 'y'], [str], fixed_len=2),
                                                        'zlevel': PVC('siglev', str,doc_str=' name of fractional layer boundary levels'),
                                                        'zlevel_mid_cell': PVC('siglay', str, doc_str=' name of fractional mid vertical cell  boundary'),
                                                        'triangles': PVC('nv', str),
                                                        'bottom_cell_index': PVC(None, str),
                                                        'is_dry_cell': PVC(None, np.int8, doc_str='Time variable flag of when cell is dry, 1= is dry cell')},
                                })

    def initial_setup(self):
        super().initial_setup()
        grid= self.grid
        # make distance weighting matrix for triangle center values at nodal points
        grid['cell_center_weights'] = hydromodel_grid_transforms.calculate_cell_center_weights_at_node_locations(
                                                    grid['x'], grid['x_center'],grid['node_to_tri_map'],grid['tri_per_node'])

    def is_3D_hydromodel(self, nc):
        return True if nc.is_var_dim(self.params['field_variable_map']['water_velocity'][0], self.params['dimension_map']['z_mid_layer']) else False


    def is_3D_variable(self,nc, var_name):
        # is variable 3D, if layer or
        return  nc.is_var_dim(var_name,self.params['dimension_map']['z']) or   nc.is_var_dim(var_name,self.params['dimension_map']['z_mid_layer'])

    def additional_setup_and_hindcast_file_checks(self, nc, msg_logger):
        # include vertical velocity if in file
        if nc.is_var('ww'):
            self.params['field_variables']['water_velocity'].append('ww')
        else:
            msg_logger.msg('No vertical velocity "ww" variable in FVCOM hydro-model files, assuming vertical_velocity=0', note=True)

    def is_var_in_file_3D(self, nc, var_name_in_file): return any(x in  nc.all_var_dims(var_name_in_file) for x in ['siglay','siglev'])


    def get_num_vector_components_in_file_variable(self,nc,file_var_name): return 1 # no vector vararibles

    def is_file_variable_time_varying(self, nc, var_name_in_file): return  'time' in nc.all_var_dims(var_name_in_file)


    def build_vertical_grid(self, nc, grid):

        # add time invariant vertical grid variables needed for transformations
        # sigma level fractions required to build zlevel after reading  tide
        # siglay, siglev are <0 and  look like layer fraction from free surface starting at top moving down, convert to fraction from bottom starting at bottom

        # first values in z axis is the top? so flip
        params = self.params
        dm = params['dimension_map']
        gm = params['grid_variable_map']

        grid['z_fractions']              = 1. + np.flip(nc.read_a_variable(gm['zlevel'], sel=None).astype(np.float32).T, axis=1)  # layer boundary fractions
        grid['z_fractions_layer_center'] =  1.+ np.flip(nc.read_a_variable(gm['zlevel_mid_cell'], sel=None).astype(np.float32).T,axis=1)  # layer center fractions
        grid['vertical_grid_type'] = 'S-sigma'

        grid['bottom_cell_index'] = np.zeros((grid['x'].shape[0],), dtype=np.int32)
        grid['nz'] = nc.dim_size(dm['z'])



        # non-uniform sigma layers
        s = [self.params['time_buffer_size'], grid['x'].shape[0], grid['nz']]
        grid['zlevel'] = np.zeros(s, dtype=np.float32, order='c')

        return grid

    def read_nodal_x(self, nc, grid):
        # get node location in meters
        # also record cell center x as well to be used for get nodal field vals from values at center, eg velocity

        if  self.params['cords_in_lat_long'] or np.all(nc.read_a_variable('x')==0): #  use lat long? as x may sometimes be all be zeros

            grid['lat']= nc.read_a_variable('lat')
            grid['lon']=nc.read_a_variable('lon')
            grid['x'] = self.convert_lon_lat_to_meters_grid(np.stack((grid['lon'],grid['lat'] ), axis=1).astype(np.float64))

            grid['x_center'] = np.stack((nc.read_a_variable('lonc'), nc.read_a_variable('latc')), axis=1)
            grid['x_center'] = self.convert_lon_lat_to_meters_grid(grid['x_center']).astype(np.float64)

        else:
            grid['x'] = np.stack((nc.read_a_variable('x'), nc.read_a_variable('y'))).astype(np.float64)

            grid['x_center'] = np.stack((nc.read_a_variable('xc'), nc.read_a_variable('yc')), axis=1).astype(np.float64)

        return grid

    def read_triangles(self, nc, grid):
        grid['triangles'] = nc.read_a_variable(self.params['grid_variable_map']['triangles']).T - 1 # convert to zero base index
        grid['quad_cells_to_split'] = np.full((grid['triangles'] .shape[0],),False,dtype=bool)
        return grid


    def read_zlevel_as_float32(self, nc, file_index, zlevel_buffer, buffer_index):
        # calcuate zlevel from depth fractions, tide and water depth
        # FVCOM has fraction of depth < from free surface, with top value first in z dim of arrAy
        # todo check first value is the bottom or free surface+-, look like free surface??
        grid = self.grid
        fields = self.shared_info.classes['fields']

        # time varying zlevel from fixed water depth fractions and total water depth at nodes
        water_depth = fields['water_depth'].data[:, :, :, 0]
        tide = fields['tide'].data[:, :, :, 0]

        zlevel_buffer[buffer_index, ...] = grid['z_fractions'][np.newaxis, ...]*(tide[buffer_index, :, :]+water_depth) - water_depth

    def read_dry_cell_data(self, nc, file_index,is_dry_cell_buffer,buffer_index):
        si = self.shared_info
        if nc.is_var('wet_cells'):
            wet_cells= nc.read_a_variable('wet_cells',sel=file_index)
            is_dry_cell_buffer[buffer_index,:] = wet_cells != 1
        else:
            # get dry cells from water depth and tide
            grid = self.grid
            fields = si.classes['fields']
            reader_util.set_dry_cell_flag_from_tide(grid['triangles'],fields['tide'].data, fields['water_depth'].data,
                                                    si.minimum_total_water_depth, is_dry_cell_buffer,buffer_index )

    def read_time_sec_since_1970(self, nc, file_index=None):
        # read time as seconds
        time_str = nc.read_a_variable('Times', sel=file_index)

        # get times from netcdf encoded  strings
        time_sec=[]
        for s in time_str:
            time_sec.append(time_util.isostr_to_seconds(s.tostring()))

        time_sec = np.asarray(time_sec, dtype= np.float64)

        if self.params['time_zone'] is not None: time_sec += self.params['time_zone'] * 3600.

        return time_sec

    def read_file_var_as_4D_nodal_values(self,nc,var_name, file_index=None):
        # read variable into 4D ( time, node, depth, comp) format
        # assumes same variable order in the file
        dm = self.params['dimension_map']
        grid = self.grid

        data = nc.read_a_variable(var_name, sel=file_index)

        # first reorder dim to ( time, node, depth, comp), ie swap z and hori
        if nc.is_var_dim(var_name,dm['z']) or nc.is_var_dim(var_name,dm['z_mid_layer']):
            dim_order = [0, 2, 1] if nc.is_var_dim(var_name, dm['time']) else [2, 1]  # only 2 dims if time varying
            data = np.transpose(data, dim_order)

        # add time dim if needed
        if not nc.is_var_dim(var_name, dm['time']):
            data  = data[np.newaxis, ...]

            # some variables at nodes, some at cell center ( eg u,v,w)
        if nc.is_var_dim(var_name, dm['triangle']):
            # data is at cell center/element  move to nodes
            data = hydromodel_grid_transforms.get_node_layer_field_values(
                data, grid['node_to_tri_map'], grid['tri_per_node'], grid['cell_center_weights'])

        # see if z or z water level  in variable and swap z and node dim
        if nc.is_var_dim(var_name,dm['z_mid_layer']) :
            #3D mid layer values
            # convert mid-layer values to values at layer boundaries, ie zlevels
            data = hydromodel_grid_transforms.convert_layer_field_to_levels_from_depth_fractions_at_each_node(
                                data, grid['z_fractions_layer_center'], grid['z_fractions'])
        elif not nc.is_var_dim(var_name,dm['z']) :
            # 2D
            data =    data = data[..., np.newaxis]

        # add dummy vector component to make 4D
        data = data[:, :, :, np.newaxis]


        return data



    def preprocess_field_variable(self, nc,name, data):
        if name =='water_velocity' and data.shape[2] > 1: # process if 3D velocity
            # linear extrapolation of 3D velocity to bottom zlevel, may not give zero vel at bottom so set to zero
            data[:, :, 0, :] = 0.
        return data

