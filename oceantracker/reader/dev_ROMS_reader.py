

# Sample data subset
# https://www.seanoe.org/data/00751/86286/
#better?
#https://tds.marine.rutgers.edu/thredds/ncss/roms/doppio/DopAnV2R3-ini2007_da/his?var=h&var=mask_psi&var=mask_rho&var=mask_u&var=mask_v&var=ubar&var=vbar&var=zeta&var=temp&var=u&var=v&var=w&north=35.25&west=-77&east=-76&south=34.3&horizStride=1&time_start=2021-08-01T01%3A00%3A00Z&time_end=2021-08-02T00%3A00%3A00Z&timeStride=1&vertCoord=&accept=netcdf

from oceantracker.reader.generic_unstructured_reader import GenericUnstructuredReader
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util
import numpy as np
from datetime import datetime
from numba import njit
from oceantracker.util.cord_transforms import WGS84_to_UTM
from matplotlib import pyplot as plt, tri

from oceantracker.reader.util import reader_util


class ROMS(GenericUnstructuredReader):
    # reads  ROMS file, and tranforms all data to PSI grid
    # then splits all triangles in two to  use in oceantracker as a triangular grid,
    # so works with curvilinear ROMS grids
     # note: # ROMS is Fortan code so np.flatten() in F order

    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({ 'field_variables': {'water_velocity': PLC(['u','v','w'], [str], fixed_len=2),
                                  'water_depth': PVC('h', str),
                                  'tide': PVC('zeta', str)}
                                })
        # don't use name mappings for these variables
        self.clear_default_params(['dimension_map','grid_variables','one_based_indices'])

    def is_var_in_file_3D(self, nc, var_name_in_file): return any(x in  nc.get_var_dims(var_name_in_file) for x in ['s_w','s_rho'])

    def get_number_of_z_levels(self,nc): return nc.get_dim_size('s_w')

    def get_num_vector_components_in_file_variable(self,nc,file_var_name): return 1 # no vector vararibles

    def is_file_variable_time_varying(self, nc, var_name_in_file): return  'ocean_time' in nc.get_var_dims(var_name_in_file)

    def make_non_time_varying_grid(self,nc, grid):
        # pre-read useful info
        grid['psi_ocean_mask'] = nc.read_a_variable('mask_psi') == 1

        grid = super().make_non_time_varying_grid(nc, grid)
        # show this be a method only
        # add time invariant vertical grid variables needed for transformations

        grid['vertical_grid_type'] = 'sigma'
        return grid

    def read_nodal_x_float32(self, nc):
        grid = self.grid
        # record useful grid info
        grid['lat_psi'] = nc.read_a_variable('lat_psi').astype(np.float32)
        grid['lon_psi'] = nc.read_a_variable('lon_psi').astype(np.float32)
        grid['lon_lat'] =  np.stack((grid['lon_psi'].flatten('F'),grid['lat_psi'].flatten('F')),  axis=1)
        return WGS84_to_UTM(grid['lon_lat'])

    def read_triangles_as_int32(self, nc):
        grid = self.grid

        # get nodes for each corner of quad
        rows = np.arange(grid['psi_ocean_mask'].shape[0])
        cols = np.arange(grid['psi_ocean_mask'].shape[1])
        grid['psi_grid_node_numbers'] = rows.reshape((-1, 1)) + grid['psi_ocean_mask'].shape[0]*cols.reshape((1,-1))

        n1 = grid['psi_grid_node_numbers'][:-1,:-1]
        n2 = grid['psi_grid_node_numbers'][:-1, 1:]
        n3 = grid['psi_grid_node_numbers'][1: ,:-1]
        n4 = grid['psi_grid_node_numbers'][1: , 1:]

        # build triangles in anti-clockwise order
        tri1 = np.stack((n1.flatten('F'), n2.flatten('F'), n4.flatten('F'))).T
        tri2 = np.stack((n3.flatten('F'), n4.flatten('F'), n1.flatten('F'))).T
        tri = np.full((2*tri1.shape[0],3),0,dtype=np.int32)
        tri[:-1:2,:] = tri1 #put adjacent triangles together in memory, to speeds acces of nodal values??
        tri[1::2 ,:] = tri2

        # keep only ocean triangles, those with at least one ocean node
        sel= np.any(grid['psi_ocean_mask'].flatten('F')[tri],axis=1)
        tri = tri[sel,:]
        quad_cells_to_split = np.full((tri.shape[0],), False, dtype=bool) # none to slip as done manually
        return tri, quad_cells_to_split

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
        # get dry cells from water depth and tide
        si = self.shared_info
        grid = self.grid
        fields = self.shared_info.classes['fields']

        reader_util.set_dry_cell_flag_from_tide(grid['triangles'],fields['tide'].data, fields['water_depth'].data,
                                                si.minimum_total_water_depth, is_dry_cell_buffer,buffer_index )

    def read_time(self, nc, file_index=None):

        if file_index is None:
            time = nc.read_a_variable('ocean_time', sel=None)
        else:
            time = nc.read_a_variable('ocean_time', sel=file_index)
        base_date = nc.get_var_attr('ocean_time','units').split('since ')[-1]
        t0 = time_util.iso8601str_to_seconds(base_date)

        time += t0
        # get times from netcdf encoded  strings
        if self.params['time_zone'] is not None: time += self.params['time_zone'] * 3600.

        return time

    def read_file_field_variable_as4D(self, nc, file_var_info, is_time_varying, file_index=None):
        # reformat file variable into 4D time,node,depth, components  form
        var_name = file_var_info['name_in_file']
        data_dims= nc.get_var_dims(var_name)
        data = nc.read_a_variable(var_name, sel=file_index if is_time_varying else None).astype(np.float32)  # allow for time independent data

        # add dummy time dim if none
        if not self.is_file_variable_time_varying(nc, var_name): data = data[np.newaxis,...]

        if self.is_var_in_file_3D(nc, var_name):
            # move depth to last dim
            data = np.transpose(data,[0,2,3,1])
        else:
            # add dummy z dim
            data = data[..., np.newaxis]

        # data is now shaped as (time, row, col, depth)
        # convert to psi grid
        if 'eta_rho' in data_dims:
            a=1

        # now reshape in 4D
        if not self.is_file_variable_time_varying(nc, var_name): data = data[np.newaxis, ...]
        if not self.is_var_in_file_3D(nc, var_name):    data = data[:, :, np.newaxis, ...]
        if file_var_info['num_components'] == 1:             data = data[:, :, :, np.newaxis]

        return data



    def preprocess_field_variable(self, nc,name, data):

        if name =='water_velocity' and data.shape[2] > 1:
            # linear extrapolation of 3D velocity to bottom zlevel, may not give zero vel at bottom so set to zero
            data[:, :, 0, :]= 0.

        return data

    def dev_show_grid(self):
        # plots to help with development
        grid = self.grid

        fig1, ax1 = plt.subplots()
        ax1.scatter(grid['x'][:,0],grid['x'][:,1],c='k', marker='.', s=4)
        ax1.triplot(grid['x'][:,0],grid['x'][:,1],grid['triangles'])


        fig2, ax2 = plt.subplots()
        ax2.scatter(grid['lon_psi'] , grid['lat_psi'] , c='k', marker='.', s=4)
        sel= grid['psi_ocean_mask']
        ax2.scatter(grid['lon_psi'][sel],grid['lat_psi'][sel] ,  c='g', marker='.', s=4)
        plt.show()



