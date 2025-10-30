import numpy as np
from datetime import datetime
from os import path
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange
from oceantracker.util.ncdf_util import NetCDFhandler

from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats

from oceantracker.shared_info import shared_info as si

stationary_status = int(si.particle_status_flags.stationary)  # compile this constant into numba code
from oceantracker.particle_statistics.util import  stats_util
from oceantracker.particle_statistics._base_stats_variants import  _BaseAgeStats



class GriddedStats2D_timeBased(_BaseParticleLocationStats):
    # class to hold counts of particles inside grid squares
    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self._add_grid_params()
    
    def initial_setup(self):
        # set up regular grid for stats
        super().initial_setup()
        info = self.info
        params = self.params
        ml = si.msg_logger
        
        self._create_grid_variables()
        dm = si.dim_names
        info['count_dims']= {dm.time: None,
                       dm.release_group:len(si.class_roles.release_groups),
                       dm.grid_row_y:  self.grid['x_grid'].shape[1],
                       dm.grid_col_x:  self.grid['x_grid'].shape[2]}

        self.create_count_variables(info['count_dims'],'time')
        self.set_up_part_prop_lists()

    def update(self, n_time_step, time_sec, alive):
        '''Do particle counts'''
        part_prop = si.class_roles.particle_properties
        info = self.info
        params = self.params
        
        num_in_buffer = si.run_info.particles_in_buffer

        # Select particles to count based on status and z location
        sel = stats_util._sel_status_waterdepth(part_prop['status'].data,
                                    part_prop['x'].data, part_prop['water_depth'].data.ravel(),
                                    self.statuses_to_count_map, info['water_depth_range'],
                                    num_in_buffer, self.get_partID_buffer('B1'))

        if si.run_info.is3D_run:
            sel = self.sel_depth_range(sel)
        
        # Users override this method to further sub-select those to count
        sel = self.select_particles_to_count(sel)

        # Update prop list data, as buffer may have expanded
        for n, name in enumerate(self.sum_binned_part_prop.keys()):
            self.prop_data_list[n] = part_prop[name].data

        # Perform the counts
        self.do_counts(n_time_step, time_sec, sel, alive)
        
        self.write_time_varying_stats(time_sec)
        self.nWrites += 1

    def write_time_varying_stats(self, time_sec):
        self._write_common_time_varying_stats(time_sec)

    def open_output_file(self, file_name):
        nc = super().open_output_file(file_name)
        self.add_time_variables_to_file(nc)
        self.add_grid_variables_to_file(nc)
        self._create_common_time_varying_stats(nc)
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
                                          self.count_time_slice,
                                          self.prop_data_list, self.sum_prop_data_list, sel)

    @staticmethod
    @njitOT
    def _do_counts_and_summing_numba(group_ID, x, x_edges, y_edges,grid_spacings, count,
                                     prop_list, sum_prop_list, sel):
        # for time based heatmaps zero counts for one time slice
        count[:]=0

        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in sel:

            ng = group_ID[n]

            # assumes equal spacing
            r = int(np.floor((x[n, 1] - y_edges[ng,0]) / grid_spacings[1]))  # row is y, column x
            c = int(np.floor((x[n, 0] - x_edges[ng,0]) / grid_spacings[0]))

            if 0 <= r < y_edges.shape[1] - 1 and 0 <= c < x_edges.shape[1] - 1:
                count[ng, r, c] += 1
                # sum particle properties
                for m in range(len(prop_list)):
                    sum_prop_list[m][ng,r,c] += prop_list[m][n]


