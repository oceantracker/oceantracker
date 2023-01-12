from oceantracker.reader.generic_unstructured_reader import GenericUnstructuredReader
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util

import numpy as np
from datetime import datetime
from numba import njit
from oceantracker.interpolator.util.interp_kernals import kernal_linear_interp1D

from oceantracker.reader.util import reader_util

#todo distance weight cell center to nodal values with pre-cacluated matrix
#todo friction velocity from bottom stress magnitude, tauc if present
#todo use A_H and A_V fields in random walk

class unstructured_FVCOM(GenericUnstructuredReader):
    # loads a standard SCHISM netcdf output file with nodal data
    # variable names can be tweaked via maps in shared_params, if non-standard names used

    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({ 'field_variables': {'water_velocity': PLC(['u','v','ww'], [str], fixed_len=2),
                                  'water_depth': PVC('h', str),
                                  'tide': PVC('zeta', str)}
                                })
        # don't use name mappings for these variables
        self.clear_default_params(['dimension_map','grid_variables','one_based_indices'])

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
        return grid

    def read_nodal_x_float64(self, nc):
        # get node location in meters
        # also record cell center x as well to be used for get nodal field vals from values at center, eg velocity
        grid= self.grid

        if  self.params['cords_in_lat_long'] or np.all(nc.read_a_variable('x')==0): #  use lat long? as x may sometimes be all be zeros
            x = np.stack((nc.read_a_variable('lon'), nc.read_a_variable('lat')), axis=1).astype(np.float64)
            x= self.convert_lat_long_to_meters_grid(x)

            grid['x_center'] = np.stack((nc.read_a_variable('lonc'), nc.read_a_variable('latc')), axis=1)
            grid['x_center'] = self.convert_lat_long_to_meters_grid(grid['x_center'] ).astype(np.float64)

        else:
            x = np.stack((nc.read_a_variable('x'), nc.read_a_variable('y'))).astype(np.float64)

            grid['x_center'] = np.stack((nc.read_a_variable('xc'), nc.read_a_variable('yc')), axis=1).astype(np.float64)

        return x

    def read_triangles_as_int32(self, nc):
        data = nc.read_a_variable('nv').T - 1
        quad_cells_to_split = np.full((data.shape[0],),False,dtype=bool)
        return data[:,:3].astype(np.int32), quad_cells_to_split

    def is_hindcast3D(self, nc):  return nc.is_var('u') # are always 3D

    def read_zlevel_as_float32(self, nc, file_index, zlevel_buffer, buffer_index):
        # calcuate zlevel from depth fractions, tide and water depth
        # FVCOM has fraction of depth < from free surface, with top value first in z dim of arrAy
        # todo check first value is the bottom or free surface+-??
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
            is_dry_cell_buffer[buffer_index,:]  = wet_cells != 1

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

        # reorder node and depth dimension to fit oceantracker convention
        if data.ndim == 3: data = data.transpose((0,2,1))

        # add dummy depth dim if not present
        if data.ndim == 2: data = data.reshape(data.shape + (1,))

        # data vertical profile starts at top/free surface, flip to start at bottom to fit ocean tracker convention
        data = np.flip(data, axis=2)

        # some variables at nodes, some at cell center ( eg u,v,w)
        if 'nele' in nc.get_var_dims(var_name) :
            # data is at cell/element and layers, move to nodes and layer boundaries
            data = get_node_layer_field_values(data,grid['node_to_tri_map'],grid['tri_per_node'])

        if  'siglay' in nc.get_var_dims(var_name):
            # convert layer values to values at layer boundaries, ie zlevels
            data = convert_layer_field_to_levels(data,grid['z_fractions_layer_center'],grid['z_fractions_layer_boundaries'])


        # add dummy component to make 4D
        data = data[:, :,:, np.newaxis]

        return data.astype(np.float32)

    def preprocess_field_variable(self, nc,name, data):

        if name =='water_velocity' and data.shape[2] > 1: # process if 3D velocity
            # linear extrapolation of 3D velocity to bottom zlevel, may not give zero vel at bottom so set to zero
            data[:, :, 0, :] = 0.

        return data

@njit
def get_node_layer_field_values(data, node_to_tri_map, tri_per_node):
    # todo very rough cell to node converted averages values in cells center to layer boundary below,
    #  make better interpolator, eg with pre-calculated distance weighted?!!!

    data_nodes= np.full( (data.shape[0],) + (len(node_to_tri_map),) +(data.shape[2],) , 0., dtype=np.float32)

    for nt in range(data.shape[0]): # loop over time steps
        # loop over triangles
        for node in range(node_to_tri_map.shape[0]):
            for nz in range(data.shape[2]):
                # loop over cells containing this node
                for cell in node_to_tri_map[node,:tri_per_node[node]]:
                    data_nodes[nt, node, nz] += data[nt, cell, nz]
                data_nodes[nt, node, nz] =  data_nodes[nt, node, nz]/len(node_to_tri_map[node])
    return data_nodes

@njit
def convert_layer_field_to_levels(data, zf_center, zf_boundaries):

    data_levels = np.full((data.shape[0],) + (data.shape[1],) + (zf_boundaries.shape[1],), 0., dtype=np.float32)

    for nt in range(data.shape[0]):
        for n in range(data.shape[1]):
            for nz in range(1,data.shape[2]):
                # linear interp levels not, first or last boundary
                data_levels[nt, n, nz] = kernal_linear_interp1D(zf_center[n, nz - 1], data[nt,n, nz - 1], zf_center[n, nz], data[nt, n, nz],zf_boundaries[n,nz])

            # extrapolate to top zlevel
            data_levels[nt, n, -1] = kernal_linear_interp1D(zf_center[n,- 2], data[nt, n, -2], zf_center[n, -1],data[nt, n, -1], zf_boundaries[n,-1])

            # extrapolate to bottom zlevel
            data_levels[nt, n, 0] = kernal_linear_interp1D(zf_center[n, 0], data[nt, n, 0], zf_center[n, 1],  data[nt, n, 1], zf_boundaries[n,0])

    return data_levels