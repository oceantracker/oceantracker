
import numpy as np
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange
from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.shared_info import shared_info as si
from oceantracker.particle_statistics.gridded_statistics2D import GriddedStats2D_timeBased
from oceantracker.particle_statistics.util import stats_util

class GriddedStats3D_timeBased(GriddedStats2D_timeBased):
    # class to hold counts of particles inside 3D grid cells
    '''
    Counts particles into 3D regular grid at given interval. Extends 2D grid version.
    '''
    def __init__(self):
        # set up info/attributes
        super().__init__()
        # add 3D specific parameters
        self.add_default_params(
            grid_size= PLC([101, 99,5], int, fixed_len=3, min=1, max=10 ** 5,
                             doc_str='number of (rows, columns, layers) in grid, where rows is y size, cols x size, values should be odd, so will be rounded up to next '),
            z_min = PVC(None, float, doc_str='Bottom of 3D counting grid', is_required=True,
                        units='meters above mean water at  z=0, so is < 0 at depth'),
            z_max = PVC(None, float, doc_str='Top of 3D counting grid',is_required=True,
                    units='meters above mean water level at z=0 , so is < 0 at depth'),

            vertical_range= PCC([0.0, 100.0], single_cord=True, is3D=True,
                                  doc_str='Use z_min and z_max to set boundaries of 3D grid',
                                  units='meters',obsolete=True),
            role_output_file_tag= PVC('stats_gridded_time3D', str),
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
                            dm.release_group:len(si.class_roles.release_groups),
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
        # Make vertical bin edges
        vsize = params['grid_size'][2]
        stats_grid['z_bin_edges'] = np.linspace(params['z_min'], params['z_max'], vsize + 1)
        dz = float((params['z_max']- params['z_min'] ) / vsize)

        # Make vertical bin centers
        stats_grid['z'] = 0.5 * (stats_grid['z_bin_edges'][1:] + stats_grid['z_bin_edges'][:-1])
        stats_grid['grid_spacings'] = np.append(stats_grid['grid_spacings'],dz)
        stats_grid['cell_volume'] = stats_grid['cell_area'] * dz

    def do_counts(self, n_time_step, time_sec, sel, alive):
        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid

        stats_util._count_all_alive_time(part_prop['status'].data,
                                         part_prop['IDrelease_group'].data,
                                         self.count_all_alive_particles, alive)
        self._do_counts_and_summing_numba(
                            part_prop['IDrelease_group'].data,
                            part_prop['x'].data,
                            stats_grid['x_bin_edges'],
                            stats_grid['y_bin_edges'],
                            stats_grid['z_bin_edges'],
                            stats_grid['grid_spacings'],
                            self.counts_inside_time_slice,
                            self.prop_data_list,
                            self.sum_prop_data_list,
                            sel)

    @staticmethod
    @njitOT
    def _do_counts_and_summing_numba(group_ID, x, x_edges, y_edges, z_edges,
                                     grid_spacings, count,
                                     prop_list, sum_prop_list, sel):
        # Zero counts for this time slice
        count[:] = 0

        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in sel:
            ng = group_ID[n]

            # assumes equal spacing, in meters or deg. if geographic
            # Calculate grid indices
            r = int(np.floor((x[n, 1] - y_edges[ng, 0]) / grid_spacings[1]))  # row is y
            c = int(np.floor((x[n, 0] - x_edges[ng, 0]) / grid_spacings[0]))  # column is x
            k = int(np.floor((x[n, 2] - z_edges[0]) / grid_spacings[2]))  # k is z

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
    def sel_depth_range(self, sel) :
        # dummy depth range sel as 3D grid sets depth range
        return sel