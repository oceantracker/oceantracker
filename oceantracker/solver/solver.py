from time import perf_counter
import psutil
from os import  path, mkdir

import numpy as np
from oceantracker.util import time_util, json_util, ncdf_util, save_state_util
from datetime import datetime
from oceantracker.particle_properties.util import particle_operations_util, particle_comparisons_util
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.solver.util import solver_util
from oceantracker.shared_info import shared_info as si

class Solver(ParameterBaseClass):
    ''' Does particle tracking solution '''

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params({
                        'RK_order':  PVC(4, int, possible_values=[1, 2, 4]),
                        'n_sub_steps': PVC(None, int, obsolete=True,  doc_str ='use shared_parameter "time_step", run may not have required time step'),
                        'screen_output_step_count': PVC(None, int, obsolete=True,  doc_str='use main setting "screen_output_time_interval" in seconds. ie not a solver setting')
                            })

    def add_required_classes_and_settings(self):
        info = self.info
        crumbs='Solver_initial_setup >'
        si.add_class('particle_properties', name= 'v_temp',class_name='ManuallyUpdatedParticleProperty', vector_dim= si.run_info.vector_components, write=False, crumbs=crumbs)

    def initial_setup(self):
        pass

    def check_requirements(self):
        self.check_class_required_fields_prop_etc( required_props_list=['x','status', 'x_last_good', 'v_temp'])

    def solve(self):
        # solve for data in buffer
        info = self.info
        ri=si.run_info
        ml = si.msg_logger
        part_prop = si.class_roles.particle_properties

        computation_started = datetime.now()
        # set up particle velocity working space for solver
        pgm, fgm = si.core_class_roles.particle_group_manager, si.core_class_roles.field_group_manager
        ri.time_steps_completed = 0

        # work out time steps between writing tracks to screen, default 1 hr
        nt_write_time_step_to_screen = max(1, int(si.settings.screen_output_time_interval/si.settings.time_step))

        t0_model = perf_counter()
        model_times = si.run_info.times
        ml.hori_line()

        # initial buffer fill
        tr0 = perf_counter()
        fgm.update_readers(model_times[0])
        si.block_timer('Reading hindcast', tr0)


        # run forwards through model time variable, which for backtracking are backwards in time
        ml.progress_marker(f'Starting time stepping: {time_util.seconds_to_isostr(si.run_info.start_date)} to {time_util.seconds_to_isostr(si.run_info.end_date)}')
        ml.msg(f'duration  {time_util.seconds_to_pretty_duration_string(si.run_info.duration)}, time step=  {time_util.seconds_to_pretty_duration_string(si.settings.time_step)} ',
                           tabs =2)

        si.msg_logger.set_screen_tag('S')

        # initial conditions
        t0_step = perf_counter()


        if si.run_info.restarting:
            nt1 = si.restart_info['restart_time_step']
            t1 = model_times[nt1]
            self._load_saved_state()
        else:
            nt1 = 0
            t1 = model_times[0]
            new_particle_indices = pgm.release_particles(nt1,t1 )
            self._pre_step_bookkeeping(nt1, t1, new_particle_indices)

        ri.time_steps_completed = nt1
        num_alive = pgm.status_counts_and_kill_old_particles(t1)
        self._screen_output(nt1, t1, t0_model, perf_counter() - t0_step)

        if si.settings.restart_interval is not None:
            # dev-schedule restart saves at given interval after start of run
            self.add_scheduler('save_state',
                               start=si.run_info.start_time,
                               interval=si.settings.restart_interval )
        # run one less step as last step is initial condition for next block
        # first step is zero or restart time step
        for n_time_step  in range(nt1, model_times.size-1):

            t0_step = perf_counter()
            self.start_update_timer()
            t1 = model_times[n_time_step]
            # record info for any error dump
            info['time_sec'] = t1

            tr0 = perf_counter()
            fgm.update_readers(t1)
            si.block_timer('Reading hindcast', tr0)


            # do integration step only for moving particles should this only be moving particles, with vel modifications and random walk
            is_moving = part_prop['status'].compare_all_to_a_value('eq', si.particle_status_flags.moving,  out=self.get_partID_buffer('B1'))

            # update particle velocity modification prior to integration
            part_prop['velocity_modifier'].set_values(0., is_moving)  # zero out  modifier, to add in current values
            for name, i in si.class_roles.velocity_modifiers.items():
                i.timed_update(n_time_step, t1, is_moving)

            # dispersion is done by random walk
            # by adding to velocity modifier prior to integration step
            if si.settings.use_dispersion:
                i = si.core_class_roles.dispersion
                i.timed_update(n_time_step, t1, is_moving)

            #  Main integration step
            #--------------------------------------
            self.do_time_step(t1, is_moving)
            #--------------------------------------

            # release particles etc at next time step
            nt2 = n_time_step + 1
            t2 = model_times[nt2]

            # release particles
            tr0 = perf_counter()
            new_particle_indices = pgm.release_particles(nt2, t2)
            si.block_timer('Releasing particles', tr0)

            # do stats etc updates and write tracks at new time step
            self._pre_step_bookkeeping(nt2, t2, new_particle_indices)

            if si.settings.restart_interval is not None and self.schedulers['save_state'].do_task(nt2):
                self._save_state_for_restart(nt2, t2)

            # cull dead particles
            # must be done after last use of "is_moving" in current time step (which refers to permanent  ID buffer which are not culled)
            pgm.remove_dead_particles_from_memory()

            # count particles of each status and count number >= stationary status
            num_alive = pgm.status_counts_and_kill_old_particles(t2)

            ri.time_steps_completed += 1
            # print progress to screen
            if nt2 % nt_write_time_step_to_screen == 0:
                self._screen_output(nt2, t2, t0_model, perf_counter() - t0_step)


            # at this point interp is not set up for current positions, this is done in pre_step_bookeeping, and after last step
            self.stop_update_timer()

            # warn of  high physical memory use every 10th step as takes 8ms per call
            if n_time_step % 10 ==0 and psutil.virtual_memory().percent > 95:
                ml.msg(' More than 95% of memory is being used!, code may run slow as memory may be paged to disk', warning=True,
                       hint=f'Reduce memory used by hindcast with smaller reader param. "time_buffer_size"')

            if abs(t2 - ri.start_time) > ri.duration: break
            if si.settings.throw_debug_error == 1 and nt2 >= int(0.2*model_times.size):
                raise(Exception(f'Restart testing, throwing deliberate error at {time_util.seconds_to_isostr(t2)}'))

        ri.end_time = t2
        ri.model_end_date = t2.astype('datetime64[s]')
        ri.model_run_duration =  ri.end_time - ri.start_time
        ri.computation_started = computation_started
        ri.computation_ended = datetime.now()
        ri.computation_duration = datetime.now() -computation_started


    def _pre_step_bookkeeping(self, n_time_step,time_sec,
                              new_particle_indices=np.full((0,),0,dtype=np.int32)):
        part_prop = si.class_roles.particle_properties
        pgm = si.core_class_roles.particle_group_manager
        fgm = si.core_class_roles.field_group_manager



        ri = si.run_info
        ri.current_model_date = time_util.seconds_to_datetime64(time_sec)
        ri.current_model_time_step = n_time_step
        ri.current_model_time = time_sec

        # some may now have status dead so update
        alive = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags.stationary, out=self.get_partID_buffer('B1'))

        # setup_interp_time_step, cell etc
        fgm.setup_time_step(time_sec, part_prop['x'].data, alive)

        #todo replace this with  tide waster depth done cell find
        fgm.interp_field_at_particle_locations('tide', alive, output=part_prop['tide'].data)
        fgm.interp_field_at_particle_locations('water_depth', alive, output=part_prop['water_depth'].data)

        # trajectory modifiers
        for name, i in si.class_roles.trajectory_modifiers.items():
            i.timed_update(n_time_step, time_sec, alive)

        alive = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags.stationary, out=self.get_partID_buffer('B1'))


        fgm.setup_time_step(time_sec, part_prop['x'].data, alive)
        #fgm.interp_field_at_particle_locations('tide', alive, output=part_prop['tide'].data)
        #fgm.interp_field_at_particle_locations('water_depth', alive, output=part_prop['water_depth'].data)

        # update particle properties
        pgm.update_PartProp(n_time_step, time_sec, alive)

        # update dry cells and tidal stranding status
        fgm.update_dry_cell_values()
        fgm.update_tidal_stranding_status(time_sec, alive)

        # update writable class lists and stats at current time step now props are up to date
        self._update_stats(n_time_step, time_sec, alive)
        self._update_events(n_time_step, time_sec)

        # update integrated models, eg LCS
        if si.core_class_roles.integrated_model is not None :
            si.core_class_roles.integrated_model.update(n_time_step, time_sec)

        # write tracks
        if si.settings.write_tracks:
            tracks_writer = si.core_class_roles.tracks_writer
            tracks_writer.start_update_timer()
            tracks_writer.open_file_if_needed()

            if new_particle_indices.size > 0:
                tracks_writer.write_all_non_time_varing_part_properties(new_particle_indices)  # these must be written on release, to work in compact mode

            # write time varying track data to file if scheduled
            if tracks_writer.schedulers['write_scheduler'].do_task(n_time_step):
                tracks_writer.write_all_time_varying_prop_and_data()
            tracks_writer.stop_update_timer()



        # resuspension is a core trajectory modifier, upated after resupension
        # so those on bottom can be recorded
        if si.settings.use_resuspension and si.run_info.is3D_run:
            # friction_velocity property  is now updated, so do resupension
            i = si.core_class_roles.resuspension
            i.timed_update(n_time_step, time_sec, alive)

    def do_time_step(self, time_sec, is_moving):

        fgm = si.core_class_roles.field_group_manager
        part_prop = si.class_roles.particle_properties

        # record las t good values og key prop
        part_prop['x_last_good'].copy('x', is_moving)
        part_prop['n_cell_last_good'].copy('n_cell', is_moving)
        part_prop['status_last_good'].copy('status', is_moving)
        part_prop['bc_coords_last_good'].copy('bc_coords', is_moving)

        # do time step
        dt = si.settings.time_step*si.run_info.model_direction
        self._RK_step(time_sec, dt, is_moving)

        pass

    def _RK_step(self, time_sec, dt, is_moving):
        # single step in particle tracking, t is time in seconds, is_moving are indcies of moving particles
        # this is done inplace directly operation on the particle properties
        # nb is buffer offset

        RK_order =self.params['RK_order']
        fgm = si.core_class_roles.field_group_manager
        part_prop =  si.class_roles.particle_properties

        # note here subStep_time_step has sign of forwards/backwards
        dt2 = dt/2.
        # set up views of  working variable space
        x1 = part_prop['x_last_good'].data
        x2 = part_prop['x'].data
        water_velocity  = part_prop['water_velocity'].data
        v_temp  = part_prop['v_temp'].data  # temp vel from interp at each RK substeps
        velocity_modifier= part_prop['velocity_modifier'].data
        n_cell =  part_prop['n_cell'].data
        n_cell_last_good = part_prop['n_cell_last_good'].data

        #  step 1 from current location and time
        fgm.setup_time_step(time_sec, x1, is_moving)

        if RK_order==1:
            fgm.interp_field_at_particle_locations('water_velocity', is_moving, output=water_velocity)
            self._euler_substep(x1, water_velocity, velocity_modifier, dt, is_moving, x2)
            return

        # do first half step location from RK1 to update values
        fgm.interp_field_at_particle_locations('water_velocity', is_moving, output=v_temp)

        self._euler_substep(x1, v_temp, velocity_modifier, dt2, is_moving, x2)
        particle_operations_util.scale_and_copy(water_velocity, v_temp, is_moving, scale=1.0 / 6.0)   # accumulate RK velocity to reduce space taken by temporary working variables

        #self.screen_info(f'xx time step {si.settings.time_step}',5)

        # step 2, get improved half step velocity
        t2= time_sec + 0.5 * dt
        fgm.setup_time_step(t2, x2, is_moving)

        if RK_order==2:
            fgm.interp_field_at_particle_locations('water_velocity', is_moving, output=water_velocity)
            self._euler_substep(x1, water_velocity, velocity_modifier, dt, is_moving, x2)
            return

        fgm.interp_field_at_particle_locations('water_velocity', is_moving, output=v_temp)
        self._euler_substep(x1, v_temp, velocity_modifier, dt2, is_moving, x2)
        particle_operations_util.add_to(water_velocity, v_temp, is_moving, scale=2.0 / 6.0)  # next accumulation of velocity step 2


        # step 3, a second half step
        t2 = time_sec + 0.5 * dt
        fgm.setup_time_step(t2, x2, is_moving)
        fgm.interp_field_at_particle_locations('water_velocity', is_moving, output=v_temp)
        self._euler_substep(x1, v_temp, velocity_modifier, dt, is_moving, x2)  # improve half step position values
        particle_operations_util.add_to(water_velocity, v_temp, is_moving, scale=2.0 / 6.0)  # next accumulation of velocity from step 3

        # step 4, full step
        t2 = time_sec + dt
        fgm.setup_time_step(t2,  x2, is_moving)
        fgm.interp_field_at_particle_locations('water_velocity', is_moving, output=v_temp)
        particle_operations_util.add_to(water_velocity, v_temp, is_moving, scale=1.0 / 6.0)  # last accumulation of velocity for v4

        # final location using  accumulation in "v"
        # below is emulated by accumulation above of
        #  v = (v1 + 2.0 * (v2 + v3) + v4) /6
        #  x2 = x1 + v*dt
        self._euler_substep(x1, water_velocity, velocity_modifier, dt, is_moving, x2)  # set final location directly to particle x property

        pass

    def _euler_substep(self, xold, water_velocity, velocity_modifier, dt, active, xnew):
        part_prop = si.class_roles.particle_properties
        t0 = perf_counter()
        if si.run_info.is3D_run:
            if si.settings.use_geographic_coords:
                solver_util.euler_substep_geographic3D(part_prop['degrees_per_meter'].data,
                    xold, water_velocity, velocity_modifier, dt, active, xnew)
            else:
                solver_util.euler_substep3D(xold, water_velocity, velocity_modifier, dt, active, xnew)
        else:
            if si.settings.use_geographic_coords:
                solver_util.euler_substep_geographic2D(part_prop['degrees_per_meter'].data,
                                                       xold, water_velocity, velocity_modifier, dt, active, xnew)
            else:
                solver_util.euler_substep2D(xold, water_velocity, velocity_modifier, dt, active, xnew)
        si.block_timer('RK integration', t0)

    def _screen_output(self, nt, time_sec,t0_model, t_step):
        ri = si.run_info
        fgm = si.core_class_roles.field_group_manager
        pgm = si.core_class_roles.particle_group_manager
        fraction_done= abs((time_sec - ri.start_time) / ri.duration)
        s = f'{nt:04d}'
        s += f': {100* fraction_done:02.0f}%'

        s += fgm.screen_info()

        t = abs(time_sec - ri.start_time)
        s += ' Day ' + ('-' if si.settings.backtracking else '+')
        s += time_util.day_hms(t)
        s += ' ' + time_util.seconds_to_pretty_str(time_sec) + ':'
        s +=   pgm.screen_info()

        elapsed_time= perf_counter() - t0_model
        if elapsed_time > 300.:
            #todo better estimate of time remaining based on partcle numbers?
            remaining_time= (1 - fraction_done) * elapsed_time / max(.01, fraction_done)
            s += ' remaining: ' + time_util.seconds_to_hours_mins_string(abs(remaining_time)) +','

        s += f' step time = { t_step * 1000:4.1f} ms'
        si.msg_logger.msg(s)

    def _update_stats(self,n_time_step, time_sec, alive):
        # update and write stats
        t0 = perf_counter()
        for name, i in si.class_roles.particle_statistics.items():
            if i.schedulers['count_scheduler'].do_task(n_time_step) and i.params['write']:
                i.open_file_if_needed()
                i.timed_update(n_time_step, time_sec, alive)

        si.block_timer('Update statistics', t0)



    def _update_events(self, n_time_step,  time_sec):
        # write events

        t0 = perf_counter()
        for name, i in si.class_roles.event_loggers.items():
            i.timed_update(n_time_step,time_sec)

        si.block_timer('Update event loggers', t0)

    def close(self):
        pass


    def _save_state_for_restart(self, n_time_step, time_sec):

        si.msg_logger.msg(f'save_state_for_restart at: {time_util.seconds_to_isostr(time_sec)}, time step= {n_time_step}'
                          +f', released  {si.core_class_roles.particle_group_manager.info["particles_released"]}  particles so far',
                          hint='Restarting is under development and does not yet work!!!')

        # close time varying output files, eg tracks and stats files first!
        if si.settings.write_tracks:
            si.core_class_roles.tracks_writer._close_file()

        state_dir = si.run_info.saved_state_dir
        state = dict(run_start_time= si.run_info.start_time,
                     restart_time=time_sec,
                     restart_time_step=n_time_step,
                     run_start_date=time_util.seconds_to_isostr(si.run_info.start_time),
                     restart_date = time_util.seconds_to_isostr(time_sec),
                     particles_released= si.core_class_roles.particle_group_manager.info['particles_released'],
                     state_dir=state_dir,
                     run_output_dir= si.run_info.root_output_dir,
                     settings= si.settings.asdict(),
                     part_prop_file =path.join(state_dir, 'particle_properties.nc'),
                     stats_files=dict(),
                     )

        # save class info
        state['class_info'] = save_state_util.get_class_info(si)

        if not path.isdir(state_dir):  mkdir(state_dir)

        # save particle properties
        save_state_util.save_part_prop_state(state['part_prop_file'], si, n_time_step, time_sec)

        # save stats state
        state['stats']= dict()
        for name, i in si.class_roles['particle_statistics'].items():
            state['stats_files'][name]= i.save_state(si, state_dir)

        state['log_file'] = si.msg_logger.save_state(si,state_dir)

        # write state json for restarting
        json_util.write_JSON(path.join(state_dir, 'state_info.json'),state)

        # write flag file to say state save successful
        with open(path.join(state_dir, 'state_complete.txt'), "w") as file:
            file.write("State Save complete.\n")


    def _load_saved_state(self):

        rsi = si.restart_info
        class_info = rsi['class_info']
        pgm = si.core_class_roles.particle_group_manager

        # load particle properties
        nc = ncdf_util.NetCDFhandler(rsi['part_prop_file'])
        num_part = nc.var_shape('water_velocity')[0]

        for name, i in si.class_roles.particle_properties.items():
            i.data = nc.read_variable(name)  # rely on particle buffer expansion
        si.run_info.particles_in_buffer = num_part

        # set new buffer size and number release so far,
        # needed to set particle ID correctly
        pgm.info['current_particle_buffer_size'] = num_part
        pgm.info['particles_released'] = rsi['particles_released']
        nc.close()

        # restore settings
        #for name,val  in rsi['settings'].items(): si.settings[name] = val
        si.settings.throw_debug_error = 0 # dont do again

        # reinstate tracks writer state
        if si.settings.write_tracks:
            si.core_class_roles.tracks_writer.info = class_info['core_class_roles']['tracks_writer']

        # restore stats from netcdf
        for name, i in si.class_roles['particle_statistics'].items():
            i.restart(rsi)
        pass