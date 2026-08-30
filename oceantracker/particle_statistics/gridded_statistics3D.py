
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
    Vertical bins can be fixed in z (relative to the geoid), or follow the instantaneous
    water surface or the sea bed, set by param "vertical_range_measured_relative_to".
    '''
    def __init__(self):
        # set up info/attributes
        super().__init__()
        regular_grid_util.add_grid_default_params(self.default_params,is3D=True, grid_center_required=False)

        # add 3D specific parameters
        self.add_default_params(
            z_min = PVC(None, float, is_required=True,
                        doc_str='Bottom of 3D counting grid. Interpretation depends on vertical_range_measured_relative_to: '
                                '"geoid" = meters above mean water level at z=0, so is < 0 at depth; '
                                '"surface" = meters below instantaneous water surface (positive down, 0=at surface); '
                                '"bottom" = meters above sea bed (positive up, 0=at bed).',
                        units='meters'),
            z_max = PVC(None, float, is_required=True,
                        doc_str='Top of 3D counting grid. Same sign convention as z_min, determined by vertical_range_measured_relative_to.',
                        units='meters'),
            vertical_range_measured_relative_to = PVC('geoid', str,
                        doc_str='Vertical range is measured relative to the geoid (mean water level), the water surface, or the sea bed. '
                                '"geoid": z_min/z_max are fixed z values (z=0 at mean water level, negative at depth); '
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
                            dm.z: stats_grid['z'].size}

        self.create_count_variables(info['count_dims'],'time')
        self.set_up_part_prop_lists()

    def set_z_range_for_counts(self):
        # set z range of 3D grid
        ml = si.msg_logger
        info = self.info
        params = self.params
        mode = params['vertical_range_measured_relative_to']

        info['z_range'] = np.asarray([params['z_min'], params['z_max'] ])

        if info['z_range'][0] > info['z_range'][1]:
            hint = 'z=0 is mean water level, so z is mostly < 0' if mode == 'geoid' else \
                   f'with vertical_range_measured_relative_to="{mode}", z_min/z_max are distances from the {"surface" if mode == "surface" else "sea bed"}, so are >= 0'
            ml.msg(f'Require z_min < z_max, (z_min,z_max) =({info["z_range"][0]:.3e}, {info["z_range"][1]:.3e}) ',
                   error=True, caller=self, hint=hint)

        if mode != 'geoid' and info['z_range'][0] < 0:
            ml.msg(f'Require z_min >= 0 when vertical_range_measured_relative_to="{mode}", got z_min={info["z_range"][0]:.3e}',
                   error=True, caller=self,
                   hint=f'z_min/z_max are distances from the {"water surface, positive down" if mode == "surface" else "sea bed, positive up"}')

    def _create_grid_variables(self):
        # First set up x,y bins using parent method
        super()._create_grid_variables()

        # Then add z bins
        stats_grid = self.grid
        params = self.params

        # Set up vertical grid, one z grid shared by all release groups
        vsize = params['layers']
        stats_grid['z_bin_edges'] = np.linspace(params['z_min'], params['z_max'], vsize + 1)
        dz = float((params['z_max'] - params['z_min']) / vsize)

        # Make vertical bin centers
        stats_grid['z'] = 0.5 * (stats_grid['z_bin_edges'][1:] + stats_grid['z_bin_edges'][:-1])
        stats_grid['grid_spacings'] = np.append(stats_grid['grid_spacings'], dz)
        stats_grid['cell_volume'] = stats_grid['cell_area'] * dz

    def do_counts(self, n_time_step, time_sec, sel, alive):
        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid

        self.count_all_currently_alive(alive)

        x = part_prop['x'].data
        mode = self.params['vertical_range_measured_relative_to']
        if mode == 'geoid':
            z_rel = x[:, 2]                                             # m above mean water level, negative at depth
        elif mode == 'surface':
            z_rel = part_prop['tide'].data.ravel() - x[:, 2]            # m below instantaneous surface, positive down
        else:  # 'bottom'
            z_rel = part_prop['water_depth'].data.ravel() + x[:, 2]     # m above sea bed, positive up

        self._do_counts_and_summing_numba(
                            part_prop['IDrelease_group'].data,
                            x, z_rel,
                            stats_grid['x_bin_edges'],
                            stats_grid['y_bin_edges'],
                            stats_grid['z_bin_edges'],
                            self.counts_inside_time_slice,
                            self.prop_data_list,
                            self.sum_prop_data_list,
                            sel)

    @staticmethod
    @njitOT
    def _do_counts_and_summing_numba(group_ID, x, z_rel, x_edges, y_edges, z_edges,
                                     count, prop_list, sum_prop_list, sel):
        # z_rel is the vertical coordinate in the same reference frame as z_edges
        # Zero counts for this time slice
        count[:] = 0

        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in sel:
            ng = group_ID[n]

            # assumes equal spacing, in meters or deg. if geographic
            dx = x_edges[ng, 1] - x_edges[ng, 0]
            dy = y_edges[ng, 1] - y_edges[ng, 0]
            dz = z_edges[1] - z_edges[0]

            # Calculate grid indices
            r = int(np.floor((x[n, 1] - y_edges[ng, 0]) / dy))  # row is y
            c = int(np.floor((x[n, 0] - x_edges[ng, 0]) / dx))  # column is x
            k = int(np.floor((z_rel[n] - z_edges[0]) / dz))  # k is z

            # Check if particle is inside grid bounds
            if (0 <= r < y_edges.shape[1] - 1 and
                0 <= c < x_edges.shape[1] - 1 and
                0 <= k < z_edges.shape[0] - 1):

                count[ng, r, c, k] += 1
                # Sum particle properties
                for m in range(len(prop_list)):
                    sum_prop_list[m][ng, r, c, k] += prop_list[m][n]

    def info_to_write_on_file_close(self, nc):

        stats_grid = self.grid

        # Write x, y grid info using parent method
        super().info_to_write_on_file_close(nc)

        dim_names =  stats_util.get_dim_names(self.info['count_dims'])
        # Write z grid info
        nc.write_variable('z', stats_grid['z'], [dim_names[4]], units='m', description='Mid point of vertical grid cell')

        # Write grid cell volume
        nc.write_variable('grid_cell_volume', stats_grid['cell_volume'],
                          dim_names[1:4],units='m^3',
                          description='Volume of each 3D grid cell')

    def sel_depth_range(self, sel):
        # dummy depth range sel as 3D grid sets depth range
        return sel
