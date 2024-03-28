

# Sample data subset
# https://www.seanoe.org/data/00751/86286/
#better?
#https://tds.marine.rutgers.edu/thredds/ncss/roms/doppio/DopAnV2R3-ini2007_da/his?var=h&var=mask_psi&var=mask_rho&var=mask_u&var=mask_v&var=ubar&var=vbar&var=zeta&var=temp&var=u&var=v&var=w&north=35.25&west=-77&east=-76&south=34.3&horizStride=1&time_start=2021-08-01T01%3A00%3A00Z&time_end=2021-08-02T00%3A00%3A00Z&timeStride=1&vertCoord=&accept=netcdf

# full grid 12 houly on month
# https://tds.marine.rutgers.edu/thredds/ncss/roms/doppio/DopAnV2R3-ini2007_da/his?var=f&var=h&var=mask_psi&var=mask_rho&var=mask_u&var=mask_v&var=ubar&var=vbar&var=zeta&var=temp&var=u&var=v&var=w&disableLLSubset=on&disableProjSubset=on&horizStride=1&time_start=2007-01-02T01%3A00%3A00Z&time_end=2007-01-31T00%3A00%3A00Z&timeStride=12&vertCoord=&accept=netcdf
from oceantracker.reader._base_reader import _BaseReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util
import numpy as np
from datetime import datetime
from numba import njit
from matplotlib import pyplot as plt, tri
from oceantracker.reader.util.reader_util import append_split_cell_data
from oceantracker.reader.util.hydromodel_grid_transforms import convert_regular_grid_to_triangles
from oceantracker.util.triangle_utilities import split_quad_cells
from oceantracker.util.numba_util import njitOT

from oceantracker.shared_info import SharedInfo as si


from oceantracker.reader.util import reader_util
from oceantracker.reader.util.hydromodel_grid_transforms import convert_layer_field_to_levels_from_fixed_depth_fractions
from oceantracker.util.ncdf_util import NetCDFhandler
# todo use ROMs turbulent viscosity for dispersion
#todo use  openbondary data to improve identifcation of open boundary nodes?
#todo implement depth average mode using depth average variables in the file
#todo friction velocity from bottom stress ???

