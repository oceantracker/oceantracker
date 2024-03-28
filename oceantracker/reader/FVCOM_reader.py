from oceantracker.reader._base_reader import _BaseReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util
from oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from datetime import datetime
from oceantracker.reader.util import hydromodel_grid_transforms

from oceantracker.reader.util import reader_util
from oceantracker.shared_info import SharedInfo as si

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
        self.add_default_params({ 'field_variable_map': {
                                                'water_velocity': PLC(['u','v','ww'], [str], fixed_len=2),
                                                'water_depth': PVC('h', str,doc_str='maps standard internal field name to file variable name'),
                                                'tide': PVC('zeta', str,doc_str='maps standard internal field name to file variable name'),
                                                'water_temperature': PVC('temp', str, doc_str='maps standard internal field name to file variable name'),
                                                 'salinity': PVC('salinity', str, doc_str='maps standard internal field name to file variable name'),
                                                 'wind_velocity': PLC(['uwind_speed', 'vwind_speed'], [str], doc_str='maps standard internal field name to file variable name'),
                                            'bottom_stress': PVC('not_known', str, doc_str='maps standard internal field name to file variable name'),
                                            'A_Z_profile': PVC('not_known', str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                }
        })


    def is_file_format(self, file_name):
        nc = NetCDFhandler(file_name,'r')
        is_file_type= set(['Times', 'nv', 'u', 'v', 'h']).issubset(list(nc.variable_info.keys()))
        nc.close()
        return is_file_type

    def build_vertical_grid(self, nc, grid):

        # time invarient z fractions at layer needed for super.build_vertical_grid
        grid['zlevel_fractions']  = 1. + np.flip(nc.read_a_variable('siglev', sel=None).astype(np.float32).T, axis=1)  # layer boundary fractions
        grid['zlevel_fractions_layer'] = 1. + np.flip(nc.read_a_variable('siglay', sel=None).astype(np.float32).T, axis=1)  # layer center fractions

        # make distance weighting matrix for triangle center values at nodal points
        grid['cell_center_weights'] = hydromodel_grid_transforms.calculate_inv_dist_weights_at_node_locations(
            grid['x'], grid['x_center'], grid['node_to_tri_map'], grid['tri_per_node'])
        grid['vertical_grid_type'] = 'S-sigma'

        # now do setup
        grid = super().build_vertical_grid(nc,grid)


        return grid



    def set_up_uniform_sigma(self, nc, grid):

        # add time invariant vertical grid variables needed for transformations
        # sigma level fractions required to build zlevel after reading  tide
        # siglay, siglev are <0 and  look like layer fraction from free surface starting at top moving down, convert to fraction from bottom starting at bottom

        # first values in z axis is the top? so flip

        # get node with thineest bottom layer in non-uniform sigma layers
        node_min = hydromodel_grid_transforms.find_node_with_smallest_top_layer(grid['zlevel_fractions'], grid['bottom_cell_index'])

        # stretch sigma out to same number of depth cells,
        # needed for LSC grid if node_min profile is not full number of cells

        grid['sigma'] = grid['zlevel_fractions'][node_min, :]
        return grid

    def read_horizontal_grid_coords(self, nc, grid):
        # get node location in meters
        # also record cell center x as well to be used for get nodal field vals from values at center, eg velocity
        grid['x'] = np.stack((nc.read_a_variable('x'), nc.read_a_variable('y'))).astype(np.float64)
        grid['x_center'] = np.stack((nc.read_a_variable('xc'), nc.read_a_variable('yc')), axis=1).astype(np.float64)

        if  np.all(nc.read_a_variable('x')==0): #  use lat long? as x may sometimes be all be zeros
            grid['hydro_model_cords_in_lat_long'] = True
            grid['x'] =   np.stack((nc.read_a_variable('lon'), nc.read_a_variable('lat')), axis=1).astype(np.float64)
            grid['x_center'] = np.stack((nc.read_a_variable('lonc'), nc.read_a_variable('latc')), axis=1).astype(np.float64)

        elif self.detect_lonlat_grid(grid['x']):
            # try auto detection
            grid['hydro_model_cords_in_lat_long'] = True

        else:
            grid['hydro_model_cords_in_lat_long'] = self.params['hydro_model_cords_in_lat_long']

        if grid['hydro_model_cords_in_lat_long']:
            grid['lon_lat'] = grid['x']
            grid['x'] = self.convert_lon_lat_to_meters_grid(grid['x'])
            grid['lon_lat_center'] = grid['x_center']
            grid['x_center'] = self.convert_lon_lat_to_meters_grid(grid['x_center'])

        return grid

    def read_triangles_as_int32(self, nc, grid):
        grid['triangles'] = nc.read_a_variable('nv').T.astype(np.int32) - 1 # convert to zero base index
        grid['quad_cells_to_split'] =  np.full((0,),0, np.int32)
        return  grid


    def is_hindcast3D(self, nc):
        return nc.is_var_dim('u','siglay')

    def number_hindcast_zlayers(self, nc):
        return nc.dim_size('siglev')

    def read_zlevel_as_float32(self, nc,grid,fields, file_index, zlevel_buffer, buffer_index):
        # calcuate zlevel from depth fractions, tide and water depth
        # FVCOM has fraction of depth < from free surface, with top value first in z dim of arrAy
        # todo check first value is the bottom or free surface+-, look like free surface??


        # time varying zlevel from fixed water depth fractions and total water depth at nodes
        water_depth = fields['water_depth'].data[:, :, :, 0]
        tide = fields['tide'].data[:, :, :, 0]

        zlevel_buffer[buffer_index, ...] = grid['zlevel_fractions'][np.newaxis, ...]*(tide[buffer_index, :, :]+water_depth) - water_depth

    def read_dry_cell_data(self, nc,grid, fields,  file_index, is_dry_cell_buffer,buffer_index):

        if nc.is_var('wet_cells'):
            wet_cells= nc.read_a_variable('wet_cells',sel=file_index)
            is_dry_cell_buffer[buffer_index,:] = wet_cells != 1
        else:
            # get dry cells from water depth and tide
            reader_util.set_dry_cell_flag_from_tide(grid['triangles'],fields['tide'].data, fields['water_depth'].data,
                                                    si.settings.minimum_total_water_depth, is_dry_cell_buffer,buffer_index )

    def read_time_sec_since_1970(self, nc, file_index=None):
        # read time as seconds
        time_str = nc.read_a_variable('Times', sel=file_index)

        # get times from netcdf encoded  strings
        time_sec=[]
        for s in time_str:
            time_sec.append(time_util.isostr_to_seconds(s.tostring()))

        time_sec = np.asarray(time_sec, dtype= np.float64)

        return time_sec


    def get_field_params(self,nc, name, crumbs=''):
        # work out if feild is 3D ,etc
        fmap = self.params['field_variable_map'][name]
        if type(fmap) != list: fmap =[fmap]
        f_params = dict(time_varying = nc.is_var_dim(fmap[0], 'time'),
                        is3D = nc.is_var_dim(fmap[0],'siglay') or nc.is_var_dim(fmap[0],'siglev'),
                        is_vector = len(fmap) > 1,
                        )
        return f_params

    def read_file_var_as_4D_nodal_values(self,nc,grid, var_name, file_index=None):
        # read variable into 4D ( time, node, depth, comp) format
        # assumes same variable order in the file

        data = nc.read_a_variable(var_name, sel=file_index)

        # first reorder dim to ( time, node, depth, comp), ie swap z and hori
        if nc.is_var_dim(var_name,'siglay') or nc.is_var_dim(var_name,'siglev'):
            dim_order = [0, 2, 1] if nc.is_var_dim(var_name, 'time') else [2, 1]  # only 2 dims if time varying
            data = np.transpose(data, dim_order)

        # add time dim if needed
        if not nc.is_var_dim(var_name, 'time'):
            data  = data[np.newaxis, ...]

        # some variables at nodes, some at cell center ( eg u,v,w)
        if nc.is_var_dim(var_name, 'nele'):
            # data is at cell center/element/triangle  move to nodes
            data = hydromodel_grid_transforms.get_nodal_values_from_weighted_data(data, grid['node_to_tri_map'], grid['tri_per_node'], grid['cell_center_weights'])

        # see if z or z water level  in variable and swap z and node dim
        if nc.is_var_dim(var_name,'siglay') :
            #3D mid layer values
            # convert mid-layer values to values at layer boundaries, ie zlevels
            data = hydromodel_grid_transforms.convert_layer_field_to_levels_from_depth_fractions_at_each_node(
                                data, grid['zlevel_fractions_layer'], grid['zlevel_fractions'])
        elif not nc.is_var_dim(var_name, 'siglev') :
            # 2D field
            data =    data = data[..., np.newaxis]

        # add dummy vector component to make 4D
        data = data[:, :, :, np.newaxis]


        return data

    def preprocess_field_variable(self, nc,name,grid, data):
        if name =='water_velocity' and data.shape[2] > 1: # process if 3D velocity
            # linear extrapolation of 3D velocity to bottom zlevel, may not give zero vel at bottom so set to zero
            data[:, :, 0, :] = 0.
        return data

