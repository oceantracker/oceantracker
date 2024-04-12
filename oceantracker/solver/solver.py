from time import perf_counter

import numpy as np
from oceantracker.util import time_util
from datetime import datetime
from oceantracker.particle_properties.util import particle_operations_util
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.solver.util import solver_util
from oceantracker.util import numpy_util


from oceantracker.shared_info import SharedInfo as si

class Solver(ParameterBaseClass):
    ''' Does particle tracking solution '''

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params({
                        'RK_order':                   PVC(4, int, possible_values=[1, 2, 4]),
                        'n_sub_steps': PVC(None, int, obsolete=True,  doc_str ='use shared_parameter "time_step", run may not have required time step'),
                        'screen_output_step_count': PVC(None, int, obsolete=True,  doc_str='use shared_parameter "screen_output_time_interval" in seconds')
                            })

    def final_setup(self):
        si.core_roles.particle_group_manager.add_particle_property('v_temp','manual_update', dict( vector_dim=si.roles.particle_properties['x'].num_vector_dimensions(), write=False))



    def check_requirements(self):
        self.check_class_required_fields_prop_etc( required_props_list=['x','status', 'x_last_good', 'particle_velocity', 'v_temp'])


    #@profile
    def solve(self):
        # solve for data in buffer
        ri=si.run_info
        ml = si.msg_logger
        part_prop = si.roles.particle_properties

        computation_started = datetime.now()
        # set up particle velocity working space for solver
        ri.total_alive_particles = 0

        pgm, fgm = si.core_roles.particle_group_manager, si.core_roles.field_group_manager
        ri.time_steps_completed = 0

        # work out time steps between writing tracks to screen
        write_tracks_time_step = si.settings['screen_output_time_interval']
        if write_tracks_time_step is None:
            nt_write_time_step_to_screen = 1
        else:
            nt_write_time_step_to_screen = max(1,int(write_tracks_time_step/si.settings.time_step))

        t0_model = perf_counter()
        ri.free_wheeling = False
        model_times = si.run_info.times
        fgm.update_reader(model_times[0]) # initial buffer fill

        # run forwards through model time variable, which for backtracking are backwards in time
        t2 = model_times[0]

        for n_time_step  in range(model_times.size-1): # one less step as last step is initial condition for next block
            t0_step = perf_counter()
            self.start_update_timer()
            time_sec = model_times[n_time_step]

            # release particles
            new_particleIDs  = pgm.release_particles(n_time_step, time_sec)

            # count particles of each status and count number >= stationary status
            num_alive = pgm.status_counts_and_kill_old_particles(time_sec)
            if num_alive == 0:
                #freewheel until more are released or end of run/hindcast
                if not ri.free_wheeling:
                    # at start note
                    ml.msg(f'No particles alive at {time_util.seconds_to_pretty_str(time_sec)}, skipping time steps until more are released', note=True)
                ri.free_wheeling = True
                continue

            ri.free_wheeling = False # has ended

           # alive particles so do steps
            ri.total_alive_particles += num_alive
            fgm.update_reader(time_sec)


            # do stats etc updates and write tracks
            self._pre_step_bookkeeping(n_time_step, time_sec, new_particleIDs)

            # now modfy location after writing of moving particles
            # do integration step only for moving particles should this only be moving particles, with vel modifications and random walk
            is_moving = part_prop['status'].compare_all_to_a_value('eq', si.particle_status_flags.moving, out=self.get_partID_buffer('ID1'))

            # update particle velocity modification
            part_prop['velocity_modifier'].set_values(0., is_moving)  # zero out  modifier, to add in current values
            for name, i in si.roles.velocity_modifiers.items():
                i.start_update_timer()
                i.update(n_time_step, time_sec, is_moving)
                i.stop_update_timer()

            # dispersion is done by random walk velocity modification prior to integration step
            if si.settings['include_dispersion']:
                i = si.core_roles.dispersion
                i.start_update_timer()
                i.update(n_time_step, time_sec, is_moving)
                i.stop_update_timer()

            #  Main integration step
            #--------------------------------------
            self.do_time_step(time_sec, is_moving)
            #--------------------------------------

            # print progress to screen
            if n_time_step % nt_write_time_step_to_screen == 0:
                self.screen_output(ri.time_steps_completed, time_sec, t0_model, t0_step)

            t2 = time_sec + si.settings.time_step * ri.model_direction

            # at this point interp is not set up for current positions, this is done in pre_step_bookeeping, and after last step
            ri.time_steps_completed += 1
            si.block_timer('Time stepping',t0_step)
            self.stop_update_timer()
            if abs(t2 - ri.start_time) > ri.duration: break


        # write out props etc at last step
        if n_time_step > 0: # if more than on set completed
            self._pre_step_bookkeeping(ri.time_steps_completed, t2) # update and record stuff from last step
            self.screen_output(ri.time_steps_completed, t2, t0_model,t0_step)

        ri.end_time = t2
        ri.model_end_date = t2.astype('datetime64[s]')
        ri.model_run_duration =  ri.end_time - ri.start_time
        ri.computation_started = computation_started
        ri.computation_ended = datetime.now()
        ri.computation_duration = datetime.now() -computation_started

    def _pre_step_bookkeeping(self, n_time_step,time_sec, new_particleIDs=np.full((0,),0,dtype=np.int32)):
        part_prop = si.roles.particle_properties
        pgm = si.core_roles.particle_group_manager
        fgm = si.core_roles.field_group_manager

        ri = si.run_info
        ri.current_model_date = time_util.seconds_to_datetime64(time_sec)
        ri.current_model_time_step = n_time_step
        ri.current_model_time = time_sec

        pgm.remove_dead_particles_from_memory()

        # some may now have status dead so update
        alive = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags.stationary, out=self.get_partID_buffer('ID1'))

        # trajectory modifiers,
        for name, i in si.roles.trajectory_modifiers.items():
            i.update(n_time_step, time_sec, alive)

        # modify status, eg tidal stranding
        fgm.update_dry_cell_index()


        alive = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags.stationary, out=self.get_partID_buffer('ID1'))

        # setup_interp_time_step, cell etc
        fgm.setup_time_step(time_sec, part_prop['x'].data, alive)

        # resuspension is a core trajectory modifier
        if si.run_info.is3D_run:
            # friction_velocity property  is now updated, so do resupension
            si.core_roles.resuspension.update(n_time_step,time_sec, alive)

        fgm.update_tidal_stranding_status(time_sec, alive)

        # update particle properties
        pgm.update_PartProp(n_time_step, time_sec, alive)

        # update writable class lists and stats at current time step now props are up to date
        self._update_stats(n_time_step, time_sec)
        self._update_concentrations(n_time_step, time_sec)
        self._update_events(n_time_step, time_sec)

        # update integrated models, eg LCS
        if si.core_roles.integrated_model is not None :
            si.core_roles.integrated_model.update(n_time_step,time_sec)

        # write tracks
        if si.settings.write_tracks:
            tracks_writer = si.core_roles.tracks_writer
            tracks_writer.open_file_if_needed()
            if new_particleIDs.size > 0:
                tracks_writer.write_all_non_time_varing_part_properties(new_particleIDs)  # these must be written on release, to work in compact mode

            # write tracks file
            pass
            if tracks_writer.write_scheduler.do_task(n_time_step):
                tracks_writer.write_all_time_varying_prop_and_data()


    def do_time_step(self, time_sec, is_moving):

        fgm = si.core_roles.field_group_manager
        part_prop = si.roles.particle_properties

        part_prop['x_last_good'].copy('x', is_moving)
        part_prop['n_cell_last_good'].copy('n_cell', is_moving)
        part_prop['cell_search_status'].set_values(si.cell_search_status_flags['ok'], is_moving)

        # do time step
        dt = si.settings.time_step*si.run_info.model_direction
        self.RK_step(time_sec, dt,is_moving)

        # for failed walks try half step
        bad = part_prop['cell_search_status'].find_subset_where(is_moving, 'lt', si.cell_search_status_flags['ok'], out=self.get_partID_subset_buffer('bad_walk'))
        if bad.size> 0:
            self.RK_step(time_sec, dt/2.0, bad)
            #bad2 = part_prop['cell_search_status'].find_subset_where(is_moving, 'lt', si.cell_search_status_flags['ok'])
            pass

        # fix any still bad
        fgm.fix_time_step(is_moving) # fix and particles bloched by boundiues etc


        # check bc coords correct
        if si.settings['dev_debug_opt'] ==10:
            from oceantracker.util import debug_util
            still_bad = debug_util.check_walk_step(si.core_roles.reader.grid, part_prop, bad, msg_logger=si.msg_logger, crumbs='solver-post RK step')

            if still_bad.size > 0:
                si.msg_logger.msg(f'Cell search,  some still bad after fixing step  {np.count_nonzero(still_bad)} of  {is_moving.size} ', warning=True)
                if si.settings['debug_plots']:
                    debug_util.plot_walk_step(part_prop['x'].data, si.core_roles.reader.grid, part_prop, still_bad)
                pass
        pass

    def RK_step(self,time_sec, dt, is_moving):
        # single step in particle tracking, t is time in seconds, is_moving are indcies of moving particles
        # this is done inplace directly operation on the particle properties
        # nb is buffer offset

        RK_order =self.params['RK_order']
        fgm = si.core_roles.field_group_manager
        part_prop =  si.roles.particle_properties

        # note here subStep_time_step has sign of forwards/backwards
        dt2 = dt/2.
        # set up views of  working variable space
        x1 = part_prop['x_last_good'].data
        x2 = part_prop['x'].data
        v       = part_prop['particle_velocity'].data
        v_temp  = part_prop['v_temp'].data  # temp vel from interp at each RK substeps
        velocity_modifier= part_prop['velocity_modifier'].data


        #  step 1 from current location and time
        fgm.setup_time_step(time_sec, x1, is_moving, fix_bad=False)

        if RK_order==1:
            fgm.interp_field_at_particle_locations('water_velocity', is_moving, output=v)
            solver_util.euler_substep( x1, v, velocity_modifier, dt, is_moving, x2)
            return

        # do first half step location from RK1 to update values
        fgm.interp_field_at_particle_locations('water_velocity', is_moving, output=v_temp)

        solver_util.euler_substep( x1, v_temp, velocity_modifier, dt2, is_moving, x2)
        particle_operations_util.copy(v, v_temp, is_moving, scale=1.0 / 6.0)   # accumulate RK velocity to reduce space taken by temporary working variables

        # step 2, get improved half step velocity
        t2= time_sec + 0.5 * dt
        fgm.setup_time_step(t2, x2, is_moving, fix_bad=False)

        if RK_order==2:
            fgm.interp_field_at_particle_locations('water_velocity', is_moving, output=v)
            solver_util.euler_substep( x1, v, velocity_modifier, dt, is_moving, x2)
            return

        fgm.interp_field_at_particle_locations('water_velocity', is_moving, output=v_temp)
        solver_util.euler_substep( x1, v_temp, velocity_modifier, dt2, is_moving, x2)
        particle_operations_util.add_to(v, v_temp, is_moving, scale=2.0 / 6.0)  # next accumulation of velocity step 2



        # step 3, a second half step
        t2 = time_sec + 0.5 * dt
        fgm.setup_time_step(t2, x2, is_moving, fix_bad=False)
        fgm.interp_field_at_particle_locations('water_velocity', is_moving, output=v_temp)
        solver_util.euler_substep( x1, v_temp, velocity_modifier, dt, is_moving, x2)  # improve half step position values
        particle_operations_util.add_to(v, v_temp, is_moving, scale=2.0 / 6.0)  # next accumulation of velocity from step 3

        # step 4, full step
        t2 = time_sec + dt
        fgm.setup_time_step(t2,  x2, is_moving, fix_bad=False)
        fgm.interp_field_at_particle_locations('water_velocity', is_moving, output=v_temp)
        particle_operations_util.add_to(v, v_temp, is_moving, scale=1.0 / 6.0)  # last accumulation of velocity for v4

        # final location using  accumulation in "v"
        # below is emulated by accumulation above of
        #  v = (v1 + 2.0 * (v2 + v3) + v4) /6
        #  x2 = x1 + v*dt
        solver_util.euler_substep( x1, v, velocity_modifier, dt, is_moving, x2)  # set final location directly to particle x property

        pass


    def screen_output(self, nt, time_sec,t0_model, t0_step):
        ri = si.run_info
        fraction_done= abs((time_sec - ri.start_time) / ri.duration)
        s = f'{100* fraction_done:02.0f}%'
        s += f' step {nt:04d}'
        s += si.core_roles.field_group_manager.screen_info()

        t = abs(time_sec - ri.start_time)
        s += ' Day ' + ('-' if si.settings.backtracking else '+')
        s += time_util.day_hms(t)
        s += ' ' + time_util.seconds_to_pretty_str(time_sec) + ':'
        s +=   si.core_roles.particle_group_manager.screen_info()

        elapsed_time= perf_counter() - t0_model
        remaining_time= (1 - fraction_done) * elapsed_time / max(.01, fraction_done)
        if elapsed_time > 300.:
            s += ' remaining: ' + time_util.seconds_to_hours_mins_string(abs(remaining_time)) +','

        s += f' step time = { (perf_counter() - t0_step) * 1000:4.1f} ms'
        si.msg_logger.msg(s)


    def _update_stats(self,n_time_step, time_sec):
        # update and write stats
        t0 = perf_counter()
        for name, i in si.roles.particle_statistics.items():
            pass
            if i.count_scheduler.do_task(n_time_step):
                i.start_update_timer()
                i.update(n_time_step, time_sec)
                i.stop_update_timer()
        si.block_timer('Update statistics', t0)

    def _update_concentrations(self,n_time_step,  time_sec):
        # update triangle concentrations, these can optionally be done every time step, if concentrations values affect particle properties

        t0 = perf_counter()
        for name, i in si.roles.particle_concentrations.items():
            i.start_update_timer()
            i.update(n_time_step, time_sec)
            i.stop_update_timer()
        si.block_timer('Update concentrations', t0)

    def _update_events(self, n_time_step,  time_sec):
        # write events

        t0 = perf_counter()
        for name, i in si.roles.event_loggers.items():
            i.start_update_timer()
            i.update(n_time_step,time_sec)
            i.stop_update_timer()
        si.block_timer('Update event loggers', t0)

    def close(self):
        pass