class GriddedStats2D_timeBased_runningMean(GriddedStats2D_timeBased):
    def __init__(self):
        super().__init__()
        # Add write_interval parameter for running mean functionality
        self.add_default_params({
            'write_interval': PVC(None, float, units='sec',
                                 doc_str='Time in seconds between writing averaged statistics to disk. '
                                        'If set and greater than update_interval, enables running mean calculation. '
                                        'Statistics are computed at update_interval frequency but averaged over write_interval before writing. '
                                        'Must be greater than update_interval to enable averaging.')
        })

    def initial_setup(self):
        super().initial_setup()
        self._initialize_running_mean()
    
    def update(self, n_time_step, time_sec, alive):
        '''Do particle counts with running mean support'''
        part_prop = si.class_roles.particle_properties
        info = self.info
        params = self.params
        
        num_in_buffer = si.run_info.particles_in_buffer

        # Select particles to count based on status and z location
        sel = stats_util._sel_status_waterdepth(part_prop['status'].data,
                                    part_prop['x'].data, part_prop['water_depth'].data.ravel(),
                                    self.statuses_to_count_map, info['water_depth_range'],
                                    num_in_buffer, self.get_partID_buffer('B1'))

        if si.run_info.is3D_run:
            sel = self.sel_depth_range(sel)
        
        # Users override this method to further sub-select those to count
        sel = self.select_particles_to_count(sel)

        # Update prop list data, as buffer may have expanded
        for n, name in enumerate(self.sum_binned_part_prop.keys()):
            self.prop_data_list[n] = part_prop[name].data

        # Perform the counts
        self.do_counts(n_time_step, time_sec, sel, alive)
        
        # Handle writing based on running mean configuration
        self._accumulate_for_running_mean()
        
        # Check if it's time to write averaged values
        if self.schedulers['write_scheduler'].do_task(n_time_step):
            self._write_averaged_stats(time_sec)
            self._reset_running_mean_accumulators()

    def _initialize_buffer_variables_for_running_mean(self):
            params = self.params
            
            # Enable running mean
            self.use_running_mean = True
        
            # Initialize running mean tracking variables
            self.running_count_sum = None
            self.running_alive_sum = None
            self.running_prop_sums = {}
            self.n_updates_in_interval = 0
            
            # Initialize accumulator arrays for running mean
            self.running_count_sum = np.zeros_like(self.count_time_slice, dtype=np.float64)
            self.running_alive_sum = np.zeros_like(self.count_all_alive_particles, dtype=np.float64)

            # Initialize property accumulator arrays
            if 'particle_property_list' in params and params['particle_property_list']:
                for key, prop in self.sum_binned_part_prop.items():
                    self.running_prop_sums[key] = self.sum_binned_part_prop[key].copy()
    
    def _initialize_running_mean(self):
        params = self.params
        ml = si.msg_logger
        
        # Validate that write_interval is greater than update_interval
        if params['write_interval'] <= params['update_interval']:
            ml.msg(f'Parameter "write_interval" ({params["write_interval"]}s) must be greater than '
                    f'"update_interval" ({params["update_interval"]}s) to enable averaging',
                    hint='Set write_interval > update_interval for running mean, or set write_interval=None for standard behavior',
                    error=True, caller=self,
                    crumbs=f'Particle Statistic "{params["name"]}"')
            return
        
        # Check if write_interval is a multiple of update_interval
        ratio = params['write_interval'] / params['update_interval']
        if abs(ratio - round(ratio)) > 1e-6:  # Not a clean multiple
            ml.msg(f'Parameter "write_interval" ({params["write_interval"]}s) is not a multiple of '
                    f'"update_interval" ({params["update_interval"]}s)',
                    hint=f'Consider using write_interval = {round(ratio) * params["update_interval"]}s for cleaner averaging',
                    warning=True, caller=self,
                    crumbs=f'Particle Statistic "{params["name"]}"')
        
        self._initialize_buffer_variables_for_running_mean()
        
        # Set up write scheduler different from update interval
        self.add_scheduler('write_scheduler', 
                            start=params['start'], 
                            end=params['end'], 
                            duration=params['duration'],
                            interval=params['write_interval'], 
                            caller=self)
            
        ml.msg(f'Running mean enabled: updating every {params["update_interval"]}s, '
                f'writing averaged values every {params["write_interval"]}s',
                hint='Statistics will be averaged over write_interval before writing',
                crumbs=f'Particle Statistic "{params["name"]}"')

    def _accumulate_for_running_mean(self):
        """Accumulate current counts for running mean calculation"""
        # Add current counts to running sum
        self.running_count_sum += self.count_time_slice.astype(np.float64)
        self.running_alive_sum += self.count_all_alive_particles.astype(np.float64)
        
        # Accumulate property sums
        for name, prop_sum in self.sum_binned_part_prop.items():
            self.running_prop_sums[name] += prop_sum
        
        self.n_updates_in_interval += 1

    def _write_averaged_stats(self, time_sec):
        """Write time-averaged statistics"""
        if self.n_updates_in_interval == 0:
            return
        elif int(self.params['write_interval']/self.params['update_interval']) > self.n_updates_in_interval:
            # In the current implementatin of the solver it updates once just after the release
            # before any particles have been moved.
            # We could design the scheduler to avoid this,
            # but this method clears this data out of the avg stack 
            # which I (Laurin) think is more intuitive to the user.
            return
        
        # Calculate averages
        avg_count = self.running_count_sum / self.n_updates_in_interval
        avg_alive = self.running_alive_sum / self.n_updates_in_interval
        
        # And replace the non-running-average data to write it with the existing method
        self.count_time_slice = avg_count
        self.count_all_alive_particles = avg_alive

        # Average property sums
        for name in self.running_prop_sums:
            if name in self.sum_binned_part_prop:
                self.sum_binned_part_prop[name] = self.running_prop_sums[name] / self.n_updates_in_interval
        
        # Write the averaged values
        self._write_common_time_varying_stats(time_sec)
        self.nWrites += 1
        
        # Reset running mean accumulators arrays
        self._reset_running_mean_accumulators()

    def _reset_running_mean_accumulators(self):
        """Reset running mean accumulator arrays"""
        self.running_count_sum.fill(0)
        self.running_alive_sum.fill(0)
        for prop_sum in self.running_prop_sums.values():
            prop_sum.fill(0)
        self.n_updates_in_interval = 0

    # def open_output_file(self, file_name):
    #     nc = super().open_output_file(file_name)
    #     # Add metadata about running mean if enabled
    #     nc.create_attribute('statistics_type', 'running_mean')
    #     nc.create_attribute('update_interval', self.params['update_interval'])
    #     nc.create_attribute('write_interval', self.params['write_interval'])


