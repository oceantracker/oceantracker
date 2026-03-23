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

        # Fine grid has (2N-1)×(2M-1) nodes: T-centres + edge midpoints + corners
        dims = info['dims']
        N_lat = dims['lat' if 'lat' in dims else 'latitude']
        N_lon = dims['lon' if 'lon' in dims else 'longitude']
        info['num_nodes'] = (2 * N_lat - 1) * (2 * N_lon - 1)


    def read_horizontal_grid_coords(self, grid):
        ds = self.dataset
        gm = self.params['grid_variable_map']
        lon1d = ds.read_variable(gm['x']).data.astype(np.float32)
        lat1d = ds.read_variable(gm['y']).data.astype(np.float32)

        # Store original T-grid sizes (used in read_file_var_as_4D_nodal_values)
        grid['_nlat_t'] = lat1d.size
        grid['_nlon_t'] = lon1d.size

        # Build interleaved fine 1-D coordinate arrays of length (2N-1):
        #   even indices → original T-point positions
        #   odd  indices → midpoints between adjacent T-points
        lon_fine = np.empty(2 * lon1d.size - 1, dtype=np.float32)
        lat_fine = np.empty(2 * lat1d.size - 1, dtype=np.float32)
        lon_fine[0::2] = lon1d
        lon_fine[1::2] = (lon1d[:-1] + lon1d[1:]) / 2.0
        lat_fine[0::2] = lat1d
        lat_fine[1::2] = (lat1d[:-1] + lat1d[1:]) / 2.0

        nlat_f, nlon_f = lat_fine.size, lon_fine.size
        grid['lon'] = np.repeat(lon_fine.reshape(1, -1), nlat_f, axis=0)
        grid['lat'] = np.repeat(lat_fine.reshape(-1, 1), nlon_f, axis=1)
        grid['x']   = np.stack((grid['lon'].ravel(), grid['lat'].ravel()), axis=1)


    def build_hori_grid(self, grid):

        ds = self.dataset
        if 'mask' in self.info['variables']:
            water_t = ds.read_variable('mask').data == 1   # (nz, N_lat, N_lon)
            water_t = np.transpose(water_t, (1, 2, 0))    # → (N_lat, N_lon, nz)
            water_t = np.flip(water_t, axis=2)

            N_lat, N_lon, nz = water_t.shape
            water_fine = np.zeros((2 * N_lat - 1, 2 * N_lon - 1, nz), dtype=bool)

            # T-points: direct
            water_fine[0::2, 0::2, :] = water_t
            # Horizontal edge midpoints: wet if either H-neighbour is wet
            water_fine[0::2, 1::2, :] = water_t[:, :-1, :] | water_t[:, 1:, :]
            # Vertical edge midpoints: wet if either V-neighbour is wet
            water_fine[1::2, 0::2, :] = water_t[:-1, :, :] | water_t[1:, :, :]
            # Corner F-points: wet if any of the 4 surrounding T-cells is wet
            water_fine[1::2, 1::2, :] = (water_t[:-1, :-1, :] | water_t[1:, :-1, :] |
                                          water_t[:-1, 1:, :]  | water_t[1:, 1:, :])

            grid['water_3D_mask'] = water_fine
            grid['land_mask'] = ~water_fine[:, :, -1]

            # Additionally mask any fine-grid node whose water_depth (deptho) would be NaN.
            # The mask variable and deptho can be inconsistent at the coast, so some nodes
            # pass the mask filter but have no valid depth.  Treat those as land too.
            depth_var = self.params['field_variable_map']['water_depth']
            if depth_var in self.info['variables']:
                deptho_t = ds.read_variable(depth_var).data.astype(np.float32)  # (N_lat, N_lon)
                depth_valid_t = np.isfinite(deptho_t)  # True = has valid depth

                # A fine-grid node has valid depth if ANY contributing T-cell has valid depth
                # (same OR logic as water_fine above)
                depth_valid_fine = np.zeros((2 * N_lat - 1, 2 * N_lon - 1), dtype=bool)
                depth_valid_fine[0::2, 0::2] = depth_valid_t
                depth_valid_fine[0::2, 1::2] = depth_valid_t[:, :-1] | depth_valid_t[:, 1:]
                depth_valid_fine[1::2, 0::2] = depth_valid_t[:-1, :] | depth_valid_t[1:, :]
                depth_valid_fine[1::2, 1::2] = (depth_valid_t[:-1, :-1] | depth_valid_t[:-1, 1:] |
                                                 depth_valid_t[1:,  :-1] | depth_valid_t[1:,  1:])

                grid['land_mask'] |= ~depth_valid_fine
        else:
            pass

        super().build_hori_grid(grid)

    def read_triangles(self, grid):
        # Build the fine-grid node numbering (same as the base helper)
        mask = grid['land_mask']
        rows = np.arange(mask.shape[0])
        cols = np.arange(mask.shape[1])
        grid['grid_node_numbers'] = cols.size * rows.reshape((-1, 1)) + cols.reshape((1, -1))

        n1 = grid['grid_node_numbers'][:-1, :-1]
        n2 = grid['grid_node_numbers'][:-1, 1:]
        n3 = grid['grid_node_numbers'][1:,  1:]
        n4 = grid['grid_node_numbers'][1:,  :-1]
        quad_cells = np.stack(
            (n1.flatten('C'), n2.flatten('C'), n3.flatten('C'), n4.flatten('C'))
        ).T

        # Strict filter: only keep quads where ALL 4 nodes are water.
        # The base-class filter (<3 land nodes) allows mixed quads, which after
        # split_quad_cells produce one valid and one all-NaN triangle ("single triangle").
        # Requiring 0 land nodes ensures both split triangles are always kept/dropped together.
        mask_flat = mask.flatten('C')
        sel = np.sum(mask_flat[quad_cells], axis=1) == 0
        grid['triangles'] = quad_cells[sel, :]


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
        gm = self.params['grid_variable_map']
        b = ds.read_variable(gm['bottom_interface_index']).data  # (N_lat, N_lon)

        b = b.astype(np.float32)
        b[b < 0] = np.nan   # land cells → NaN

        N_lat, N_lon = b.shape
        b_fine = np.full((2 * N_lat - 1, 2 * N_lon - 1), np.nan, dtype=np.float32)

        # T-points: direct values
        b_fine[0::2, 0::2] = b
        # Horizontal edge midpoints: shallowest of 2 H-neighbours (np.fmin ignores NaN)
        b_fine[0::2, 1::2] = np.fmin(b[:, :-1], b[:, 1:])
        # Vertical edge midpoints: shallowest of 2 V-neighbours
        b_fine[1::2, 0::2] = np.fmin(b[:-1, :], b[1:, :])
        # Corner F-points: shallowest of 4 surrounding T-cells
        b_fine[1::2, 1::2] = np.fmin(np.fmin(b[:-1, :-1], b[:-1, 1:]),
                                      np.fmin(b[1:,  :-1], b[1:,  1:]))

        b_fine -= self.params['one_based_indices']
        b_fine = info['num_z_interfaces'] - b_fine  # top-down → bottom-up index

        b_fine[np.isnan(b_fine)] = -1   # land nodes

        grid['bottom_interface_index_grid'] = b_fine.astype(np.int32)
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
        # Expand T-grid to fine (2N_lat-1, 2N_lon-1) grid using 9-point stencil:
        #   (even, even) = T-point          → direct value
        #   (even, odd)  = H-edge midpoint  → NaN-safe mean of 2 H-neighbours
        #   (odd,  even) = V-edge midpoint  → NaN-safe mean of 2 V-neighbours
        #   (odd,  odd)  = corner F-point   → NaN-safe mean of 4 surrounding T-cells
        nt, N_lat, N_lon, nz = data.shape
        data_fine = np.full((nt, 2 * N_lat - 1, 2 * N_lon - 1, nz), np.nan, dtype=np.float32)

        # T-points
        data_fine[:, 0::2, 0::2, :] = data

        # Horizontal edge midpoints
        d_l, d_r = data[:, :, :-1, :], data[:, :, 1:, :]
        v_h = np.isfinite(d_l).astype(np.float32) + np.isfinite(d_r).astype(np.float32)
        data_fine[:, 0::2, 1::2, :] = np.where(
            v_h > 0, np.nansum(np.stack([d_l, d_r], axis=0), axis=0) / v_h, np.nan)

        # Vertical edge midpoints
        d_b, d_t = data[:, :-1, :, :], data[:, 1:, :, :]
        v_v = np.isfinite(d_b).astype(np.float32) + np.isfinite(d_t).astype(np.float32)
        data_fine[:, 1::2, 0::2, :] = np.where(
            v_v > 0, np.nansum(np.stack([d_b, d_t], axis=0), axis=0) / v_v, np.nan)

        # Corner F-points
        d00, d01 = data[:, :-1, :-1, :], data[:, :-1, 1:, :]
        d10, d11 = data[:, 1:,  :-1, :], data[:, 1:,  1:, :]
        v_c = sum(np.isfinite(x).astype(np.float32) for x in [d00, d01, d10, d11])
        data_fine[:, 1::2, 1::2, :] = np.where(
            v_c > 0, np.nansum(np.stack([d00, d01, d10, d11], axis=0), axis=0) / v_c, np.nan)

        data = data_fine

        # flatten (time, 2N_lat-1, 2N_lon-1, depth) → (time, nodes, depth)
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