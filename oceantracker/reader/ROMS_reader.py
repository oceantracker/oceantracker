

# Sample data subset
# https://www.seanoe.org/data/00751/86286/
#better?
#https://tds.marine.rutgers.edu/thredds/ncss/roms/doppio/DopAnV2R3-ini2007_da/his?var=h&var=mask_psi&var=mask_rho&var=mask_u&var=mask_v&var=ubar&var=vbar&var=zeta&var=temp&var=u&var=v&var=w&north=35.25&west=-77&east=-76&south=34.3&horizStride=1&time_start=2021-08-01T01%3A00%3A00Z&time_end=2021-08-02T00%3A00%3A00Z&timeStride=1&vertCoord=&accept=netcdf

# full grid 12 houly on month
# https://tds.marine.rutgers.edu/thredds/ncss/roms/doppio/DopAnV2R3-ini2007_da/his?var=f&var=h&var=mask_psi&var=mask_rho&var=mask_u&var=mask_v&var=ubar&var=vbar&var=zeta&var=temp&var=u&var=v&var=w&disableLLSubset=on&disableProjSubset=on&horizStride=1&time_start=2007-01-02T01%3A00%3A00Z&time_end=2007-01-31T00%3A00%3A00Z&timeStride=12&vertCoord=&accept=netcdf
from oceantracker.reader._base_structured_reader import _BaseStructuredReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util
import numpy as np
from datetime import datetime
from numba import njit
from matplotlib import pyplot as plt, tri
from oceantracker.reader.util.reader_util import append_split_cell_data

from oceantracker.util.triangle_utilities import split_quad_cells
from oceantracker.util.numba_util import njitOT

from oceantracker.shared_info import shared_info as si


from oceantracker.reader.util import reader_util
from oceantracker.reader.util.hydromodel_grid_transforms import convert_mid_layer_sigma_top_bot_layer_values
from oceantracker.util.ncdf_util import NetCDFhandler
# todo use ROMs turbulent viscosity for dispersion
#todo use  openbondary data to improve identifcation of open boundary nodes?
#todo implement depth average mode using depth average variables in the file
#todo friction velocity from bottom stress ???