class GriddedStats2D_ageBased(_BaseAgeStats, _BaseParticleLocationStats):

    # does grid stats  based on age, but must keep whole stats grid in memory so ages can bw bined
    # bins all particles across all times into age bins,

    # NOTE: note to get unbiased stats, need to stop releasing particles 'max_age_to_bin' before end of run

    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params(
            role_output_file_tag= PVC('stats_gridded_age', str),)

        self._add_grid_params()
        self._add_age_params()

    def initial_setup(self):
        # set up regular grid for  stats
        super().initial_setup()
        info = self.info
        self._create_grid_variables()
        self._create_age_variables()
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

        # debug code
        if False:
            gridIDa=  part_prop['hydro_model_gridID'].get_values(alive)
            gridIDs = part_prop['hydro_model_gridID'].get_values(sel)
            print('xx heatmap/grid counts, numbers on each grid ID, alive', np.sum(gridIDa==0),  np.sum(gridIDa==1),
                  'selected to count', np.sum(gridIDs==0),  np.sum(gridIDs==1) )


        self._do_counts_and_summing_numba(release_groupID, p_x,
                        stats_grid['x_bin_edges'], stats_grid['y_bin_edges'],
                        stats_grid['grid_spacings'],
                        self.count_age_bins,
                        self.prop_data_list, self.sum_prop_data_list,
                        stats_grid['age_bin_edges'], p_age, sel)

    @staticmethod
    @njitOT
    def _do_counts_and_summing_numba(group_ID, x, x_edges, y_edges,grid_spacings, count,
                                     prop_list, sum_prop_list,
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
                if 0 <= r < y_edges.shape[1] - 1 and 0 <= c < x_edges.shape[1] - 1 :
                    count[na, ng, r, c] += 1
                    # sum particle properties
                    for m in range(len(prop_list)):
                        sum_prop_list[m][na, ng, r, c] += prop_list[m][n]

    def write_time_varying_stats(self, time_sec):
        pass # no writing on the fly in aged based states

    def info_to_write_on_file_close(self, nc):
        # only write age count variables as whole at end of run
        stats_grid = self.grid
        dim_names =  stats_util.get_dim_names(self.info['count_dims'])
        nc.write_variable('count', self.count_age_bins, dim_names,
                          description= 'counts of particles in grid at given ages, for each release group')
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

        # to do:
        # * add metadata about running mean if enabled
        # if self.use_running_mean:
        #     nc.create_attribute('statistics_type', 'running_mean')
        #     nc.create_attribute('update_interval', self.params['update_interval'])
        #     nc.create_attribute('write_interval', self.params['write_interval'])

