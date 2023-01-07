from time import perf_counter

import numpy as np

from oceantracker.util import time_util
from datetime import datetime

from oceantracker.particle_properties.util import particle_operations_util
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from oceantracker.solver.util import solver_util


class Solver(ParameterBaseClass):
    #  does particle tracking solution as class to allow multi processing

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params({ 'screen_output_step_count':   PVC(1, int),
                                  'RK_order':                   PVC(4, int, possible_values=[1, 2, 4]),
                                  'n_sub_steps':                PVC(1, int, min=1),
                                  'name':                       PVC('solver',str) })

    def initialize(self):

        self.code_timer.start('solver_initialization')
        si = self.shared_info
        si.classes['particle_group_manager'].create_particle_property('manual_update', dict(name='v_temp', vector_dim=si.classes['particle_properties']['x'].num_vector_dimensions(), write=False))

        # set up working space for RK stesp to impriove L3 cache performance
        self.code_timer.stop('solver_initialization')

    def check_requirements(self):

        msg_list = self.check_class_required_fields_prop_etc(
            required_fields_list=['water_velocity'],
            required_props_list=['x','status', 'x_last_good', 'particle_velocity', 'v_temp'],
            required_grid_var_list=[])

        return msg_list

    def initialize_run(self):
        si = self.shared_info
        grid = si.classes['reader'].grid
        info = self.info
        pgm, fgm, tracks_writer = si.classes['particle_group_manager'], si.classes['field_group_manager'], si.classes['tracks_writer']
        part_prop = si.classes['particle_properties']

        info['computation_started'] = datetime.now()
        # set up particle velocity working space for solver
        info['n_time_steps_completed'] = 0
        info['total_alive_particles'] = 0


    def solve(self, nt_hindcast):
        # solve for data in buffer
        si = self.shared_info
        reader = si.classes['reader']
        grid = reader.grid
        grid_time_buffers = reader.grid_time_buffers

        info = self.info
        pgm, fgm   = si.classes['particle_group_manager'], si.classes['field_group_manager']
        part_prop = si.classes['particle_properties']

        for n, nt in enumerate(nt_hindcast[:-2]): # one less step as last step is initial condition for next block
            nt_remaining= nt_hindcast[n:] # remaining hindcast time steps to run
            if not reader.time_steps_in_buffer(nt_remaining):
                reader.fill_time_buffer(nt_remaining) # get next steps into buffer if not in buffer

            # set up run now data in buffer
            nb = (nt -grid_time_buffers['nt_hindcast'][0])*si.model_direction
            t_hindcast = grid_time_buffers['time'][nb]  # make time exactly that of hindcast

            # do sub steps with hind-cast model step
            for ns in range(self.params['n_sub_steps']):

                t0_step = perf_counter()

                t1 = t_hindcast + ns*si.model_substep_timestep*si.model_direction

                # release particles, update cell location/interp, update status, write tracks etc,
                # todo refactor all to use nt_hindcast not nb
                self.pre_step_bookkeeping(nb, t1, info['n_time_steps_completed'])

                # do integration step only for moving particles should this only be moving particles, with vel modifications and random walk
                is_moving = part_prop['status'].compare_all_to_a_value('eq', si.particle_status_flags['moving'], out=self.get_particle_index_buffer())

                # update particle velocity modification
                part_prop['velocity_modifier'].set_values(0., is_moving)  # zero out  modifier, to add in current values
                for i in si.class_interators_using_name['velocity_modifiers']['all'].values():
                    i.update(nb, t1, is_moving)

                # dispersion is done by random walk velocity modification prior to integration step
                si.classes['dispersion'].update(nb, t1, is_moving)

                #  Main integration step
                self.code_timer.start('integration_step')
                #--------------------------------------
                self.integration_step(nb,t1, is_moving)
                #--------------------------------------
                self.code_timer.stop('integration_step')

                t2 = t1 + si.model_substep_timestep * si.model_direction


                # at this point interp is not set up for current positions this is done in pre_step_bookeeping, and after last step

                # print screen data
                if (info['n_time_steps_completed']  + ns) % self.params['screen_output_step_count'] == 0:
                    self.screen_output(info['n_time_steps_completed'] , nt,  nb, ns, t1, t0_step)

                info['n_time_steps_completed']  += 1

                if abs(t2 - si.model_start_time) > si.model_duration:  break

        self.pre_step_bookkeeping(nb, t2, info['n_time_steps_completed']) # update interp and write out props at last step

        return info['n_time_steps_completed'], t2

    def pre_step_bookkeeping(self, nb, t, n_time_steps_completed):
        self.code_timer.start('pre_step_bookkeeping')
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        pgm = si.classes['particle_group_manager']
        fgm = si.classes['field_group_manager']
        # release particles
        #todo remove setp interp from particle release as done just below??
        new_particleIDs = pgm.release_particles(nb, t)

        alive = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags['frozen'], out=self.get_particle_index_buffer())
        self.info['total_alive_particles'] += alive.shape[0]
        
        # modify status
        for i in si.class_interators_using_name['status_modifiers']['all'].values():
            i.update(nb, t, alive)

        pgm.kill_old_particles(t) # todo convert to status modifier
        if si.compact_mode: pgm.remove_dead_particles_from_memory()

        # some may now have status dead so update
        alive = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags['frozen'], out=self.get_particle_index_buffer())

        # trajectory modifiers,
        for i in si.class_interators_using_name['trajectory_modifiers']['all'].values():
            i.update(nb, t, alive)

        alive = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags['frozen'], out=self.get_particle_index_buffer())

        # setup_interp_time_step
        fgm.setup_interp_time_step(nb, t, part_prop['x'].data, alive)

        # update particle properties
        pgm .update_PartProp(t, alive)

        # update writable class lists and stats at current time step now props are up to date
        self._update_stats(t)
        self._update_concentrations(nb, t)
        self._update_events(t)

        # write tracks
        if si.write_tracks:
            tracks_writer = si.classes['tracks_writer']
            tracks_writer.open_file_if_needed()
            tracks_writer.write_all_non_time_varing_part_properties(new_particleIDs)  # these must be written on release, to work in compact mode

            # write tracks file
            if n_time_steps_completed % si.classes['tracks_writer'].params['output_step_count'] == 0:
                tracks_writer.write_all_time_varying_prop_and_data()

        self.code_timer.stop('pre_step_bookkeeping')


    def integration_step(self, nb, t, is_moving):
        # single step in particle tracking, t is time in seconds, is_moving are indcies of moving particles
        # this is done inplace directly operation on the particle properties
        # nb is buffer offset
        si = self.shared_info
        RK_order =self.params['RK_order']
        fgm = si.classes['field_group_manager']
        part_prop =  si.classes['particle_properties']

        # note here subStep_time_step has sign of forwards/backwards
        dt = si.model_substep_timestep*si.model_direction
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
        fgm.setup_interp_time_step(nb, t,  x1, is_moving)

        if RK_order==1:
            fgm.interp_named_field_at_particle_locations('water_velocity', is_moving, output=v)
            solver_util.euler_substep( x1, v, velocity_modifier, dt, is_moving, x2)
            return is_moving

        # do first half step location from RK1 to update values
        fgm.interp_named_field_at_particle_locations('water_velocity', is_moving, output=v_temp)
        solver_util.euler_substep( x1, v_temp, velocity_modifier, dt2, is_moving, x2)
        particle_operations_util.copy(v, v_temp, is_moving, scale=1.0 / 6.0)   # accumulate RK velocity to reduce space taken by temporary working variables

        # step 2, get improved half step velocity
        t2=t + 0.5*dt
        fgm.setup_interp_time_step(nb, t2, x2, is_moving)

        if RK_order==2:
            fgm.interp_named_field_at_particle_locations('water_velocity', is_moving, output=v)
            solver_util.euler_substep( x1, v, velocity_modifier, dt, is_moving, x2)
            return is_moving

        fgm.interp_named_field_at_particle_locations('water_velocity', is_moving, output=v_temp)
        solver_util.euler_substep( x1, v_temp, velocity_modifier, dt2, is_moving, x2)
        particle_operations_util.add_to(v, v_temp, is_moving, scale=2.0 / 6.0)  # next accumulation of velocity step 2

        # step 3, a second half step
        t2 = t + 0.5 * dt
        fgm.setup_interp_time_step(nb, t2, x2, is_moving)
        fgm.interp_named_field_at_particle_locations('water_velocity', is_moving, output=v_temp)
        solver_util.euler_substep( x1, v_temp, velocity_modifier, dt, is_moving, x2)  # improve half step position values
        particle_operations_util.add_to(v, v_temp, is_moving, scale=2.0 / 6.0)  # next accumulation of velocity from step 3

        # step 4, full step
        t2 = t + dt
        fgm.setup_interp_time_step(nb, t2,  x2, is_moving)
        fgm.interp_named_field_at_particle_locations('water_velocity', is_moving, output=v_temp)
        particle_operations_util.add_to(v, v_temp, is_moving, scale=1.0 / 6.0)  # last accumulation of velocity for v4

        # final location using  accumulation in "v"
        # below is emulated by accumulation above of
        #  v = (v1 + 2.0 * (v2 + v3) + v4) /6
        #  x2 = x1 + v*dt
        solver_util.euler_substep( x1, v, velocity_modifier, dt, is_moving, x2)  # set final location directly to particle x property


    def screen_output(self,n_steps, nt,  nb,  ns, t1, t0_step):

        si= self.shared_info
        fraction_done= abs((t1 -si.model_start_time) / si.model_duration)
        s = '%02.0f%%:' % (100* fraction_done)
        s += '%06.0f:' % n_steps + 'h%06.0f:' % (nt) + 's%02.0f:' % ns + 'b%03.0f:' % nb

        t = abs( t1-si.model_start_time)
        s += 'Day ' +  ('-' if si.backtracking else '+')
        s += time_util.day_hms(t)
        s += ' ' + time_util.seconds_to_pretty_str(t1) + ':'
        s +=    si.classes['particle_group_manager'].screen_info()
        timePerStep = perf_counter() - t0_step
        #s += ' Finishes: ' + (datetime.now() + timePerStep*n_steps/(1.-fraction_done)).strftime('%y-%m-%d %H:%M')
        s +=  ' Step-%4.0f ms' % (timePerStep * 1000.)

        si.case_log.write_msg(s)


    def _update_stats(self,t):
        # update and write stats
        si= self.shared_info
        self.code_timer.start('on_the_fly_statistics')
        for s in si.class_interators_using_name['particle_statistics']['all'].values():
            if abs(t - s.info['time_last_stats_recorded']) >= s.params['calculation_interval']:
                s.update(time=t)

        self.code_timer.stop('on_the_fly_statistics')

    def _update_concentrations(self, nb, t):
        # update triangle concentrations
        si = self.shared_info
        self.code_timer.start('particle_concentrations')
        for s in si.class_interators_using_name['particle_concentrations']['all'].values():
            if abs(t - s.info['time_last_stats_recorded']) >= s.params['calculation_interval']:
                s.update(nb, t)

        self.code_timer.stop('particle_concentrations')

    def _update_events(self, t):
        # write events
        si = self.shared_info

        self.code_timer.start('event_logging')
        for e in si.class_interators_using_name['event_loggers']['all'].values():
            e.update(time=t)

        self.code_timer.stop('event_logging')

    def close(self):
        a=1



