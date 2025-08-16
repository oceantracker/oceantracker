import numpy as np
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange


from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats

from oceantracker.shared_info import shared_info as si

stationary_status = int(si.particle_status_flags.stationary)  # compile this constant into numba code
from oceantracker.particle_statistics.util import  stats_util
class GriddedStats2D_timeBased(_BaseParticleLocationStats):
    # class to hold counts of particles inside grid squares

    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_grid_params()



    def initial_setup(self):
        # set up regular grid for  stats
        super().initial_setup()
        info = self.info
        self.create_grid_variables()
        dm = si.dim_names
        info['count_dims']= {dm.time: None,
                       dm.release_group:len(si.class_roles.release_groups),
                       dm.grid_row_y:  self.grid['x_grid'].shape[1],
                       dm.grid_col_x:  self.grid['x_grid'].shape[2]}

        self.create_count_variables(info['count_dims'],'time')
        self.set_up_part_prop_lists()


    def open_output_file(self, file_name):
        nc = super().open_output_file(file_name)
        self.nWrites = 0
        self.add_time_variables_to_file(nc)
        self.add_grid_variables_to_file(nc)

        # time grid count variables
        dims = self.info['count_dims']
        dim_names = [key for key in dims]
        nc.create_variable('count_all_selected_particles', dim_names[:2], np.int64,
                           compression_level=si.settings.NCDF_compression_level,
                           description='counts of all particles selected to be  within grid, eg by depth range etc wherethe inside grid or not')
        nc.create_variable('count_all_alive_particles', dim_names[:2], np.int64,
                           compression_level=si.settings.NCDF_compression_level,
                           description='counts of all alive particles everywhere')
        nc.create_variable('count',dims.keys(), np.int64, compression_level=si.settings.NCDF_compression_level,
                           description='counts of particles in spatial bins at given times, for each release group')
        for p in self.params['particle_property_list']:
            nc.create_variable('sum_' + p,list(dims.keys()), np.float64, description='sum of particle property inside bin')
        return nc

    def do_counts(self,n_time_step, time_sec, sel, alive):
        # do counts for each release  location and grid cell
        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid

        stats_util._count_all_alive_time(part_prop['status'].data, part_prop['IDrelease_group'].data,
                                         self.count_all_alive_particles, alive)

        # set up pointers to particle properties
        release_groupID = part_prop['IDrelease_group'].used_buffer()
        p_x= part_prop['x'].used_buffer()

        self._do_counts_and_summing_numba(release_groupID, p_x,
                                          stats_grid['x_bin_edges'], stats_grid['y_bin_edges'],
                                          stats_grid['grid_spacings'],
                                          self.count_time_slice, self.count_all_selected_particles_time_slice,
                                          self.prop_data_list, self.sum_prop_data_list, sel)
        pass

    @staticmethod
    @njitOT
    def _do_counts_and_summing_numba(group_ID, x, x_edges, y_edges,grid_spacings, count, count_all_particles, prop_list, sum_prop_list, sel):
        # for time based heatmaps zero counts for one time slice
        count[:]=0
        count_all_particles[:] = 0
        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.
        dx= grid_spacings[0]
        dy = grid_spacings
        for n in sel:

            ng = group_ID[n]
            count_all_particles[ng] += 1

            # assumes equal spacing
            r = int(np.floor((x[n, 1] - y_edges[ng,0]) / grid_spacings[1]))  # row is y, column x
            c = int(np.floor((x[n, 0] - x_edges[ng,0]) / grid_spacings[0]))

            if 0 <= r < y_edges.shape[1] - 1 and 0 <= c < x_edges.shape[1] - 1:
                count[ng, r, c] += 1
                # sum particle properties
                for m in range(len(prop_list)):
                    sum_prop_list[m][ng,r,c] += prop_list[m][n]

