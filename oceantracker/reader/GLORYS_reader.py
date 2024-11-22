from oceantracker.reader._base_structured_reader import  _BaseStructuredReader
from oceantracker.reader.util import reader_util
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
import  oceantracker.util.time_util as time_util
import numpy as np
from datetime import  datetime
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.shared_info import shared_info as si
from oceantracker.util.numba_util import njitOT
from oceantracker.util.numpy_util import ensure_int32_dtype
from copy import copy

class GLORYSreader(_BaseStructuredReader):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params(
            dimension_map= dict(
                        z=PVC('depth', str, doc_str='name of dimensions for z layer boundaries '),
                        all_z_dims=PLC(['depth'], str, doc_str='All z dims used to identify  3D variables'),
                        row=PVC('lat', str, doc_str='row dim of grid'),
                        col=PVC('lon', str, doc_str='column dim of grid'),

                        ),
            grid_variable_map= dict(
                        time=PVC('time', str, doc_str='Name of time variable in hindcast'),
                        x = PVC('longitude', str, doc_str='x location of nodes'),
                        y = PVC('latitude', str, doc_str='y location of nodes'),
                        z=PVC('depth', str, doc_str='interface depth levels'),
                        bottom_cell_index=PVC('deptho_lev', str, doc_str='deepest vertical cell for each node'),
                        ),

            field_variable_map= {'water_velocity': PLC(['uo', 'vo','wo'], str),
                                   'tide': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                                   'water_depth': PVC('deptho', str, doc_str='maps standard internal field name to file variable name'),
                                   #'water_temperature': PVC('temp', str, doc_str='maps standard internal field name to file variable name'),
                                   #'salinity': PVC('salt', str, doc_str='maps standard internal field name to file variable name'),
                                   #'wind_stress': PVC('wind_stress', str, doc_str='maps standard internal field name to file variable name'),
                                   #'bottom_stress': PVC('bottom_stress', str, doc_str='maps standard internal field name to file variable name'),
                                   #'A_Z_profile': PVC('diffusivity', str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                   #'water_velocity_depth_averaged': PLC(['dahv'], str, fixed_len=2,
                                   #                                     doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
            variable_signature= PLC(['latitude', 'uo','vo','depth'], str, doc_str='Variable names used to test if file is this format'),
            one_based_indices = PVC(False, bool, doc_str='File has indices starting at 1, not pythons zero, eg node numbers in triangulation/simplex'),

                        )

    def get_hindcast_info(self, catalog):
        dm = self.params['dimension_map']
        fm = self.params['field_variable_map']
        hi = dict(is3D=any(d in catalog['variables'][fm['water_velocity'][0]]['dims'] for d in dm['all_z_dims']))
        if hi['is3D']:
            hi['z_dim'] = dm['z']
            hi['num_z_levels'] = catalog['info']['dims'][hi['z_dim']]
            hi['all_z_dims'] = dm['all_z_dims']

            if 'deptho_lev' in catalog['variables']:
                hi['vert_grid_type'] = si.vertical_grid_types.Zfixed
            else:
                si.msg_logger.msg('Glorys reader under development, only works for fixed zlevel grids, eg NEMO (output with "deptho_lev" variable) , contact developer to extend to sigma and other vertical grids',
                                  hint='Please provide hindcast example files to test fixes against', fatal_error=True, exit_now=True)

        else:
            hi['z_dim'] = None
            hi['num_z_levels'] = 1
            hi['all_z_dims'] = []
            hi['vert_grid_type'] = None

        # get num nodes in each field
        params= self.params
        dims = catalog['info']['dims']
        # nodes = rows* cols
        hi['num_nodes'] = dims['lat' if 'lat' in dims else 'latitude'] * dims['lon' if 'lon' in dims else 'longitude']
        return hi

    def read_horizontal_grid_coords(self, grid):
        ds = self.dataset
        gm = self.params['grid_variable_map']
        # record useful grid info
        grid['lon'] =  ds.read_variable(gm['x']).data
        grid['lat'] =  ds.read_variable(gm['y']).data

        # make a full grid coords
        nlat, nlon= grid['lat'].size, grid['lon'].size
        grid['lon'] = np.repeat(grid['lon'].reshape( 1,-1), nlat, axis= 0)
        grid['lat'] = np.repeat(grid['lat'].reshape(-1, 1), nlon, axis =1)

        grid['x'] =  np.stack((grid['lon'].ravel(),grid['lat'].ravel()),  axis=1)

        return grid['x']


    def build_hori_grid(self, grid):

        ds = self.dataset
        if 'mask' in ds.variables:
            grid['water_3D_mask'] = ds.read_variable('mask').data == 1 # water grid
            grid['water_3D_mask'] = np.transpose(grid['water_3D_mask'],(1,2,0)) # put z last
            grid['water_3D_mask'] = np.flip(grid['water_3D_mask'], axis=2) # mask 0 layer is
            grid['land_mask'] = ~grid['water_3D_mask'][:, :, -1]  # uppermost mask is the land
        else:
            pass


        grid = super().build_hori_grid(grid)
        return grid

    def build_vertical_grid(self, grid):
        # add time invariant vertical grid variables needed for transformations

        ds = self.dataset
        gm = self.grid_variable_map
        grid['z'] = ds.read_variable(gm['z']).data.astype(np.float32)
        grid['z'] = -grid['z'][::-1]  # z is positive down so take -ve
        # GLORY are fized z
        si.settings['regrid_z_to_uniform_sigma_levels'] = False  # no need to regrid

        grid = super().build_vertical_grid(grid)
        return grid

    def read_bottom_cell_index(self, grid):
        # bottom cell is in data files
        ds = self.dataset
        cat = ds.catalog
        gm = self.grid_variable_map
        grid['bottom_cell_index_grid'] = ds.read_variable(gm['bottom_cell_index']).data - self.params['one_based_indices']
        # file cell count is top down, convert to bottom up index
        grid['bottom_cell_index_grid'] = cat['info']['num_z_levels'] - grid['bottom_cell_index_grid'] # do this before making an it to capture nans
        # land nodes use 0
        sel = np.isnan(grid['bottom_cell_index_grid'])
        grid['bottom_cell_index_grid'][sel] = 0

        grid['bottom_cell_index_grid'] =  ensure_int32_dtype(grid['bottom_cell_index_grid'])

        return grid['bottom_cell_index_grid'].ravel()

    def read_file_var_as_4D_nodal_values(self,var_name, var_info, nt=None):
        # reformat file variable into 4D time,node,depth, components  form

        ml = si.msg_logger
        ds = self.dataset
        catalog = ds.catalog
        info = self.info

        dm = self.params['dimension_map']
        grid = self.grid

        # get xarray variable
        data = ds.read_variable(var_name, nt=nt)
        data_dims = data.dims
        data = data.data  # now a numpy array for numba to work on

        # add dummy time dim if none
        if info['time_dim'] not in data_dims: data = data[np.newaxis, ...]

        if any(x in info['all_z_dims'] for x in data_dims):
            data = np.transpose(data,(0,2,3,1))# move z to end
            # cell zero is at top, put at bottom
            data = np.flip(data, axis=3) # flip z

        else:
            # add dummy z dim
            data = data[..., np.newaxis]

        # data is now shaped as (time, row, col, depth)
        # now flatten (time,rows, col, depth)  to  (time,nodes, depth)
        s = data.shape
        data = data.reshape((s[0], s[1] * s[2], s[3])) # this should match flatten in "C" order

        # add dummy depth, vector components axis,
        data = data[..., np.newaxis]

        return data

    def setup_tide_field(self):
        # assume no tide, so create a dummy zero tide reader field
        i = self._add_a_reader_field('tide',dict(is3D=False,time_varying=True, initial_value=0.), dummy=True)
        return i

    def update_tide_field(self, buffer_index, nt):
        # there is no tide, so set to zero
       field = self.fields['tide']
       pass


    def read_dry_cell_data(self, nt_index, buffer_index):
        # get dry cells from water depth and tide
        grid = self.grid
        fields = self.fields
        reader_util.set_dry_cell_flag_from_tide(grid['triangles'], fields['tide'].data, fields['water_depth'].data,
                                                si.settings.minimum_total_water_depth, grid['is_dry_cell_buffer'], buffer_index)
        pass


    @staticmethod
    @njitOT
    def find_deepest_zlayer_in_water_not_used(water_3D_mask):
        # find deepset water cell seraching up from bottom
        s= water_3D_mask.shape
        deepest_cell= np.full(s[:2],-1, dtype=np.int32) # -1 is no data
        for r in range(s[0]):
            for c in range(s[1]):
                for nz in range(s[2]): # loop over depth cells
                    if water_3D_mask[r, c, nz]: # find first non masked value
                        deepest_cell[r, c] = nz
                        break
        return deepest_cell