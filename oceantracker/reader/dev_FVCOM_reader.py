from oceantracker.reader.generic_unstructured_reader import GenericUnstructuredReader
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util

import numpy as np
from datetime import datetime
from oceantracker.reader.util import data_grid_transforms

from oceantracker.reader.util import reader_util

#todo add required variables and dimensions lists to sensure
#todo friction velocity from bottom stress magnitude, tauc if present
#todo use A_H and A_V fields in random walk
#todo implement depth average mode using depth average variables in the file

class unstructured_FVCOM(GenericUnstructuredReader):
    # loads a standard SCHISM netcdf output file with nodal data
    # variable names can be tweaked via maps in shared_params, if non-standard names used

    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({ 'field_variables': {'water_velocity': PLC(['u','v'], [str], fixed_len=2),
                                  'water_depth': PVC('h', str),
                                  'tide': PVC('zeta', str)},
                                  'required_file_variables': PLC(['Times','nv', 'u', 'v', 'h'], [str]),
                                  'required_file_dimensions': PLC(['siglay', 'siglev'], [str]),
                                })
        # don't use name mappings for these variables
        self.clear_default_params(['dimension_map','grid_variables','one_based_indices'])

    def additional_setup_and_hindcast_file_checks(self, nc, msg_logger):
        # include vertical velocity if in file
        if nc.is_var('ww'):
            self.params['field_variables']['water_velocity'].append('ww')
        else:
            msg_logger.msg('No vertical velocity "ww" variable in FVCOM hydro-model files, assuming vertical_velocity=0', note=True)

    def is_var_in_file_3D(self, nc, var_name_in_file): return any(x in  nc.get_var_dims(var_name_in_file) for x in ['siglay','siglev'])

    def get_number_of_z_levels(self,nc):  return nc.get_dim_size('siglev')

    def get_num_vector_components_in_file_variable(self,nc,file_var_name): return 1 # no vector vararibles

    def is_file_variable_time_varying(self, nc, var_name_in_file): return  'time' in nc.get_var_dims(var_name_in_file)

    def make_non_time_varying_grid(self,nc, grid):
        grid = super().make_non_time_varying_grid(nc, grid)
        # add time invariant vertical grid variables needed for transformations
        # sigma level fractions required to build zlevel after reading  tide
        # siglay, siglev are <0 and  look like layer fraction from free surface starting at top moving down, convert to fraction from bottom starting at bottom

        # first values in z axis is the top? so flip
        grid['z_fractions_layer_center'] =  1.+np.flip(nc.read_a_variable('siglay', sel=None).astype(np.float32).T,axis=1)  # layer center fractions
        grid['z_fractions_layer_boundaries'] = 1.+np.flip(nc.read_a_variable('siglev', sel=None).astype(np.float32).T,axis=1)  # layer boundary fractions
        grid['vertical_grid_type'] = 'S-sigma'


        # make distance weighting matrix for triangle center values at nodal points
        grid['cell_center_weights'] = data_grid_transforms.calculate_cell_center_weights_at_node_locations(
                                                    grid['x'], grid['x_center'],grid['node_to_tri_map'],grid['tri_per_node'])
        return grid

    def read_nodal_x_as_float64(self, nc):
        # get node location in meters
        # also record cell center x as well to be used for get nodal field vals from values at center, eg velocity
        grid= self.grid

        if  self.params['cords_in_lat_long'] or np.all(nc.read_a_variable('x')==0): #  use lat long? as x may sometimes be all be zeros

            grid['lat']= nc.read_a_variable('lat')
            grid['lon']=nc.read_a_variable('lon')
            x = np.stack((grid['lon'],grid['lat'] ), axis=1).astype(np.float64)
            x= self.convert_lon_lat_to_meters_grid(x)

            grid['x_center'] = np.stack((nc.read_a_variable('lonc'), nc.read_a_variable('latc')), axis=1)
            grid['x_center'] = self.convert_lon_lat_to_meters_grid(grid['x_center']).astype(np.float64)

        else:
            x = np.stack((nc.read_a_variable('x'), nc.read_a_variable('y'))).astype(np.float64)

            grid['x_center'] = np.stack((nc.read_a_variable('xc'), nc.read_a_variable('yc')), axis=1).astype(np.float64)

        return x

    def read_triangles_as_int32(self, nc):
        data = nc.read_a_variable('nv').T - 1 # convert to zero base index
        quad_cells_to_split = np.full((data.shape[0],),False,dtype=bool)
        return data[:,:3].astype(np.int32), quad_cells_to_split

    def is_hindcast3D(self, nc):  return nc.is_var('u') # are always 3D

    def read_zlevel_as_float32(self, nc, file_index, zlevel_buffer, buffer_index):
        # calcuate zlevel from depth fractions, tide and water depth
        # FVCOM has fraction of depth < from free surface, with top value first in z dim of arrAy
        # todo check first value is the bottom or free surface+-, look like free surface??
        grid = self.grid
        fields = self.shared_info.classes['fields']

        # time varying zlevel from fixed water depth fractions and total water depth at nodes
        water_depth = fields['water_depth'].data[:, :, :, 0]
        tide = fields['tide'].data[:, :, :, 0]

        zlevel_buffer[buffer_index, ...] = grid['z_fractions_layer_boundaries'][np.newaxis, ...]*(tide[buffer_index, :, :]+water_depth) - water_depth

    def read_dry_cell_data(self, nc, file_index,is_dry_cell_buffer,buffer_index):
        si = self.shared_info
        if nc.is_var('wet_cells'):
            wet_cells= nc.read_a_variable('wet_cells',sel=file_index)
            is_dry_cell_buffer[buffer_index,:] = wet_cells != 1
        else:
            # get dry cells from water depth and tide
            grid = self.grid
            fields = self.shared_info.classes['fields']
            reader_util.set_dry_cell_flag_from_tide(grid['triangles'],fields['tide'].data, fields['water_depth'].data,
                                                    si.minimum_total_water_depth, is_dry_cell_buffer,buffer_index )

    def read_time(self, nc, file_index=None):

        if file_index is None:
            time_str = nc.read_a_variable('Times', sel=None)
        else:
            time_str = nc.read_a_variable('Times', sel=file_index)

        # get times from netcdf encoded  strings
        time=[]
        for s in time_str:
            time.append(time_util.iso8601str_to_seconds(s.tostring()))

        time = np.asarray(time, dtype= np.float64)

        if self.params['time_zone'] is not None: time += self.params['time_zone'] * 3600.

        return time

    def read_file_field_variable_as4D(self, nc, file_var_info,is_time_varying, file_index=None):
        # reformat file variable into 4D time,node,depth, components  form
        grid = self.grid

        var_name= file_var_info['name_in_file']

        data = nc.read_a_variable(var_name, sel= file_index if is_time_varying else None) # allow for time independent data

        # add a time dim if not present
        if not self.is_file_variable_time_varying(nc,var_name): data = data[np.newaxis,...]

        if data.ndim == 3:
            # reorder node and depth dimension to fit oceantracker convention
            data = data.transpose((0,2,1))
        elif data.ndim == 2:
            # other wise add dummy depth dim if not present
            data = data[: ,: , np.newaxis]

        # data vertical profile starts at top/free surface, flip to start at bottom to fit ocean tracker convention
        data = np.flip(data, axis=2)

        # some variables at nodes, some at cell center ( eg u,v,w)
        if 'nele' in nc.get_var_dims(var_name) :
            # data is at cell center/element  move to nodes
            data = data_grid_transforms.get_node_layer_field_values(
                            data,grid['node_to_tri_map'],grid['tri_per_node'], grid['cell_center_weights'])

        if  'siglay' in nc.get_var_dims(var_name):
            # convert mid-layer values to values at layer boundaries, ie zlevels
            data =  data_grid_transforms.convert_layer_field_to_levels_from_depth_fractions_at_each_node(
                        data,grid['z_fractions_layer_center'],grid['z_fractions_layer_boundaries'])

        # add dummy vector component to make 4D
        data = data[:, :, :, np.newaxis]

        return data.astype(np.float32)

    def preprocess_field_variable(self, nc,name, data):
        if name =='water_velocity' and data.shape[2] > 1: # process if 3D velocity
            # linear extrapolation of 3D velocity to bottom zlevel, may not give zero vel at bottom so set to zero
            data[:, :, 0, :] = 0.
        return data

