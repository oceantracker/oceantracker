

# Sample data subset
# https://www.seanoe.org/data/00751/86286/
#better?
#https://tds.marine.rutgers.edu/thredds/ncss/roms/doppio/DopAnV2R3-ini2007_da/his?var=h&var=mask_psi&var=mask_rho&var=mask_u&var=mask_v&var=ubar&var=vbar&var=zeta&var=temp&var=u&var=v&var=w&north=35.25&west=-77&east=-76&south=34.3&horizStride=1&time_start=2021-08-01T01%3A00%3A00Z&time_end=2021-08-02T00%3A00%3A00Z&timeStride=1&vertCoord=&accept=netcdf

# full grid 12 houly on month
# https://tds.marine.rutgers.edu/thredds/ncss/roms/doppio/DopAnV2R3-ini2007_da/his?var=f&var=h&var=mask_psi&var=mask_rho&var=mask_u&var=mask_v&var=ubar&var=vbar&var=zeta&var=temp&var=u&var=v&var=w&disableLLSubset=on&disableProjSubset=on&horizStride=1&time_start=2007-01-02T01%3A00%3A00Z&time_end=2007-01-31T00%3A00%3A00Z&timeStride=12&vertCoord=&accept=netcdf
from oceantracker.reader.generic_unstructured_reader import GenericUnstructuredReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util
import numpy as np
from datetime import datetime
from numba import njit
from oceantracker.util.cord_transforms import WGS84_to_UTM
from matplotlib import pyplot as plt, tri
from oceantracker.reader.util.reader_util import append_split_cell_data
from oceantracker.util.triangle_utilities_code import split_quad_cells


from oceantracker.util.basic_util import  is_substring_in_list

from oceantracker.reader.util import reader_util
from oceantracker.reader.util.data_grid_transforms import convert_layer_field_to_levels_from_fixed_depth_fractions

# todo use ROMs turbulent viscosity for dispersion
#todo use  openbondary data to improve identifcation of open boundary nodes?
#todo implement depth average mode using depth average variables in the file
#todo friction velocity from bottom stress ???