class ROMsNativeReader(_BaseStructuredReader):
    # reads  ROMS file, and tranforms all data to PSI grid
    # then splits all triangles in two to  use in oceantracker as a triangular grid,
    # so works with curvilinear ROMS grids
     # note: # ROMS is Fortan code so np.flatten() in F order

    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults
        self.add_default_params(
                hydro_model_cords_geographic= PVC(False, bool, doc_str='Force conversion given nodal lat longs to a UTM meters grid, only used if lat long coordinates not auto detected'),

                field_variable_map= {'water_velocity': PLC(['u','v','w'], str, fixed_len=3),
                                    'water_depth': PVC('h', str),
                                    'tide': PVC('zeta', str),
                                    'water_temperature': PVC('temp', str) ,
                                    'bottom_stress': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                                    'A_Z_profile': PVC(None, str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                    'water_velocity_depth_averaged':PLC(['ubar','vbar'], str, fixed_len=2),
                                    },
                grid_variable_map=dict(
                                    time=PVC('ocean_time', str, doc_str='Name of time variable in hindcast'),
                                    x=PVC('lon_psi', str),
                                    y=PVC('lat_psi', str)),
                dimension_map=dict(  z=PVC('s_w', str, doc_str='name of dimensions for z layer boundaries '),
                            all_z_dims=PLC(['s_w','s_rho'], str, doc_str='All z dims used to identify  3D variables'),
                             row=PVC('eta_psi', str, doc_str='row dim of grid'),
                            col=PVC('xi_psi', str, doc_str='column dim of grid'),
                                      ),

                variable_signature= PLC(['ocean_time','mask_psi','lat_psi','lon_psi','h','zeta','u','v'], str,
                                         doc_str='Variable names used to test if file is this format'),
                  )
        pass

    def get_hindcast_info(self, catalog):
        hi = dict(is3D=True)
        if hi['is3D']:
            hi['z_dim'] = self.params['dimension_map']['z']
            hi['num_z_levels'] = catalog['info']['dims'][hi['z_dim']]
            hi['all_z_dims'] = self.params['dimension_map']['all_z_dims']
            hi['vert_grid_type'] = si.vertical_grid_types.Sigma  # Slayer uses zero bottom cell, so treated the dame
        else:
            hi['z_dim'] = None
            hi['num_z_levels'] = 0
            hi['num_z_levels'] = 0
            hi['all_z_dims'] = []
            hi['vert_grid_type'] = None

        # get num nodes in each field
        params= self.params
        dims = catalog['info']['dims']
        # nodes = rows* cols
        hi['num_nodes'] = dims[params['dimension_map']['row']] * dims[params['dimension_map']['col']]
        return hi

    def build_hori_grid(self, grid):
        # pre-read useful info
        ds = self.dataset
        grid['psi_land_mask'] = ds.read_variable('mask_psi').data != 1
        grid['u_land_mask'] = ds.read_variable('mask_u').data  != 1
        grid['v_land_mask'] = ds.read_variable('mask_v').data  != 1
        grid['rho_land_mask'] = ds.read_variable('mask_rho').data  != 1

        # build a full land mask based on the psi grid
        grid['land_mask'] = grid['psi_land_mask'].copy() # the used grid's mask
        # mask psi node if either v node either side is mask
        m = np.logical_or(grid['v_land_mask'][:, 1:], grid['v_land_mask'][:, :-1])
        grid['land_mask'] = np.logical_or(grid['land_mask'] , m)

        # mask psi node if either u node above or below is masked
        m = np.logical_or(grid['u_land_mask'][ 1:,:], grid['u_land_mask'][:-1, :])
        grid['land_mask'] = np.logical_or(grid['land_mask'], m)

        grid = super().build_hori_grid(grid)

        return grid

    def build_vertical_grid(self, grid):
        # add time invariant vertical grid variables needed for transformations
        # first values in z axis is the top? so flip
        ds = self.dataset
        grid['sigma']       = 1. + ds.read_variable('s_w').data.astype(np.float32)  # layer boundary fractions reversed from negative values
        grid['sigma_layer'] = 1. + ds.read_variable('s_rho').data.astype(np.float32)  # layer center fractions


        grid = super().build_vertical_grid(grid)
        return grid

    def read_horizontal_grid_coords(self, grid):
        ds = self.dataset
        gm = self.params['grid_variable_map']
        # record useful grid info
        grid['lon'] =  ds.read_variable(gm['x']).data
        grid['lat'] =  ds.read_variable(gm['y']).data

        grid['x'] =  np.stack((grid['lon'].ravel(),grid['lat'].ravel()),  axis=1)

        return grid['x']



    def read_dry_cell_data(self, nt_index, buffer_index):
        # get dry cells from water depth and tide
        grid= self.grid
        fields= self.fields
        reader_util.set_dry_cell_flag_from_tide(grid['triangles'],fields['tide'].data, fields['water_depth'].data,
                                                si.settings.minimum_total_water_depth,grid['is_dry_cell_buffer'],buffer_index )
        pass


    def read_file_var_as_4D_nodal_values(self,var_name, var_info, nt=None):
        # reformat file variable into 4D time,node,depth, components  form
        ml = si.msg_logger
        ds = self.dataset
        info = self.info
        dm = self.params['dimension_map']
        grid = self.grid

        # get xarray variable
        data = ds.read_variable(var_name, nt=nt)
        data_dims = data.dims
        data = data.data  # now a numpy array for numba to work on

        # add dummy time dim if none
        if info['time_dim'] not in data_dims: data = data[np.newaxis,...]

        if any(x in info['all_z_dims'] for x in data_dims):
            # move depth to last dim
            # also depth dim [0] is deepest value, like schisim, ie cold water at bottom
            data = np.transpose(data,[0,2,3,1])
        else:
            # add dummy z dim
            data = data[..., np.newaxis]

        # data is now shaped as (time, row, col, depth)

        # convert data  to psi grid, from other variable grids if needed
        if 'eta_rho' in data_dims:
            data = rho_grid_to_psi(data, grid['rho_land_mask'])

        elif 'eta_u' in data_dims:
            # masked value 10^36 ,  so set to zero before finding mean value for psi grid
            data = u_grid_to_psi(data, grid['u_land_mask'])

        elif  'eta_v' in data_dims:
            data = v_grid_to_psi(data, grid['v_land_mask'])

        # now flatten (time,rows, col, depth)  to  (time,nodes, depth)
        s = data.shape

        # check if rows/cols now  consistent with Psi grid
        if not (grid['psi_land_mask'].shape == s[1:3]):
            ml.msg('not all ROMS variables consisted and cannot map all to psi grid, may be in-correctly formed subset of full model domain , try with full model domain, files variable "' + var_name +'"',
                              fatal_error=True, caller=self)

        data = data.reshape( (s[0],s[1]*s[2], s[3])) # this should match flatten in "C" order

        if 's_rho' in data_dims:
            # convert mid-layer values to values at layer boundaries, ie zlevels
            data = convert_mid_layer_sigma_top_bot_layer_values(data, grid['sigma_layer'], grid['sigma'])

        # add dummy vector components axis, note in ROMS vectors are stored in netcdf as individual components,
        data = data[:, :, :, np.newaxis]

        return data


    def preprocess_field_variable(self, name,grid, data):
        if name =='water_velocity':
            if data.shape[2] > 1:
                # ensure water vel at bottom is zero
                # linear extrapolation of 3D velocity to bottom zlevel, may not give zero vel at bottom so set to zero
                data[:, :, 0, :]= 0.

        return data




    def _dev_show_grid(self):
        # plots to help with development
        grid = self.grid

        fig1, ax1 = plt.subplots()
        ax1.scatter(grid['x'][:,0],grid['x'][:,1],c='k', marker='.', s=4)
        ax1.triplot(grid['x'][:,0],grid['x'][:,1],grid['triangles'])


        fig2, ax2 = plt.subplots()
        ax2.scatter(grid['lon_psi'] , grid['lat_psi'] , c='k', marker='.', s=4)
        sel= grid['land_mask']
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