class ROMsNativeReader(_BaseReader):
    # reads  ROMS file, and tranforms all data to PSI grid
    # then splits all triangles in two to  use in oceantracker as a triangular grid,
    # so works with curvilinear ROMS grids
     # note: # ROMS is Fortan code so np.flatten() in F order

    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({ 'field_variable_map': {'water_velocity': PLC(['u','v','w'], [str], fixed_len=3),
                                                    'water_depth': PVC('h', str),
                                                    'tide': PVC('zeta', str),
                                                    'water_temperature': PVC('temp', str) ,
                                                    'bottom_stress': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                                                    'A_Z_profile': PVC(None, str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                                    'water_velocity_depth_averaged':PLC(['ubar','vbar'], [str], fixed_len=2),
                                  }
                                  })


    def is_file_format(self, file_name):
        nc = self._open_file(file_name)
        is_file_type=  set(['ocean_time','mask_psi','lat_psi','lon_psi','h','zeta','u','v']).issubset(list(nc.variable_info.keys()))
        nc.close()
        return is_file_type
    def build_hori_grid(self, nc, grid):
        # pre-read useful info
        grid['psi_land_mask'] = nc.read_a_variable('mask_psi') != 1
        grid['u_land_mask'] = nc.read_a_variable('mask_u') != 1
        grid['v_land_mask'] = nc.read_a_variable('mask_v') != 1
        grid['rho_land_mask'] = nc.read_a_variable('mask_rho') != 1

        grid = super().build_hori_grid(nc, grid)

        return grid

    def build_vertical_grid(self, nc, grid):
        # add time invariant vertical grid variables needed for transformations
        # first values in z axis is the top? so flip
        grid['sigma'] = 1+ nc.read_a_variable('s_w', sel=None).astype(np.float32)  # layer boundary fractions reversed from negative values
        grid['sigma_layer'] =1 + nc.read_a_variable('s_rho', sel=None).astype(np.float32)  # layer center fractions
        grid['vertical_grid_type'] = 'S-sigma'

        grid['nz'] = grid['sigma'].size  # used to size field data arrays

        #ROMS are uniform sigma
        si.settings['regrid_z_to_uniform_sigma_levels'] = False # no need to regrid
        grid = self._make_sigma_depth_cell_search_map(nc, grid)

        return grid

    def set_up_uniform_sigma(self, nc, grid): return grid

    def read_horizontal_grid_coords(self, nc, grid):

        # record useful grid info
        grid['lat_psi'] = nc.read_a_variable('lat_psi').astype(np.float64)
        grid['lon_psi'] = nc.read_a_variable('lon_psi').astype(np.float64)

        grid['lon_lat_grid'] =  np.stack((grid['lon_psi'],grid['lat_psi']),  axis=2)
        s=   grid['lon_lat_grid'].shape
        grid['lon_lat']=   grid['lon_lat_grid'].reshape(s[0]*s[1],s[2])
        grid['hydro_model_cords_in_lat_long'] = True
        grid['x'] = self.convert_lon_lat_to_meters_grid(grid['lon_lat'])

        # get land mask

        return grid

    def read_triangles_as_int32(self, nc, grid):
        # build triangles from regular grid
        grid = convert_regular_grid_to_triangles(grid, grid['psi_land_mask'] )
        # get nodes for each corner of quad

        return grid

    def is_hindcast3D(self, nc):  return nc.is_var('u') # are always 3D

    def get_field_params(self,nc, name, crumbs=''):
        # work out if feild is 3D ,etc
        fmap = self.params['field_variable_map'][name]
        if type(fmap) != list: fmap =[fmap]
        f_params = dict(time_varying = nc.is_var_dim(fmap[0], 'ocean_time'),
                        is3D = nc.is_var_dim(fmap[0],'s_rho') or nc.is_var_dim(fmap[0],'s_w'),
                        is_vector = len(fmap) > 1,
                        )
        return f_params

    def read_zlevel_as_float32(self, nc, grid,fields, file_index, zlevel_buffer, buffer_index):
        # calcuate zlevel from depth fractions, tide and water depth
        # FVCOM has fraction of depth < from free surface, with top value first in z dim of arrAy
        # todo check first value is the bottom or free surface+-??

        # time varying zlevel from fixed water depth fractions and total water depth at nodes

        water_depth = fields['water_depth'].data[:, :, :, 0]
        tide = fields['tide'].data[:, :, :, 0]

        zlevel_buffer[buffer_index, ...] = grid['z_fractions'][np.newaxis, ...]*(tide[buffer_index, :, :]+water_depth) - water_depth
        pass

    def read_dry_cell_data(self, nc, grid,fields,  file_index,is_dry_cell_buffer,buffer_index):
        # get dry cells from water depth and tide
        reader_util.set_dry_cell_flag_from_tide(grid['triangles'],fields['tide'].data, fields['water_depth'].data,
                                                si.settings.minimum_total_water_depth, is_dry_cell_buffer,buffer_index )
        pass

    def read_time_sec_since_1970(self, nc, file_index=None):
        # get times relative to base date from netcdf encoded  strings
        var_name = 'ocean_time'
        if file_index is None:
            time_sec = nc.read_a_variable(var_name, sel=None)
        else:
            time_sec = nc.read_a_variable(var_name, sel=file_index)

        base_date = nc.var_attr(var_name,'units').split('since ')[-1]
        t0 = time_util.isostr_to_seconds(base_date)

        time_sec += t0

        return time_sec

    def read_file_var_as_4D_nodal_values(self,nc, grid, var_name, file_index=None):
        # reformat file variable into 4D time,node,depth, components  form

        ml = si.msg_logger

        data = nc.read_a_variable(var_name, sel=file_index)

        # add dummy time dim if none
        if not nc.is_var_dim(var_name, 'ocean_time'): data = data[np.newaxis,...]

        if nc.is_var_dim(var_name, 's_w') or nc.is_var_dim(var_name, 's_rho'):
            # move depth to last dim
            # also depth dim [0] is deepest value, like schisim, ie cold water at bottom
            data = np.transpose(data,[0,2,3,1])
        else:
            # add dummy z dim
            data = data[..., np.newaxis]

        # data is now shaped as (time, row, col, depth)

        # convert data  to psi grid, from other variable grids if needed
        if nc.is_var_dim(var_name,'eta_rho'):
            data = rho_grid_to_psi(data, grid['rho_land_mask'])

        elif nc.is_var_dim(var_name,'eta_u'):
            # masked value 10^36 ,  so set to zero before finding mean value for psi grid
            data = u_grid_to_psi(data, grid['u_land_mask'])

        elif nc.is_var_dim(var_name,'eta_v'):
            data = v_grid_to_psi(data, grid['v_land_mask'])

        # now flatten (time,rows, col, depth)  to  (time,nodes, depth)
        s = data.shape

        # check if rows/cols now  consistent with Psi grid
        if not (grid['psi_land_mask'].shape == s[1:3]):
            ml.msg('not all ROMS variables consisted and cannot map all to psi grid, may be in-correctly formed subset of full model domain , try with full model domain, files variable "' + var_name +'"',
                              fatal_error=True,exit_now=True, caller=self)

        data = data.reshape( (s[0],s[1]*s[2], s[3])) # this should match flatten in "C" order

        if nc.is_var_dim(var_name,'s_rho'):
            # convert mid-layer values to values at layer boundaries, ie zlevels
            data = convert_layer_field_to_levels_from_fixed_depth_fractions(
                data, grid['sigma_layer'], grid['sigma'])

        # add dummy vector components axis, note in ROMS vectors are stored in netcdf as individual components,

        data = data[:, :, :, np.newaxis]

        return data






    def preprocess_field_variable(self, nc,name,grid, data):

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

@njitOT
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

@njitOT
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

@njitOT
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