class ROMsNativeReader(GenericUnstructuredReader):
    # reads  ROMS file, and tranforms all data to PSI grid
    # then splits all triangles in two to  use in oceantracker as a triangular grid,
    # so works with curvilinear ROMS grids
     # note: # ROMS is Fortan code so np.flatten() in F order

    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({ 'field_variables': {'water_velocity': PLC(['u','v','w'], [str], fixed_len=2),
                                  'water_depth': PVC('h', str),
                                  'tide': PVC('zeta', str)},
                                  'required_file_variables': PLC(['ocean_time','mask_psi','lat_psi','lon_psi','h','zeta','u','v'], [str]),
                                  'required_file_dimensions': PLC(['s_w','s_rho','eta_u','eta_v'], [str]),
                                })
        # don't use name mappings for these variables
        self.clear_default_params(['dimension_map','grid_variables','one_based_indices'])

    def is_var_in_file_3D(self, nc, var_name_in_file): return any(x in  nc.get_var_dims(var_name_in_file) for x in ['s_w','s_rho'])

    def get_number_of_z_levels(self,nc): return nc.get_dim_size('s_w')

    def get_num_vector_components_in_file_variable(self,nc,file_var_name): return 1 # no vector vararibles

    def is_file_variable_time_varying(self, nc, var_name_in_file): return  'ocean_time' in nc.get_var_dims(var_name_in_file)

    def build_grid(self, nc, grid):
        # pre-read useful info
        grid['psi_land_mask'] = nc.read_a_variable('mask_psi') != 1
        grid['u_land_mask'] = nc.read_a_variable('mask_u') != 1
        grid['v_land_mask'] = nc.read_a_variable('mask_v') != 1
        grid['rho_land_mask'] = nc.read_a_variable('mask_rho') != 1


        grid = super().build_grid(nc, grid)

        grid['active_nodes'] = np.unique(grid['triangles']) # the nodes that are used in triangulation ( ie owithout land)

        # add time invariant vertical grid variables needed for transformations

        # first values in z axis is the top? so flip
        grid['z_fractions_layer_center'] = nc.read_a_variable('s_rho', sel=None).astype(np.float32)  # layer center fractions
        grid['z_fractions_layer_boundaries'] = nc.read_a_variable('s_w', sel=None).astype(np.float32)  # layer boundary fractions
        grid['vertical_grid_type'] = 'S-sigma'
        return grid

    def read_nodal_x_as_float64(self, nc):
        grid = self.grid
        # record useful grid info
        grid['lat_psi'] = nc.read_a_variable('lat_psi').astype(np.float64)
        grid['lon_psi'] = nc.read_a_variable('lon_psi').astype(np.float64)

        grid['lon_lat'] =  np.stack((grid['lon_psi'],grid['lat_psi']),  axis=2)
        s=   grid['lon_lat'].shape
        grid['lon_lat']=   grid['lon_lat'].reshape(s[0]*s[1],s[2])
        x = self.convert_lon_lat_to_meters_grid(grid['lon_lat'])
        return x

    def read_triangles_as_int32(self, nc):
        # build triangles from regular grid
        grid = self.grid

        # get nodes for each corner of quad
        rows = np.arange(grid['psi_land_mask'].shape[0])
        cols = np.arange(grid['psi_land_mask'].shape[1])

        # get global node numbers for flattened grid in C order, row 1 should be 0, 1, 3 ....
        # note rows are x, and cols y in ROMS which are Fortran ordered arrays
        grid['psi_grid_node_numbers'] = cols.size*rows.reshape((-1, 1)) + cols.reshape((1,-1))

        # get global node numbers of triangle nodes
        n1 = grid['psi_grid_node_numbers'][:-1, :-1]
        n2 = grid['psi_grid_node_numbers'][:-1, 1: ]
        n3 = grid['psi_grid_node_numbers'][1: , 1: ]
        n4 = grid['psi_grid_node_numbers'][1: , :-1]

        # build Quad cellls
        quad_cells =  np.stack((n1.flatten('C'), n2.flatten('C'), n3.flatten('C'), n4.flatten('C'))).T

        # keep  quad cells with less than 3 land nodes
        sel= np.sum(grid['psi_land_mask'].flatten('C')[quad_cells],axis=1) < 3
        quad_cells = quad_cells[sel,:]

        quad_cells_to_split = np.full((quad_cells.shape[0],), True, dtype=bool)
        tri = split_quad_cells(quad_cells, quad_cells_to_split)

        return tri.astype(np.int32), quad_cells_to_split.astype(np.int32)

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
        pass

    def read_dry_cell_data(self, nc, file_index,is_dry_cell_buffer,buffer_index):
        # get dry cells from water depth and tide
        si = self.shared_info
        grid = self.grid
        fields = self.shared_info.classes['fields']

        reader_util.set_dry_cell_flag_from_tide(grid['triangles'],fields['tide'].data, fields['water_depth'].data,
                                                si.minimum_total_water_depth, is_dry_cell_buffer,buffer_index )
        pass

    def read_time_sec_since_1970(self, nc, file_index=None):
        # get times relative to base date from netcdf encoded  strings
        if file_index is None:
            time_sec = nc.read_a_variable('ocean_time', sel=None)
        else:
            time_sec = nc.read_a_variable('ocean_time', sel=file_index)

        base_date = nc.get_var_attr('ocean_time','units').split('since ')[-1]
        t0 = time_util.isostr_to_seconds(base_date)

        time_sec += t0

        if self.params['time_zone'] is not None: time_sec += self.params['time_zone'] * 3600.

        return time_sec

    def read_file_field_variable_as4D(self, nc, file_var_info, is_time_varying, file_index=None):
        # reformat file variable into 4D time,node,depth, components  form
        grid = self.grid
        var_name = file_var_info['name_in_file']
        data_dims= nc.get_var_dims(var_name)
        data = nc.read_a_variable(var_name, sel=file_index if is_time_varying else None).astype(np.float32)  # allow for time independent data

        # add dummy time dim if none
        if not self.is_file_variable_time_varying(nc, var_name): data = data[np.newaxis,...]

        if self.is_var_in_file_3D(nc, var_name):
            # move depth to last dim
            # also depth dim [0] is deepest value, like schisim, ie cold water at bottom
            data = np.transpose(data,[0,2,3,1])
        else:
            # add dummy z dim
            data = data[..., np.newaxis]

        # data is now shaped as (time, row, col, depth)

        # convert data  to psi grid, from other variable grids if neded
        if 'eta_rho' in data_dims:
            data = rho_grid_to_psi(data, grid['rho_land_mask'])

        elif 'eta_u' in data_dims:
            # masked value 10^36 ,  so set to zero before finding mean value for psi grid
            data = u_grid_to_psi(data, grid['u_land_mask'])

        elif 'eta_v' in data_dims:
            data = v_grid_to_psi(data, grid['v_land_mask'])

        # now flatten (time,rows, col, depth)  to  (time,nodes, depth)
        s = data.shape

        # check if rows/cols now  consistent with Psi grid
        if not (grid['psi_land_mask'].shape == s[1:3]):
            #todo better error messaging !!!
            print('not all ROMS variables consisted and cannot map all to psi grid, may be in-correctly formed subset of full model domain , try with full model domain, files variable' + var_name)

        data = data.reshape( (s[0],s[1]*s[2], s[3])) # this should match flatten in "C" order

        grid = self.grid

        if 's_rho' in data_dims:
            # convert mid-layer values to values at layer boundaries, ie zlevels
            data = convert_layer_field_to_levels_from_fixed_depth_fractions(
                data, grid['z_fractions_layer_center'], grid['z_fractions_layer_boundaries'])

        # add dummy vector components axis, note in ROMS vectors are stored in netcdf as individual compoents,
        # so  file_var_info['num_components'] is always 1
        if file_var_info['num_components'] == 1:             data = data[:, :, :, np.newaxis]

        return data


    def preprocess_field_variable(self, nc,name, data):

        if name =='water_velocity':

            if data.shape[2] > 1:
                # linear extrapolation of 3D velocity to bottom zlevel, may not give zero vel at bottom so set to zero
                data[:, :, 0, :]= 0.

        return data

    def read_open_boundary_data_as_boolean(self, grid):
        # and make this part of the read grid method

        # read hgrid file for open boundary data
        is_open_boundary_node = np.full((grid['psi_land_mask'].shape), False)

        # flag all edges of regular as open boundaries
        # this will pick up most open boundary nodes, but not internal rivers
        is_open_boundary_node[:,[0,-1]] = True
        is_open_boundary_node[[0, -1],:] = True

        # only flag those  as open which are part of the ocean
        is_open_boundary_node = np.logical_and(is_open_boundary_node,~grid['psi_land_mask'])
        #todo write note open boundary data avaible, chose OBC mode param
        s = is_open_boundary_node.shape
        is_open_boundary_node = is_open_boundary_node.reshape((s[0]*s[1],))
        return is_open_boundary_node




    def _dev_show_grid(self):
        # plots to help with development
        grid = self.grid

        fig1, ax1 = plt.subplots()
        ax1.scatter(grid['x'][:,0],grid['x'][:,1],c='k', marker='.', s=4)
        ax1.triplot(grid['x'][:,0],grid['x'][:,1],grid['triangles'])


        fig2, ax2 = plt.subplots()
        ax2.scatter(grid['lon_psi'] , grid['lat_psi'] , c='k', marker='.', s=4)
        sel= grid['psi_land_mask']
        ax2.scatter(grid['lon_psi'][sel],grid['lat_psi'][sel] ,  c='g', marker='.', s=4)
        plt.show()

