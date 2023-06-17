from time import perf_counter

import numpy as np
from oceantracker.util import time_util
from datetime import datetime
from numba import types as nbt ,from_dtype,typeof
from oceantracker.util.numba_util import njitter
from oceantracker.particle_properties import particle_operations_util
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.solver.util import solver_util ,dev_triangle_kernnal_solver
from oceantracker.util.profiling_util import function_profiler
from oceantracker.util import numpy_util

class Solver(ParameterBaseClass):
    #  does particle tracking solution as class to allow multi processing

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params({
                        'RK_order':                   PVC(4, int, possible_values=[1, 2, 4]),
                        'n_sub_steps': PVC(None, int, obsolete='use shared_parameter "time_step", run may not have required time step'),
                        'screen_output_step_count': PVC(None, int, obsolete='use shared_parameter "screen_output_time_interval" in seconds')
                            })

    def initial_setup(self):
        si = self.shared_info
        si.classes['particle_group_manager'].create_particle_property('v_temp','manual_update', dict( vector_dim=si.classes['particle_properties']['x'].num_vector_dimensions(), write=False))

        # set up working space for RK stesp to impriove L3 cache performance


    def check_requirements(self):

        self.check_class_required_fields_prop_etc(
            required_fields_list=['water_velocity'],
            required_props_list=['x','status', 'x_last_good', 'particle_velocity', 'v_temp'],
            required_grid_var_list=[])

    def initialize_run(self):
        si = self.shared_info
        grid = si.classes['reader'].grid
        info = self.info
        pgm, fgm, tracks_writer = si.classes['particle_group_manager'], si.classes['field_group_manager'], si.classes['tracks_writer']
        part_prop = si.classes['particle_properties']


        # set up particle velocity working space for solver
        info['total_alive_particles'] = 0

        # todo dev work kernal solvnot working yet
        # kernal working space as numpy structure
        val = np.zeros((3,), dtype=np.float64)
        self.kernal_solver_info = numpy_util.numpy_structure_from_dict(
            dict( bc=val.copy(), x_temp= val.copy(),
                v1 =val.copy(),v2 =val.copy(),v3 =val.copy(),v4 =val.copy(),
                v=val.copy()
                ))  # barycentric coords
        if False:
            # wrap kernal solver with signature
            interp = si.classes['interpolator']
            pgm = si.classes['particle_group_manager']
            sig =[  nbt.float64,
                    nbt.float32[:, :, :, :],
                    from_dtype(interp.grid_as_struct.dtype),
                   from_dtype(pgm.part_prop_as_struct.dtype),
                   from_dtype(interp.step_info.dtype),
                   from_dtype(self.kernal_solver_info.dtype),
                   nbt.float64,
                   typeof(self.params['RK_order']),
                   nbt.float32[:]]
            #'(nestedarray(float64, (947, 3)), Tuple(float32, slice<a:b>))

            self.kernal_solver_fun = njitter(triangle_kernnal_solver.RKsolver, sig)

    #@profile
    def solve(self):
        # solve for data in buffer
        si = self.shared_info
        ml = si.msg_logger
        part_prop = si.classes['particle_properties']
        info = self.info # same as si.solver_info

        computation_started = datetime.now()

        pgm, fgm = si.classes['particle_group_manager'], si.classes['field_group_manager']
        info['time_steps_completed'] = 0

        # get hindcast step range
        time_span = fgm.get_hindcast_range()
        #todo simplify by dropping need to find model end time
        model_times = info['model_start_time'] + si.model_direction*np.arange(0., abs(time_span[1]-time_span[0]),abs(info['model_time_step']))
        # trim times to hindcast range
        sel = np.logical_and(model_times >= time_span[0], model_times <=time_span[1])
        model_times = model_times[ sel]


        # work out time steps between writing tracks to screen
        write_tracks_time_step = si.settings['screen_output_time_interval']
        if write_tracks_time_step is None:
            nt_write_time_step_to_screen = 1
        else:
            nt_write_time_step_to_screen = max(1,int(write_tracks_time_step/si.solver_info['model_time_step']))

        t0_model = perf_counter()
        free_wheeling =False
        # run forwards through model time variable, which for backtracking are backwards in time
        for nt  in range(model_times.size-1): # one less step as last step is initial condition for next block

            t0_step = perf_counter()
            time_sec = model_times[nt]

            # release particles
            new_particleIDs  = pgm.release_particles(time_sec)

            # count particles of each status and count number >= frozen status
            num_alive = pgm.status_counts_and_kill_old_particles(time_sec)
            if num_alive == 0:
                #freewheel until more are released or end of run/hindcast
                if not free_wheeling:
                    # at start note
                    ml.msg(f'No particles alive at {time_util.seconds_to_pretty_str(time_sec)}, skipping time steps until more are released', note=True)
                free_wheeling =True
                continue

            free_wheeling = False # has ended

            # print progress to screen
            if nt % nt_write_time_step_to_screen == 0:
                self.screen_output(si.solver_info['time_steps_completed'], time_sec, t0_model, t0_step)

            # alive partiles so do steps
            info['total_alive_particles'] += num_alive
            fgm.fill_reader_buffers_if_needed(time_sec)


            # do stats etc updates and write tracks
            self.pre_step_bookkeeping(nt, time_sec, new_particleIDs)

            # now modfy location after writing of moving particles
            # do integration step only for moving particles should this only be moving particles, with vel modifications and random walk
            is_moving = part_prop['status'].compare_all_to_a_value('eq', si.particle_status_flags['moving'], out=self.get_partID_buffer('ID1'))

            # update particle velocity modification
            part_prop['velocity_modifier'].set_values(0., is_moving)  # zero out  modifier, to add in current values
            for name, i in si.classes['velocity_modifiers'].items():
                i.update(time_sec, is_moving)

            # dispersion is done by random walk velocity modification prior to integration step
            si.classes['dispersion'].update(time_sec, is_moving)

            #  Main integration step
            #--------------------------------------
            self.integration_step(time_sec, is_moving)
            #self.kernal_solver(time_sec, is_moving)
            #--------------------------------------


            t2 = time_sec + info['model_time_step'] * si.model_direction

            # at this point interp is not set up for current positions, this is done in pre_step_bookeeping, and after last step


            info['time_steps_completed'] += 1

            if abs(t2 - info['model_start_time']) > info['model_duration']:  break

        # write out props etc at last step
        if nt > 0:# if more than on set completed
            self.pre_step_bookkeeping(nt, t2)
            self.screen_output(si.solver_info['time_steps_completed'], t2, t0_model, t0_step)

        info['model_end_time'] = t2
        info['model_end_date'] = t2.astype('datetime64[s]')
        info['model_run_duration'] =  info['model_end_time'] -info['model_start_time']
        info['computation_started'] =computation_started
        info['computation_ended'] = datetime.now()
        info['computation_duration'] = datetime.now() -computation_started

    def pre_step_bookkeeping(self, nt,time_sec,new_particleIDs=None):
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        pgm = si.classes['particle_group_manager']
        fgm = si.classes['field_group_manager']

        info = self.info  # same as si.solver_info

        info['current_model_date'] = time_util.seconds_to_datetime64(time_sec)
        info['current_model_time_step'] = nt
        info['current_model_time'] = time_sec

        pgm.remove_dead_particles_from_memory()

        # some may now have status dead so update
        alive = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags['frozen'], out=self.get_partID_buffer('ID1'))

        # modify status, eg tidal stranding
        for name, i in si.classes['status_modifiers'].items():
            i.update(time_sec, alive)

        # trajectory modifiers,
        for name, i in si.classes['trajectory_modifiers'].items():
            i.update(time_sec, alive)

        if si.is_3D_run:
            si.classes['resuspension'].update(time_sec, alive)

        alive = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags['frozen'], out=self.get_partID_buffer('ID1'))

        # setup_interp_time_step
        fgm.setup_time_step(time_sec, part_prop['x'].data, alive)
        fgm.update_dry_cells()

        # update particle properties
        pgm.update_PartProp(time_sec, alive)

        # update writable class lists and stats at current time step now props are up to date
        self._update_stats(time_sec)
        self._update_concentrations(time_sec)
        self._update_events(time_sec)

        # write tracks
        if si.write_tracks:
            tracks_writer = si.classes['tracks_writer']
            tracks_writer.open_file_if_needed()
            if new_particleIDs is not None:
                tracks_writer.write_all_non_time_varing_part_properties(new_particleIDs)  # these must be written on release, to work in compact mode

            # write tracks file
            tracks_writer.write_all_time_varying_prop_and_data()


    def integration_step(self, time_sec, is_moving):
        # single step in particle tracking, t is time in seconds, is_moving are indcies of moving particles
        # this is done inplace directly operation on the particle properties
        # nb is buffer offset
        si = self.shared_info
        RK_order =self.params['RK_order']
        fgm = si.classes['field_group_manager']
        part_prop =  si.classes['particle_properties']

        # note here subStep_time_step has sign of forwards/backwards
        dt = si.solver_info['model_time_step']*si.model_direction
        dt2=dt/2.
        # set up views of  working variable space
        x1      = part_prop['x_last_good'].data
        x2      = part_prop['x'].data
        v       = part_prop['particle_velocity'].data
        v_temp  = part_prop['v_temp'].data  # temp vel from interp at each RK substeps
        velocity_modifier= part_prop['velocity_modifier'].data

        # this makes x1, ['x_last_good']  at start of new integration step for moving particles, allowing updates to x2 ['x']
        particle_operations_util.copy(x1, x2, is_moving)

        #  step 1 from current location and time
        fgm.setup_time_step(time_sec, x1, is_moving)

        if RK_order==1:
            fgm.eval_water_velocity(v, is_moving)
            solver_util.euler_substep( x1, v, velocity_modifier, dt, is_moving, x2)
            return is_moving

        # do first half step location from RK1 to update values
        fgm.eval_water_velocity( v_temp, is_moving)
        solver_util.euler_substep( x1, v_temp, velocity_modifier, dt2, is_moving, x2)
        particle_operations_util.copy(v, v_temp, is_moving, scale=1.0 / 6.0)   # accumulate RK velocity to reduce space taken by temporary working variables

        # step 2, get improved half step velocity
        t2= time_sec + 0.5 * dt
        fgm.setup_time_step(t2, x2, is_moving)

        if RK_order==2:
            fgm.eval_water_velocity(v, is_moving)
            solver_util.euler_substep( x1, v, velocity_modifier, dt, is_moving, x2)
            return is_moving

        fgm.eval_water_velocity( v_temp, is_moving)
        solver_util.euler_substep( x1, v_temp, velocity_modifier, dt2, is_moving, x2)
        particle_operations_util.add_to(v, v_temp, is_moving, scale=2.0 / 6.0)  # next accumulation of velocity step 2

        # step 3, a second half step
        t2 = time_sec + 0.5 * dt
        fgm.setup_time_step(t2, x2, is_moving)
        fgm.eval_water_velocity( v_temp, is_moving)
        solver_util.euler_substep( x1, v_temp, velocity_modifier, dt, is_moving, x2)  # improve half step position values
        particle_operations_util.add_to(v, v_temp, is_moving, scale=2.0 / 6.0)  # next accumulation of velocity from step 3

        # step 4, full step
        t2 = time_sec + dt
        fgm.setup_time_step(t2,  x2, is_moving)
        fgm.eval_water_velocity( v_temp, is_moving)
        particle_operations_util.add_to(v, v_temp, is_moving, scale=1.0 / 6.0)  # last accumulation of velocity for v4

        # final location using  accumulation in "v"
        # below is emulated by accumulation above of
        #  v = (v1 + 2.0 * (v2 + v3) + v4) /6
        #  x2 = x1 + v*dt
        solver_util.euler_substep( x1, v, velocity_modifier, dt, is_moving, x2)  # set final location directly to particle x property

        #print('xxx', x2[:10, :] - x1[:10, :],v[:10,:])

    def screen_output(self, nt, time_sec,t0_model, t0_step):

        si= self.shared_info
        interp_info= si.classes["interpolator"].step_info #todo more than one reader?

        fraction_done= abs((time_sec - si.solver_info['model_start_time']) / si.solver_info['model_duration'])
        s = f'{100* fraction_done:02.0f}%'
        s += f' step {nt:04d}:H{interp_info["current_hydro_model_step"]:04d}b{interp_info["nb"][0]:02d}-{interp_info["nb"][1]:02d}'
        t = abs(time_sec - si.solver_info['model_start_time'])
        s += ' Day ' + ('-' if si.backtracking else '+')
        s += time_util.day_hms(t)
        s += ' ' + time_util.seconds_to_pretty_str(time_sec) + ':'
        s +=   si.classes['particle_group_manager'].screen_info()

        elapsed_time= perf_counter() - t0_model
        remaining_time= (1 - fraction_done) * elapsed_time / max(.01, fraction_done)
        if elapsed_time > 300.:
            s += ' remaining: ' + time_util.seconds_to_hours_mins_string(abs(remaining_time)) +','

        s += f' step time = { (perf_counter() - t0_step) * 1000:4.1f} ms'
        si.msg_logger.msg(s)

    def _update_stats(self,time_sec):
        # update and write stats
        si= self.shared_info
        for name, i in si.classes['particle_statistics'].items():
            if abs(time_sec - i.info['time_last_stats_recorded']) >= i.params['update_interval']:
                i.start_update_timer()
                i.update(time_sec)
                i.stop_update_timer()

    def _update_concentrations(self, time_sec):
        # update triangle concentrations
        si = self.shared_info
        for name, i in si.classes['particle_concentrations'].items():
            if abs(time_sec - i.info['time_last_stats_recorded']) >= i.params['update_interval']:
                i.start_update_timer()
                i.update(time_sec)
                i.stop_update_timer()

    def _update_events(self, t):
        # write events
        si = self.shared_info
        for name, i in si.classes['event_loggers'].items():
            i.start_update_timer()
            i.update(time_sec=t)
            i.stop_update_timer()

    def close(self):
        pass



