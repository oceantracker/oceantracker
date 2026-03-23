from oceantracker.reader._base_structured_reader import  _BaseStructuredReader
from oceantracker.reader.util import reader_util
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
import  oceantracker.util.time_util as time_util
import numpy as np
from datetime import  datetime
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.shared_info import shared_info as si
from oceantracker.util.numba_util import njitOT

from copy import copy

class GLORYSreader(_BaseStructuredReader):

    development = True
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
                        z = PVC('depth', str, doc_str='interface depth levels'),
                        bottom_interface_index=PVC('deptho_lev', str, doc_str='deepest vertical cell for each node'),
                        ),
            field_variable_map= {'water_velocity': PLC(['uo', 'vo','wo'], str),
                                   'tide': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                                   'water_depth': PVC('deptho', str, doc_str='maps standard internal field name to file variable name'),
                                   'water_temperature': PVC('thetao', str, doc_str='maps standard internal field name to file variable name'),
                                   'salinity': PVC('so', str, doc_str='maps standard internal field name to file variable name'),
                                   #'wind_stress': PLC(None, str, doc_str='maps standard internal field name to file variable name'),
                                   #'bottom_stress': PLC(['bottom_stress'], str, doc_str='maps standard internal field name to file variable name'),
                                   #'A_Z_profile': PVC('diffusivity', str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                   #'water_velocity_depth_averaged': PLC(['dahv'], str, fixed_len=2,
                                   #                                     doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
            variable_signature= PLC(['time','latitude', 'uo','vo'], str, doc_str='Variable names used to test if file is this format'),
            one_based_indices = PVC(False, bool, doc_str='File has indices starting at 1, not pythons zero, eg node numbers in triangulation/simplex'),
                        )

    def add_hindcast_info(self):
        params= self.params
        info = self.info
        dm = params['dimension_map']
        fm = params['field_variable_map']

        if 'mask' not in info['variables']:
            si.msg_logger.msg('For GLORYS hindcasts, must include the static variables netcdf file in same folder as the currents hindcast files, as need variables such as the land mask in that file',
                              hint =f'reader "file_mask" param, must also include static file as  well, given mask {self.params["file_mask"]}',
                              caller = self, error=True, fatal_error=True)
        if info['is3D']:
            # sort out z dim and vertical grid size
            info['z_dim'] = dm['z']
            info['num_z_interfaces'] = info['dims'][info['z_dim']]
            info['all_z_dims'] = dm['all_z_dims']
            if 'deptho_lev' in info['variables']:
                info['vert_grid_type'] = si.vertical_grid_types.Zfixed
            else:
                si.msg_logger.msg('Glorys reader under development, only works for fixed z_interface grids, eg NEMO (output with "deptho_lev" variable) , contact developer to extend to sigma and other vertical grids',
                                  hint='Please provide hindcast example files to test fixes against', fatal_error=True)
        else:
            info['vert_grid_type'] = None

        # F-corner grid has one fewer node in each horizontal direction than the T-grid
        dims = info['dims']
        info['num_nodes'] = (dims['lat' if 'lat' in dims else 'latitude'] - 1) * (dims['lon' if 'lon' in dims else 'longitude'] - 1)


    def read_horizontal_grid_coords(self, grid):
        ds = self.dataset
        gm = self.params['grid_variable_map']
        lon1d = ds.read_variable(gm['x']).data
        lat1d = ds.read_variable(gm['y']).data

        # Store T-grid sizes for use in read_file_var_as_4D_nodal_values
        grid['_nlat_t'] = lat1d.size
        grid['_nlon_t'] = lon1d.size

        # F-corner positions: midpoint between each pair of adjacent T-centres.
        # GLORYS provides data at cell centres (T-points); OceanTracker needs
        # nodal (corner) values.  The F-grid has one fewer point per dimension.
        lon_c = ((lon1d[:-1] + lon1d[1:]) / 2.0).astype(np.float32)
        lat_c = ((lat1d[:-1] + lat1d[1:]) / 2.0).astype(np.float32)

        nlat_c, nlon_c = lat_c.size, lon_c.size
        grid['lon'] = np.repeat(lon_c.reshape(1, -1), nlat_c, axis=0)
        grid['lat'] = np.repeat(lat_c.reshape(-1, 1), nlon_c, axis=1)
        grid['x']   = np.stack((grid['lon'].ravel(), grid['lat'].ravel()), axis=1)


    def build_hori_grid(self, grid):

        ds = self.dataset
        if 'mask' in self.info['variables']:
            water_t = ds.read_variable('mask').data == 1  # (nz, N_lat, N_lon), True = water
            water_t = np.transpose(water_t, (1, 2, 0))   # → (N_lat, N_lon, nz)
            water_t = np.flip(water_t, axis=2)

            # Convert 3-D mask to F-corner grid: a corner is wet at depth nz if
            # at least one of its 4 surrounding T-cells is wet at that depth.
            grid['water_3D_mask'] = (water_t[:-1, :-1, :] | water_t[1:, :-1, :] |
                                     water_t[:-1, 1:, :]  | water_t[1:, 1:, :])

            # Land mask on F-grid: corner is land only if all 4 surrounding
            # surface T-cells are land.
            grid['land_mask'] = ~grid['water_3D_mask'][:, :, -1]
        else:
            pass

        super().build_hori_grid(grid)


    def build_vertical_grid(self):
        # add time invariant vertical grid variables needed for transformations

        ds = self.dataset
        grid = self.grid
        gm = self.params['grid_variable_map']
        grid['z'] = ds.read_variable(gm['z']).data.astype(np.float32)
        grid['z'] = -grid['z'][::-1]  # z is positive down so take -ve

        super().build_vertical_grid()


    def read_bottom_interface_index(self, grid):
        # bottom cell is in data files
        ds = self.dataset
        info = self.info
        gm =  self.params['grid_variable_map']
        b = ds.read_variable(gm['bottom_interface_index']).data

        # ensure missing values are nans so missing stay missing in changing to bottom up values
        b = b.astype(np.float32)
        b[b < 0] = np.nan

        # T-centre → F-corner: take the minimum (shallowest) valid bottom index
        # among the 4 surrounding T-cells so we never extrapolate below any neighbour.
        b_stack = np.stack([b[:-1, :-1], b[1:, :-1], b[:-1, 1:], b[1:, 1:]], axis=0)
        b = np.nanmin(b_stack, axis=0)  # (N_lat-1, N_lon-1)

        b -= self.params['one_based_indices']

        # file cell count is top down, convert to bottom up index
        b = info['num_z_interfaces'] - b

        # land corners use -1
        sel = np.isnan(b)
        b[sel] = -1

        grid['bottom_interface_index_grid'] = b.astype(np.int32)
        return grid['bottom_interface_index_grid'].ravel()

    def read_file_var_as_4D_nodal_values(self,var_name, var_info,  nt=None):
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
        if info['time_dim'] not in data_dims: data = data[np.newaxis, ...]

        if any(x in info['all_z_dims'] for x in data_dims):
            data = np.transpose(data,(0,2,3,1))# move z to end
            # cell zero is at top, put at bottom
            data = np.flip(data, axis=3) # flip z

        else:
            # add dummy z dim
            data = data[..., np.newaxis]

        # data is now shaped as (time, N_lat, N_lon, depth)
        # T-centre → F-corner: NaN-safe 4-point average over the 4 surrounding T-cells.
        # Reduces each horizontal dimension by 1: → (time, N_lat-1, N_lon-1, depth)
        d00 = data[:, :-1, :-1, :]
        d01 = data[:, :-1, 1:,  :]
        d10 = data[:, 1:,  :-1, :]
        d11 = data[:, 1:,  1:,  :]
        valid = (np.isfinite(d00) + np.isfinite(d01) +
                 np.isfinite(d10) + np.isfinite(d11)).astype(np.float32)
        data = np.where(valid > 0,
                        np.nansum(np.stack([d00, d01, d10, d11], axis=0), axis=0) / valid,
                        np.nan).astype(np.float32)

        # now flatten (time, N_lat-1, N_lon-1, depth) to (time, nodes, depth)
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