class GriddedStats2D_ageBased(_BaseParticleLocationStats):
    # does grid stats  based on age, but must keep whole stats grid in memory so ages can bw bined
    # bins all particles across all times into age bins,

    # NOTE: note to get unbiased stats, need to stop releasing particles 'max_age_to_bin' before end of run

    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_grid_params()
        self.add_age_params()

    def initial_setup(self):
        # set up regular grid for  stats
        super().initial_setup()
        info = self.info
        self.create_grid_variables()
        self.create_age_variables()
        dm = si.dim_names
        info['count_dims']= {dm.age: self.grid['age_bins'].size,
                            dm.release_group:len(si.class_roles.release_groups),
                            dm.grid_row_y: self.grid['x_grid'].shape[1],
                            dm.grid_col_x: self.grid['x_grid'].shape[2]}

        self.create_count_variables(info['count_dims'],'age')

        self.set_up_part_prop_lists()

    def open_output_file(self,file_name):
        self.nWrites = 0
        nc = super().open_output_file(file_name)
        self.add_grid_variables_to_file(nc)
        return nc

    def do_counts(self,n_time_step, time_sec, sel, alive):
        # do counts for each release  location and grid cell, overrides parent
        # set up pointers to particle properties
        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid
        release_groupID = part_prop['IDrelease_group'].used_buffer()
        stats_util._count_all_alive_age_bins(part_prop['status'].data,
                            part_prop['IDrelease_group'].data,
                            part_prop['age'].data,  stats_grid['age_bin_edges'],
                            self.count_all_alive_particles, alive)

        p_x = part_prop['x'].used_buffer()
        p_age = part_prop['age'].used_buffer()

        self._do_counts_and_summing_numba(release_groupID, p_x,
                        stats_grid['x_bin_edges'], stats_grid['y_bin_edges'],
                        stats_grid['grid_spacings'],
                        self.count_age_bins,
                         self.count_all_selected_particles,
                          self.prop_data_list, self.sum_prop_data_list,
                          stats_grid['age_bin_edges'], p_age, sel)

    @staticmethod
    @njitOT
    def _do_counts_and_summing_numba(group_ID, x, x_edges, y_edges,grid_spacings, count, count_all_particles, prop_list, sum_prop_list,
                                     age_bin_edges, age, sel):
        # (no zeroing as accumulated over  whole run)
        da = age_bin_edges[1] - age_bin_edges[0]

        for n in sel:
            ng = group_ID[n]

            #grids may have release group centers , so coods differ by release group
            r = int(np.floor((x[n, 1] - y_edges[ng, 0]) / grid_spacings[1]))  # row is y, column x
            c = int(np.floor((x[n, 0] - x_edges[ng, 0]) / grid_spacings[0]))
            na = int(np.floor((age[n] - age_bin_edges[0]) / da))

            if 0 <= na < (age_bin_edges.size - 1):
                count_all_particles[na, ng] += 1 # count all in each age band
                if 0 <= r < y_edges.shape[1] - 1 and 0 <= c < x_edges.shape[1] - 1 :
                    count[na, ng, r, c] += 1
                    # sum particle properties
                    for m in range(len(prop_list)):
                        sum_prop_list[m][na, ng, r, c] += prop_list[m][n]

    def write_time_varying_stats(self, time_sec):
        pass # no writing on the fly in aged based states

    def info_to_write_at_end(self):
        # only write age count variables as whole at end of run

        nc = self.nc
        stats_grid = self.grid
        dim_names = [key for key in self.info['count_dims']]
        nc.write_variable('count', self.count_age_bins, dim_names,
                          description= 'counts of particles in grid at given ages, for each release group')
        nc.write_variable('count_all_selected_particles', self.count_all_selected_particles,
                          dim_names[:2],
                          description='counts of all particles selected to be counted in age bands for each release group ( eg selected by z range)')
        nc.write_variable('count_all_alive_particles', self.count_all_alive_particles,
                          dim_names[:2],
                          description='counts of all particles alive from each release group, into age bins')
        nc.write_variable('age_bins', stats_grid['age_bins'], ['age_bin_dim'], description='center of age bin, ie age axis of heat map in seconds')
        nc.write_variable('age_bin_edges', stats_grid['age_bin_edges'], ['age_bin_edges'], description='center of age bin, ie age axis of heat map in seconds')
        # particle property sums
        dims = ('age_bin_dim', 'release_group_dim', 'y_dim', 'x_dim')
        for key, item in self.sum_binned_part_prop.items():
            # need to write final sums of properties  after all age counts done across all times
            nc.write_variable('sum_' + key, item[:], dims, description='sum of particle property inside grid bins  ' + key)