@njit()
def u_grid_to_psi(data, mask):
    # data ins (time, row, col, depth),  mask is land  nodes
    # to convert to pis grid make mean of adajacet rows, but  use land masked values as zero
    #  data = 0.5 * (data[:, :-1, :, :] + data[:, 1:, :, :])
    nTimes, nRows, nCols, nDepths = data.shape

    out = np.full((nTimes,nRows-1,nCols,nDepths), np.nan,dtype=data.dtype)

    for nt  in range(nTimes):
        for r in range(nRows-1):
            for c in range(nCols):
                for nd in range(nDepths):
                    v1 = 0. if mask[r   ,c] else data[nt,   r, c, nd]
                    v2 = 0. if mask[r+1, c] else data[nt, r+1, c, nd]
                    out[nt, r, c, nd] = 0.5*(v1 + v2)
    return out

@njit()
def v_grid_to_psi(data, mask):
    # data ins (time, row, col, depth),  mask is land  nodes
    # to convert to pis grid make mean of adajacet rows, but  use land masked values as zero
    #  data =  0.5 * (data[:, :, :-1, :] + data[:, :, 1::, :])
    nTimes, nRows, nCols, nDepths = data.shape

    out = np.full((nTimes,nRows,nCols-1,nDepths), np.nan,dtype=data.dtype)

    for nt  in range(nTimes):
        for r in range(nRows):
            for c in range(nCols-1):
                for nd in range(nDepths):
                    v1 = 0. if mask[r   ,c] else data[nt,   r, c, nd]
                    v2 = 0. if mask[r, c+1] else data[nt, r, c+1, nd]
                    out[nt, r, c, nd] = 0.5*(v1 + v2)
    return out

@njit()
def rho_grid_to_psi(data, mask):
    # data ins (time, row, col, depth),  mask is land  nodes
    # to convert to psi grid make mean of adajacet rows andcolumns, but  use land masked values as zero
    #       data = 0.5 * (data[:, :-1, :, :] + data[:, 1:, :, :])
    #       data = 0.5 * (data[:, :, :-1, :] + data[:, :, 1::, : ])

    nTimes, nRows, nCols, nDepths = data.shape

    out = np.full((nTimes,nRows-1, nCols-1, nDepths), np.nan,dtype=data.dtype)

    v = np.full((4,), np.nan)
    for nt  in range(nTimes):
        for r in range(nRows-1):
            for c in range(nCols-1):
                for nd in range(nDepths):
                    v[0] = np.nan if mask[r    , c     ] else data[nt, r    , c    , nd]
                    v[1] = np.nan if mask[r    , c  + 1] else data[nt, r    , c + 1, nd]
                    v[2] = np.nan if mask[r + 1, c     ] else data[nt, r + 1, c    , nd]
                    v[3] = np.nan if mask[r + 1, c  + 1] else data[nt, r + 1, c + 1, nd]

                    out[nt, r, c, nd] = np.nanmean(v)
    return out
