import numpy as np
from time import perf_counter
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.particle_properties.util import particle_operations_util
from copy import deepcopy
from  oceantracker.particle_group_manager.util import  pgm_util
from oceantracker.shared_info import shared_info as si
from oceantracker.particle_properties._base_particle_properties import FieldParticleProperty,ManuallyUpdatedParticleProperty,CustomParticleProperty

class ParticleGroupManager(ParameterBaseClass):
    '''
    holds and provides access to different types a  particle properties, eg position, field properties, custom properties
    manages particle buffers size, periodically culls dead particles
    '''
    def __init__(self):
        # set up info/attributes
        super().__init__()  # requir+ed in children to get parent defaults

        # set up pointer dict and lists
        self.status_flags= si.particle_status_flags

    def add_required_classes_and_settings(self):
        info = self.info
        nDim = si.run_info.vector_components

        # core particle props. , write at each required time step
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='x',
                     vector_dim=nDim)  # particle location
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='x0', write=True,
                     time_varying=False, vector_dim=nDim)  # location when last moving

        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='x_last_good',
                     write=False, vector_dim=nDim)  # location when last moving

        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='velocity_modifier',
                     vector_dim=nDim)

        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='status', dtype='int8', )

        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='age', initial_value=0.,
                     units='seconds', description='Time in seconds since particle released')

        # parameters are set once and then don't change with time
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='ID', dtype='int32',
                     initial_value=-1, time_varying=False,
                     description='unique particle ID number, zero based')
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='IDrelease_group',
                     dtype='int32', initial_value=-1, time_varying=False,
                     description='ID of group release particle is part of  is in, zero based')
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='user_release_groupID',
                     dtype='int32', initial_value=-1, time_varying=False,
                     description='user given integer ID of release group')
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='IDpulse', dtype='int32',
                     initial_value=-1, time_varying=False,
                     description='ID of pulse particle was released within its release group, zero based')
        # ID used when nested grids only
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='hydro_model_gridID',
                     write=True, time_varying=True, dtype='int8', initial_value=-1,
                     description='ID for which grid, outer (ID=0) or nested (ID >0),  each particle resides in ')
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='time_released',
                     time_varying=False,
                     units='seconds since 1970-01-01 00:00:00',
                     description='time (sec) each particle was released')

        #  time dependent core  properties
        si.add_class('time_varying_info', name='time',
                     units='seconds since 1970-01-01 00:00:00',
                     description='time in seconds, since 1/1/1970')  # time has only one value at each time step
        si.add_class('time_varying_info', name='num_part_released_so_far',
                     description='number of particles released up to the given time',
                     dtype='int32')  # time has only one value at each time step

    def initial_setup(self):
        info=self.info
        # is data 3D
        si.particles_in_buffer = 0

        info['num_alive'] = 0
        info['particles_released'] = 0

        info['current_particle_buffer_size'] = si.settings.particle_buffer_initial_size
        self.status_count_array_per_thread= np.zeros((si.settings.processors, 256), np.int32) # array to insert status counts for a

        info['current_status_counts'] = {}
        for name, val,  in si.particle_status_flags.asdict().items():
            info['current_status_counts'][name] = 0

        si.run_info.particle_counts['current_status_counts'] = info['current_status_counts']

        # only record bad totals to avoid overflow
        info['total_bad_status_counts'] = {key :  0 for key  in  ['cell_search_failed','bad_coord','outside_domain']}
        si.run_info.particle_counts['total_bad_status_counts'] = info['total_bad_status_counts']

    #@function_profiler(__name__)
    def release_particles(self,n_time_step, time_sec):
        # see if any group is ready to release

        part_prop = si.class_roles.particle_properties
        new_buffer_indices = np.full((0,), 0, np.int32)

        for name, rg in si.class_roles.release_groups.items():
            if rg.schedulers['release'].do_task(n_time_step):
                release_part_prop = rg.get_release_locations(time_sec)
                new_index = self.release_a_particle_group_pulse(release_part_prop, time_sec)
                new_buffer_indices = np.concatenate((new_buffer_indices,new_index), dtype=np.int32)

        # aviod calling numba code with nothing to do
        if new_buffer_indices.size==0 : return new_buffer_indices  # no releases shedulued

        # initial values  part prop derived from fields
        for name, i  in part_prop.items():
            if isinstance(i, FieldParticleProperty) :
                i.initial_value_at_birth(new_buffer_indices)

        # give user/custom prop their initial values at birth, eg zero distance, these may require interp that is setup above
        for name, i  in part_prop.items():
            if isinstance(i,CustomParticleProperty):
                i.initial_value_at_birth(new_buffer_indices)

        # update new particles props
        # todo does this update_PartProp have to be here as setup_interp_time_step and update_PartProp are run immediately after this in pre step bookkeeping ?
        self.update_PartProp(n_time_step, time_sec, new_buffer_indices)
        return new_buffer_indices #indices of all new particles

    def release_a_particle_group_pulse(self, release_data, time_sec):
        # release one pulse of particles from given group
        info= self.info
        # check if buffer needs expanding
        smax = si.particles_in_buffer + release_data['x'].shape[0]
        if smax > si.settings['max_particles']: return # no more can be released

        if smax > self.info['current_particle_buffer_size']:
            self._expand_particle_buffers(smax)

        # get indices within particle buffer where new particles will go, as in compact mode particle ID is not the buffer index
        new_buffer_indices= np.arange(si.particles_in_buffer, smax).astype(np.int32)  # indices of particles IN BUFFER to add ( zero base)
        num_released = new_buffer_indices.shape[0]

        part_prop = si.class_roles.particle_properties

        # copy over release data to new part props
        for name in release_data.keys():
            part_prop[name].set_values(release_data[name], new_buffer_indices)

        # record needed copies
        if new_buffer_indices.size >0:
            part_prop['x0'].set_values(release_data['x'], new_buffer_indices)
            part_prop['x_last_good'].set_values(release_data['x'], new_buffer_indices)
            part_prop['n_cell_last_good'].set_values(release_data['n_cell'], new_buffer_indices)
            part_prop['status'].set_values(si.particle_status_flags.moving, new_buffer_indices)  # set  status of released particles
            part_prop['time_released'].set_values(time_sec, new_buffer_indices)  # time released for each particle, needed to calculate age
            part_prop['ID'].set_values(info['particles_released'] + np.arange(num_released), new_buffer_indices)

        # set interp memory properties if present
        info['particles_released'] += num_released # total released
        si.particles_in_buffer += num_released # number in particle buffer
        info['particles_in_buffer'] = si.particles_in_buffer
        return new_buffer_indices

    def _expand_particle_buffers(self,num_particles):
        info = self.info
        part_prop = si.class_roles.particle_properties
        # get number of chunks required rounded up
        n_chunks = max(1,int(np.ceil(num_particles/si.settings.particle_buffer_initial_size)))
        info['current_particle_buffer_size'] = n_chunks*si.settings.particle_buffer_initial_size
        num_in_buffer = si.particles_in_buffer

        #print('xxy',num_particles,n_chunks,num_in_buffer,info['current_particle_buffer_size'])
        # copy property data
        for key, i in part_prop.items():
            #debug_util.print_referers(i.data,tag=key)
            s= list(i.data.shape)
            s[0] = info['current_particle_buffer_size']
            old_data = i.data
            new_data = np.zeros(s, dtype=old_data.dtype) # the new buffer
            np.copyto(new_data[:num_in_buffer, ...], old_data[:num_in_buffer, ...])
            i.data = new_data

        si.msg_logger.msg(f'Expanded particle property and index buffers to hold = {info["current_particle_buffer_size"]:4,d} particles', tabs=1)

    #@function_profiler(__name__)
    def update_PartProp(self,n_time_step, time_sec, active):
        # updates particle properties which can be updated automatically. ie those derive from reader fields or custom prop. using .update() method
        t0 = perf_counter()
        cr = si.class_roles
        cr.time_varying_info['time'].set_values(time_sec)
        cr.time_varying_info['num_part_released_so_far'].set_values(self.info['particles_released'])
        part_prop =cr.particle_properties

        #  calculate age core particle property = t-time_released
        particle_operations_util.set_value_and_add(part_prop['age'].used_buffer(), time_sec,
                                                   part_prop['time_released'].used_buffer(), active, scale= -1.)

        # first interpolate to give particle properties from reader derived  fields
        for name,i in cr.particle_properties.items():
            if isinstance(i, FieldParticleProperty):
                i.start_update_timer()
                i.update(n_time_step, time_sec, active)
                i.stop_update_timer()

        # user/custom particle prop are updated after reader based prop. , as reader prop.  may be need for their update
        for name, i in cr.particle_properties.items():
            if isinstance(i, CustomParticleProperty):
                i.start_update_timer()
                i.update(n_time_step, time_sec, active)
                i.stop_update_timer()
        si.block_timer('Update particle properties',t0)

    def find_alive_particles(self):
        status = si.class_roles.particle_properties['status'].data[:si.particles_in_buffer]
        alive = pgm_util._find_status_alive(status, self.get_partID_buffer('aliveIDs'))
        return alive
    def find_moving_particles(self):
        status = si.class_roles.particle_properties['status'].data[:si.particles_in_buffer]
        moving = pgm_util._find_status_moving(status, self.get_partID_buffer('movingIDs'))
        return moving

    def status_counts_and_kill_old_particles(self, t):
        # deactivate old particles for each release group
        part_prop = si.class_roles.particle_properties
        info = self.info
        info['num_alive_last_time_step'] =  info['num_alive']
        num_alive = pgm_util._status_counts_and_kill_old_particles(part_prop['age'].data,
                                                                   part_prop['status'].data,
                                                                   part_prop['IDrelease_group'].data,
                                                                   info['max_age_for_each_release_group'],
                                                                   self.status_count_array_per_thread,
                                                                   si.particles_in_buffer)
        pc = si.run_info.particle_counts
        pc['num_alive'] = num_alive
        pc['particles_in_buffer'] = si.particles_in_buffer
        pc['particles_released']  = info['particles_released']

        # transfer stats counts from array to run_info dict
        for key, val in si.particle_status_flags.asdict().items():
            pc['current_status_counts'][key] = self.status_count_array_per_thread[:, 128 + val].sum(axis=0)

        for key, item in pc['total_bad_status_counts'].items():
            item += pc['current_status_counts'][key]


        return num_alive

    def remove_dead_particles_from_memory(self, num_alive):
        # in comapct mode, if too many   dead particles remove then from buffer
        info = self.info

        nDead = si.particles_in_buffer - num_alive

        # kill if fraction of buffer are dead or > 20% active particles are, only if buffer at least 25% full
        if nDead > 100_000 and nDead >= 0.20* si.particles_in_buffer:
                # if too many dead then delete from memory
                part_prop = si.class_roles.particle_properties
                ID_alive = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags.stationary, out=self.get_partID_buffer('B1'))
                dead_frac=100*nDead/si.particles_in_buffer
                si.msg_logger.msg(f'removing dead {nDead:6,d} particles from buffer,  {dead_frac:2.0f}% are dead', tabs=3)

                # only  retain alive particles in buffer
                for pp in part_prop.values():
                        pp.data[:num_alive,...] = pp.get_values(ID_alive)

                # mark remaining not released to make inactive
                notReleased = np.arange(num_alive, info['current_particle_buffer_size'])
                part_prop['status'].set_values(si.particle_status_flags.notReleased, notReleased)

                si.particles_in_buffer = num_alive # record new number in buffer

    def screen_info(self):
        #  return  info about particle numbers
        info = self.info

        pc = si.run_info.particle_counts
        counts = pc['current_status_counts']
        s =  f' Rel:{info["particles_released"]:<5,d}: '
        s += f'Active:{pc["num_alive"]:<6,d} Move:{counts["moving"]:<6,d} '
        s += f'Bottom:{counts["on_bottom"]:4d} Strand:{counts["stranded_by_tide"]:<5,d}  '
        s += f'Dead:{counts["dead"]:4d} Out:{counts["outside_open_boundary"]:4d} '
        p = int((100. * si.particles_in_buffer / si.core_class_roles.particle_group_manager.info['current_particle_buffer_size']))
        s += f'Buffer:{p:2d}% '
        return s











