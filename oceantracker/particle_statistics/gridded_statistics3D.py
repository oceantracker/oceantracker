
import numpy as np
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange
from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.shared_info import shared_info as si
from oceantracker.particle_statistics.gridded_statistics2D import GriddedStats2D_timeBased
from oceantracker.particle_statistics.util import stats_util
from oceantracker.util import regular_grid_util

class GriddedStats3D_timeBased(GriddedStats2D_timeBased):
    # class to hold counts of particles inside 3D grid cells
    '''
    Counts particles into 3D regular grid at given interval. Extends 2D grid version.
    '''
    def __init__(self):
        # set up info/attributes
        super().__init__()
        regular_grid_util.add_grid_default_params(self.default_params,is3D=True, grid_center_required=False)

        # add 3D specific parameters
        self.add_default_params(
            z_min = PVC(None, float, is_required=True,
                        doc_str='Bottom of 3D counting grid. Interpretation depends on vertical_range_measured_relative_to: '
                                '"geoid" = meters above chart datum (negative at depth, z=0 at MSL); '
                                '"surface" = meters below instantaneous water surface (positive down, 0=at surface); '
                                '"bottom" = meters above sea bed (positive up, 0=at bed).',
                        units='meters'),
            z_max = PVC(None, float, is_required=True,
                        doc_str='Top of 3D counting grid. Same sign convention as z_min, determined by vertical_range_measured_relative_to.',
                        units='meters'),
            vertical_range_measured_relative_to = PVC('surface', str,
                        doc_str='Vertical range is measured relative to the geoid (normal-null), the water surface, or the sea bed. '
                                'Options are "geoid", "surface", "bottom". '
                                '"geoid": z_min/z_max are depths from chart datum (z=0 at MSL, negative at depth); '
                                '"surface": z_min/z_max are depths below instantaneous water surface (0=at surface, positive down); '
                                '"bottom": z_min/z_max are heights above sea bed (0=at bed, positive up).',
                        possible_values=['geoid', 'surface', 'bottom']),
            vertical_range= PCC([0.0, 100.0], single_cord=True, is3D=True,
                                  doc_str='Use z_min and z_max to set boundaries of 3D grid',
                                  units='meters',obsolete=True),
            output_file_base=PVC('stats_gridded_time_3D', str, doc_str='start of output file names'),
            )
        self.remove_default_params(['near_seabed','near_seasurface'])

    def initial_setup(self):
        # set up regular grid for  stats
        super().initial_setup()
        info = self.info
        stats_grid = self.grid
        self._create_grid_variables()

        dm = si.dim_names
        info['count_dims']= {dm.time: None,
                            dm.release_group: len(si.class_roles.release_groups),
                            dm.grid_row_y: self.grid['x_grid'].shape[1],
                            dm.grid_col_x: self.grid['x_grid'].shape[2],
                            dm.z: stats_grid['z'].shape[1]}

        self.create_count_variables(info['count_dims'],'time')
        self.set_up_part_prop_lists()

    def set_z_range_for_counts(self):
        # set z range of 3D grid
        ml = si.msg_logger
        info = self.info
        params = self.params

        info['z_range'] = np.asarray([params['z_min'], params['z_max'] ])

        if info['z_range'][0] > info['z_range'][1]:
            ml.msg(f'Require zmin > zmax, (z_min,z_max) =({info["z_range"][0]:.3e}, {info["z_range"][1]:.3e}) ',
                   error=True, caller=self,
                   hint='z=0 is mean water level, so z is mostly < 0')

    def _create_grid_variables(self):
        # First set up x,y bins using parent method
        super()._create_grid_variables()

        # Then add z bins
        stats_grid = self.grid
        params = self.params

        # Set up vertical grid
        vsize = params['layers']
        base_z_bin_edges = np.linspace(params['z_min'], params['z_max'], vsize + 1)
        dz = float((params['z_max'] - params['z_min']) / vsize)

        # tile to per-release-group shape, consistent with x_bin_edges/y_bin_edges convention
        n_grids = stats_grid['x_bin_edges'].shape[0]
        stats_grid['z_bin_edges'] = np.tile(base_z_bin_edges[np.newaxis, :], (n_grids, 1))
        stats_grid['z'] = 0.5 * (stats_grid['z_bin_edges'][:, 1:] + stats_grid['z_bin_edges'][:, :-1])
        stats_grid['grid_spacings'] = np.append(stats_grid['grid_spacings'], dz)
        stats_grid['cell_volume'] = stats_grid['cell_area'] * dz

    def do_counts(self, n_time_step, time_sec, sel, alive):
        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid

        self.count_all_currently_alive(alive)

        p_groupID = part_prop['IDrelease_group'].data
        p_x = part_prop['x'].data
        mode = self.params['vertical_range_measured_relative_to']

        if mode == 'geoid':
            self.do_counts_and_summing_numba_geoid(
                p_groupID, p_x,
                stats_grid['x_bin_edges'], stats_grid['y_bin_edges'], stats_grid['z_bin_edges'],
                self.counts_inside_time_slice,
                self.prop_data_list, self.sum_prop_data_list, sel)

        elif mode == 'surface':
            p_depth = part_prop['tide'].data - p_x[:, 2]
            self.do_counts_and_summing_numba_surface(
                p_groupID, p_x, p_depth,
                stats_grid['x_bin_edges'], stats_grid['y_bin_edges'], stats_grid['z_bin_edges'],
                self.counts_inside_time_slice,
                self.prop_data_list, self.sum_prop_data_list, sel)

        elif mode == 'bottom':
            p_depth = part_prop['water_depth'].data
            self.do_counts_and_summing_numba_bottom(
                p_groupID, p_x, p_depth,
                stats_grid['x_bin_edges'], stats_grid['y_bin_edges'], stats_grid['z_bin_edges'],
                self.counts_inside_time_slice,
                self.prop_data_list, self.sum_prop_data_list, sel)

        else:
            raise ValueError('vertical_range_measured_relative_to must be "geoid", "surface", or "bottom"')

    @staticmethod
    @njitOT
    def do_counts_and_summing_numba_geoid(group_ID, x, x_edges, y_edges, z_edges, count,
                                          prop_list, sum_prop_list, sel):
        count[:] = 0
        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in sel:
            ng = group_ID[n]

            dx = x_edges[ng, 1] - x_edges[ng, 0]
            dy = y_edges[ng, 1] - y_edges[ng, 0]
            dz = z_edges[ng, 1] - z_edges[ng, 0]

            r = int(np.floor((x[n, 1] - y_edges[ng, 0]) / dy))
            c = int(np.floor((x[n, 0] - x_edges[ng, 0]) / dx))
            k = int(np.floor((-x[n, 2] - z_edges[ng, 0]) / dz))

            if (0 <= r < y_edges.shape[1] - 1 and
                    0 <= c < x_edges.shape[1] - 1 and
                    0 <= k < z_edges.shape[1] - 1):
                count[ng, r, c, k] += 1
                for m in range(len(prop_list)):
                    sum_prop_list[m][ng, r, c, k] += prop_list[m][n]

    @staticmethod
    @njitOT
    def do_counts_and_summing_numba_surface(group_ID, x, depth, x_edges, y_edges, z_edges, count,
                                            prop_list, sum_prop_list, sel):
        # depth = tide - x[:,2], i.e. distance below current water surface (positive down)
        count[:] = 0
        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in sel:
            ng = group_ID[n]

            dx = x_edges[ng, 1] - x_edges[ng, 0]
            dy = y_edges[ng, 1] - y_edges[ng, 0]
            dz = z_edges[ng, 1] - z_edges[ng, 0]

            r = int(np.floor((x[n, 1] - y_edges[ng, 0]) / dy))
            c = int(np.floor((x[n, 0] - x_edges[ng, 0]) / dx))
            k = int(np.floor((depth[n] - z_edges[ng, 0]) / dz))

            if (0 <= r < y_edges.shape[1] - 1 and
                    0 <= c < x_edges.shape[1] - 1 and
                    0 <= k < z_edges.shape[1] - 1):
                count[ng, r, c, k] += 1
                for m in range(len(prop_list)):
                    sum_prop_list[m][ng, r, c, k] += prop_list[m][n]

    @staticmethod
    @njitOT
    def do_counts_and_summing_numba_bottom(group_ID, x, depth, x_edges, y_edges, z_edges, count,
                                           prop_list, sum_prop_list, sel):
        # depth = water_depth - (-x[:,2]), i.e. height above sea bed (positive up)
        count[:] = 0
        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in sel:
            ng = group_ID[n]

            dx = x_edges[ng, 1] - x_edges[ng, 0]
            dy = y_edges[ng, 1] - y_edges[ng, 0]
            dz = z_edges[ng, 1] - z_edges[ng, 0]

            r = int(np.floor((x[n, 1] - y_edges[ng, 0]) / dy))
            c = int(np.floor((x[n, 0] - x_edges[ng, 0]) / dx))
            k = int(np.floor((depth[n] - z_edges[ng, 0]) / dz))

            if (0 <= r < y_edges.shape[1] - 1 and
                    0 <= c < x_edges.shape[1] - 1 and
                    0 <= k < z_edges.shape[1] - 1):
                count[ng, r, c, k] += 1
                for m in range(len(prop_list)):
                    sum_prop_list[m][ng, r, c, k] += prop_list[m][n]

    def info_to_write_on_file_close(self, nc):

        stats_grid = self.grid

        # Write x, y grid info using parent method
        super().info_to_write_on_file_close(nc)

        dim_names =  stats_util.get_dim_names(self.info['count_dims'])
        # Write z grid info
        nc.write_variable('z', stats_grid['z'], [dim_names[1], dim_names[4]], units='m', description='Mid point of vertical grid cell')

        # Write grid cell volume (shape: n_groups, n_y, n_x)
        nc.write_variable('grid_cell_volume', stats_grid['cell_volume'],
                          dim_names[1:4], units='m^3',
                          description='Volume of each 3D grid cell')

    def sel_depth_range(self, sel):
        # dummy depth range sel as 3D grid sets depth range
        return sel
