from time import perf_counter
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

        msg_list = self.check_class_required_fields_properties_grid_vars_and_3D(
            required_fields=['water_velocity'],
            required_props=['x','status', 'x_last_good', 'particle_velocity', 'v_temp'],
            required_grid_vars=[])

        return msg_list

    def initialize_run(self, nb0):
        si = self.shared_info
        grid = si.classes['reader'].grid
        info = self.info
        pgm, fgm, tracks_writer = si.classes['particle_group_manager'], si.classes['field_group_manager'], si.classes['tracks_writer']
        part_prop = si.classes['particle_properties']

        info['computation_started'] = datetime.now()
        # set up particle velocity working space for solver
        info['n_time_steps_completed'] = 0
        info['total_active_particles'] = 0

        # initial release , writes and statistics etc
        t0 = grid['time'][nb0]
        new_particleIDs = pgm.release_particles(nb0, t0)
        fgm.setup_interp_time_step(nb0, t0, part_prop['x'].data, new_particleIDs)  # set up interp for first time step
        pgm.update_PartProp(t0, new_particleIDs)  # now update part prop with good cell and bc cords, eg  interp water_depth

        if si.write_output_files and si.write_tracks:
            tracks_writer.open_file_if_needed()
            tracks_writer.write_all_time_varying_prop_and_data()
            tracks_writer.write_all_non_time_varing_part_properties(new_particleIDs)

        self._update_stats(t0)
        self._update_concentrations(nb0, t0)
        self._update_events(t0)


    def solve_for_data_in_buffer(self, nb0, num_in_buffer, nt0):
        # solve for data in buffer
        si = self.shared_info
        grid = si.classes['reader'].grid
        info = self.info
        pgm, fgm, tracks_writer   = si.classes['particle_group_manager'], si.classes['field_group_manager'], si.classes['tracks_writer']
        part_prop = si.classes['particle_properties']


        for nb in range(nb0,nb0 + num_in_buffer-1): # one less step as last step is initial condition for next block

            t_hindcast = grid['time'][nb]  # make time exactly that of grid

            # do sub steps with hindcast model step
            for ns in range(self.params['n_sub_steps']):
                # round start time to nearest hindcast step
                t0_step = perf_counter()
                t1 = t_hindcast + ns*si.model_substep_timestep*si.model_direction

                #  Main integration step
                #  --------------------------------------
                self.code_timer.start('integration_step')
                #  --------------------------------------

                moving = self.integration_step(nb,t1)
                #--------------------------------------
                self.code_timer.stop('integration_step')

                t2 = t1 + si.model_substep_timestep * si.model_direction

                # dispersion
                if moving.shape[0] > 0:
                    si.classes['dispersion'].update(nb, t2, moving)
                    # after dispersion some may be outside, update search cell status to see which are now outside domain etc
                    fgm.setup_interp_time_step(nb, t2, part_prop['x'].data, moving)



                self.post_step_bookeeping(nb, t2)

                new_particleIDs = pgm.release_particles(nb, t2)
                if si.write_tracks:
                    tracks_writer.write_all_non_time_varing_part_properties(new_particleIDs)  # these must be written on release, to work in compact mode

                    # write tracks file
                    if info['n_time_steps_completed'] % si.classes['tracks_writer'].params['output_step_count'] == 0:
                        tracks_writer.open_file_if_needed()
                        tracks_writer.write_all_time_varying_prop_and_data()

                # update outputs
                self._update_stats(t2)
                self._update_concentrations(nb, t2)
                self._update_events(t2)

                # print screen data
                if (info['n_time_steps_completed']  + ns) % self.params['screen_output_step_count'] == 0:
                    self.screen_output(info['n_time_steps_completed'] , nt0, nb0, nb, ns, t1, t0_step)

                pgm.kill_old_particles(t2)

                if si.compact_mode: pgm.remove_dead_particles_from_memory()


                info['n_time_steps_completed']  += 1

                if abs(t2 - si.model_start_time) > si.model_duration:  break

        return info['n_time_steps_completed'], t2

    def integration_step(self, nb, t):
        # single step in particle tracking, t is time in seconds, is_moving are indcies of moving particles
        # this is done inplace directly operation on the particle properties
        # nb is buffer offset
        si = self.shared_info
        RK_order =self.params['RK_order']
        fgm = si.classes['field_group_manager']
        part_prop =  si.classes['particle_properties']

        # note here subStep_time_step has sign of forwards/backwards
        dt = si.model_substep_timestep*si.model_direction
        # set up views of  working variable space
        x1      = part_prop['x_last_good'].data
        x2      = part_prop['x'].data
        v       = part_prop['particle_velocity'].data
        v_temp  = part_prop['v_temp'].data  # temp vel from interp at each RK substeps
        is_moving = part_prop['status'].compare_all_to_a_value('eq', si.particle_status_flags['moving'], out = self.get_particle_index_buffer())

        # this makes x1, ['x_last_good']  at start of new integration step for moving particles, allowing updates to x2 ['x']
        particle_operations_util.copy(x1, x2, is_moving)

        #  step 1 from current location and time
        fgm.setup_interp_time_step(nb, t,  x1, is_moving)

        if RK_order==1:
            self.update_particle_velocity(t,v, is_moving) # put vel into permanent place
            solver_util.euler_substep(x2, x1, v, dt, is_moving)
            return is_moving

        self.update_particle_velocity(t,v_temp, is_moving)  # velocity in temp place

        # do first half step location from RK1 to update values
        solver_util.euler_substep(x2, x1, v_temp, dt / 2., is_moving)

        # accumulate RK velocity to reduce space taken by temporary working variables
        particle_operations_util.copy(v, v_temp, is_moving, scale=1.0 / 6.0) # vel at start of step

        # step 2, get improved half step velocity
        t2=t + 0.5*dt
        fgm.setup_interp_time_step(nb, t2, x2, is_moving)

        if RK_order==2:
            self.update_particle_velocity(t2,v, is_moving)
            solver_util.euler_substep(x2, x1, v, dt, is_moving)
            return is_moving

        self.update_particle_velocity(t2, v_temp, is_moving)

        # step 3, a second half step
        solver_util.euler_substep(x2, x1, v_temp, dt / 2., is_moving)  # improve half step position
        particle_operations_util.add_to(v, v_temp, is_moving, scale=2.0 / 6.0)  # next accumulation of velocity step 2

        t2 = t + 0.5 * dt
        fgm.setup_interp_time_step(nb, t2, x2, is_moving)
        self.update_particle_velocity(t2,v_temp , is_moving)  # v3, better velocity at half step

        solver_util.euler_substep(x2, x1, v_temp, dt, is_moving)  # improve half step position values
        particle_operations_util.add_to(v, v_temp, is_moving, scale=2.0 / 6.0)  # next accumulation of velocity from step 3

        # step 4, full step
        t2 = t + dt
        fgm.setup_interp_time_step(nb, t2,  x2, is_moving)
        self.update_particle_velocity( t2, v_temp, is_moving)  # full step for v4

        particle_operations_util.add_to(v, v_temp, is_moving, scale=1.0 / 6.0)  # last accumulation of velocity for v4

        # final location using  accumulation in "v"
        # below is emulated by accumulation above of
        #  v = (v1 + 2.0 * (v2 + v3) + v4) /6
        #  x2 = x1 + v*dt
        solver_util.euler_substep(x2, x1, v, dt, is_moving)  # set final location directly to particle x property

        return  is_moving

    def update_particle_velocity(self, t, v, active):
        # get water velocity plus any particle affects on velocity in particle_velocity, eg terminal velocity
        si= self.shared_info
        si.classes['field_group_manager'].interp_named_field_at_particle_locations('water_velocity', active, output=v)

        # any effects of super-imposable modifiers of the velocity, eg terminal  velocity in 3D to be added to w component
        for key, vm in si.classes['velocity_modifiers'].items():
            v = vm.modify_velocity(v, t, active)

    def post_step_bookeeping(self, nb, t2):
        # do dispersion, modify trajectories,
        # do strandings etc to change particle status
        # update part prop, eg  interp mapped reader fields to particle locations
        self.code_timer.start('post_step_bookeeping')
        si = self.shared_info
        grid = si.classes['reader'].grid
        pm = si.classes['particle_group_manager'] # internal short cuts
        fgm = si.classes['field_group_manager']
        part_prop  =  si.classes['particle_properties']



        # user particle movements, eg resupension for all particles
        # re-find alive particles after above movements
        sel = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags['frozen'], out=self.get_particle_index_buffer())
        self.info['total_active_particles'] += sel.shape[0]
        for i in si.class_interators_using_name['trajectory_modifiers']['all'].values():
            i.update(nb, t2, sel)

        # after moves, update search cell status, dry cell index,  to see which are now outside domain etc
        fgm.setup_interp_time_step(nb, t2, part_prop['x'].data, sel)

        # now all  particle movements complete after trajectory changes, move backs, update cell and bc cords for latest locations, update particle properties
        sel = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags['frozen'], out=self.get_particle_index_buffer())
        # now update part prop with good cell and bc cords, eg  interp water_depth
        pm.update_PartProp(t2, sel)

        # do any status only changes, eg stranding by tide
        # eg total water depth used for tidal stranding must be up to date
        # (dry_cell_index, status_frozen, status_stranded ,status_moving, sel, status)
        solver_util.tidal_stranding_from_dry_cell_index(
                                           grid['dry_cell_index'],
                                           part_prop['n_cell'].data,
                                           si.particle_status_flags['frozen'],
                                           si.particle_status_flags['stranded_by_tide'],
                                           si.particle_status_flags['moving'],
                                           sel,
                                           part_prop['status'].data)

        self.code_timer.stop('post_step_bookeeping')



    def screen_output(self,n_steps, nt0, nb0,  nb,  ns, t1, t0_step):

        si= self.shared_info
        fraction_done= abs((t1 -si.model_start_time) / si.model_duration)
        s = '%02.0f%%:' % (100* fraction_done)
        s += '%06.0f:' % n_steps + 'h%06.0f:' % (nt0+nb-nb0) + 's%02.0f:' % ns + 'b%03.0f:' % nb

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
                t0 = perf_counter()
                s.update(time=t)
                s.update_timer(t0)

        self.code_timer.stop('on_the_fly_statistics')

    def _update_concentrations(self, nb, t):
        # update triangle concentrations
        si = self.shared_info
        self.code_timer.start('particle_concentrations')
        for s in si.class_interators_using_name['particle_concentrations']['all'].values():
            if abs(t - s.info['time_last_stats_recorded']) >= s.params['calculation_interval']:
                t0 = perf_counter()
                s.update(nb, t)
                s.update_timer(t0)
        self.code_timer.stop('particle_concentrations')

    def _update_events(self, t):
        # write events
        si = self.shared_info

        self.code_timer.start('event_logging')
        for e in si.class_interators_using_name['event_loggers']['all'].values():
            t0 = perf_counter()
            e.update(time=t)
            e.update_timer(t0)
        self.code_timer.stop('event_logging')

    def close(self):
        a=1



