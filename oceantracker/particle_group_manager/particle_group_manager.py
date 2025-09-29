import numpy as np
from time import perf_counter
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.numba_util import njitOT, prange, njitOTparallel

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

        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='status', dtype='int8' )
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='status_last_good', dtype='int8', )

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
        si.run_info.particles_in_buffer = 0

        info['num_alive'] = 0
        info['particles_released'] = 0

        info['current_particle_buffer_size'] = si.settings.particle_buffer_initial_size
        self.status_count_array_per_thread= np.zeros((si.settings.processors, 256), np.int32) # array to insert status counts for a

        info['current_status_counts'] = {}
        for name, val,  in si.particle_status_flags.items():
            info['current_status_counts'][name] = 0

        si.run_info.particle_counts['current_status_counts'] = info['current_status_counts']

    def release_particles(self,n_time_step, time_sec):
        # see if any group is ready to release

        part_prop = si.class_roles.particle_properties
        new_buffer_index = np.full((0,), 0, np.int32)

        for name, rg in si.class_roles.release_groups.items():
            if rg.schedulers['release'].do_task(n_time_step):
                rg.start_update_timer()
                release_part_prop = rg.get_release_locations(time_sec)
                index = self.release_a_particle_group_pulse(release_part_prop, time_sec)
                new_buffer_index = np.concatenate((new_buffer_index,index), dtype=np.int32)
                rg.stop_update_timer()

        # aviod calling numba code with nothing to do
        if new_buffer_index.size==0 : return new_buffer_index  # no releases shedulued

        # initial values  part prop derived from fields
        for name, i  in part_prop.items():
            if isinstance(i, FieldParticleProperty) :
                i.initial_value_at_birth(new_buffer_index)

        # give user/custom prop their initial values at birth, eg zero distance, these may require interp that is setup above
        for name, i  in part_prop.items():
            if isinstance(i,CustomParticleProperty):
                i.initial_value_at_birth(new_buffer_index)

        # update new particles props, after finding hori and vert cell, first update hori and vert cell
        si.core_class_roles.field_group_manager.setup_time_step(time_sec, part_prop['x'].data, new_buffer_index)
        self.update_PartProp(n_time_step, time_sec, new_buffer_index)

        return new_buffer_index #indices of all new particles

    def release_a_particle_group_pulse(self, release_data, time_sec):
        # release one pulse of particles from given group
        info= self.info
        # check if buffer needs expanding
        smax = si.run_info.particles_in_buffer + release_data['x'].shape[0]
        if smax > si.settings.max_particles: return # no more can be released

        if smax > self.info['current_particle_buffer_size']:
            self._expand_particle_buffers(smax)

        # get indices within particle buffer where new particles will go, as in compact mode particle ID is not the buffer index
        new_part_buffer_indices = np.arange(si.run_info.particles_in_buffer, smax).astype(np.int32)  # indices of particles IN BUFFER to add ( zero base)
        num_released = new_part_buffer_indices.size

        part_prop = si.class_roles.particle_properties

        # copy over release data to new part props
        for name in release_data.keys():
            part_prop[name].set_values(release_data[name], new_part_buffer_indices)

        # record needed copies
        if new_part_buffer_indices.size >0:
            part_prop['x0'].set_values(release_data['x'], new_part_buffer_indices)
            part_prop['x_last_good'].set_values(release_data['x'], new_part_buffer_indices)
            part_prop['n_cell_last_good'].set_values(release_data['n_cell'], new_part_buffer_indices)
            part_prop['status'].set_values(si.particle_status_flags.moving, new_part_buffer_indices)  # set  status of released particles
            part_prop['status_last_good'].set_values(si.particle_status_flags.moving, new_part_buffer_indices)  # set  status of released particles
            part_prop['time_released'].set_values(time_sec, new_part_buffer_indices)  # time released for each particle, needed to calculate age
            part_prop['ID'].set_values(info['particles_released'] + np.arange(num_released), new_part_buffer_indices)

        info['particles_released'] += num_released  # total released
        si.run_info.particles_in_buffer += num_released  # number in particle buffer


        return new_part_buffer_indices

    def _expand_particle_buffers(self,num_particles):
        info = self.info
        part_prop = si.class_roles.particle_properties
        # get number of chunks required rounded up
        n_chunks = max(1,int(np.ceil(num_particles/si.settings.particle_buffer_initial_size)))
        info['current_particle_buffer_size'] = n_chunks*si.settings.particle_buffer_initial_size
        num_in_buffer = si.run_info.particles_in_buffer

        # copy property data
        for key, i in part_prop.items():
            #debug_util.print_referers(i.data,tag=key)
            s= list(i.data.shape)
            s[0] = info['current_particle_buffer_size']
            old_data = i.data
            new_data = np.zeros(s, dtype=old_data.dtype) # the new buffer
            np.copyto(new_data[:num_in_buffer, ...], old_data[:num_in_buffer, ...])
            i.data = new_data
            i.info['data_shape'] = i.data.shape # record new shape for debugging

        si.msg_logger.msg(f'Expanded particle property and index buffers to hold = {info["current_particle_buffer_size"]:4,d} particles', tabs=1)

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

        t0 = perf_counter()
        # first interpolate to give particle properties from reader derived  fields
        for name,i in cr.particle_properties.items():
            if isinstance(i, FieldParticleProperty):
                i.timed_update(n_time_step, time_sec, active)

        si.block_timer('Interpolate fields', t0)

        t0 = perf_counter()
        # user/custom particle prop are updated after reader based prop. , as reader prop.  may be need for their update
        for name, i in cr.particle_properties.items():
            if isinstance(i, CustomParticleProperty):
                i.timed_update(n_time_step, time_sec, active)
        si.block_timer('Update custom particle prop.',t0)


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
                                                                   si.run_info.particles_in_buffer)
        pc = si.run_info.particle_counts
        pc['num_alive'] = num_alive
        pc['particles_released']  = info['particles_released']

        # transfer stats counts from array to run_info dict
        for key, val in si.particle_status_flags.items():
            pc['current_status_counts'][key] = self.status_count_array_per_thread[:, 128 + val].sum(axis=0)

        return num_alive



    def remove_dead_particles_from_memory(self):
        # in compact  if too many   dead particles remove then from buffer
        info = self.info

        nDead = si.run_info.particle_counts['current_status_counts']['dead']

        # kill if fraction of buffer are dead or > 20% active particles are, only if buffer at least 25% full
        if nDead > si.settings.min_dead_to_remove and nDead >= 0.20 * si.run_info.particles_in_buffer:
                # if too many dead then delete from memory
                part_prop = si.class_roles.particle_properties
                ID_alive = part_prop['status'].compare_all_to_a_value('gt', si.particle_status_flags.dead, out=self.get_partID_buffer('B1'))
                nDead = si.run_info.particles_in_buffer-ID_alive.size # update nDead as particle counts are from start of time step, removal at the end
                dead_frac=100*nDead/si.run_info.particles_in_buffer
                si.msg_logger.msg(f'removing {dead_frac:2.0f}%  dead  = {nDead:6,d} of  {si.run_info.particles_in_buffer:6,d} particles in buffer', tabs=3)
                pass
                # only  retain alive particles in buffer
                for pp in part_prop.values():
                    pp.data[:ID_alive.size,...] = pp.get_values(ID_alive)

                # mark remaining not released to make inactive
                notReleased = np.arange(ID_alive.size, info['current_particle_buffer_size'])
                part_prop['status'].set_values(si.particle_status_flags.notReleased, notReleased)

                si.run_info.particles_in_buffer = ID_alive.size # record new number in buffer
    @staticmethod
    @njitOT
    def _pack_particle_buffer(data, cull):
        pass


    def screen_info(self):
        #  return  info about particle numbers
        info = self.info

        pc = si.run_info.particle_counts
        counts = pc['current_status_counts']
        s =  f' Rel:{info["particles_released"]:<5,d}: '
        s += f'Active:{pc["num_alive"]:<6,d} Move:{counts["moving"]:<6,d} '
        s += f'Bottom:{counts["on_bottom"]:<5,d} Strand:{counts["stranded_by_tide"]:<5,d}  '
        s += f'Dead:{counts["dead"]:<5,d} Out:{counts["outside_open_boundary"]:4d} '
        p = int((100. * si.run_info.particles_in_buffer / si.core_class_roles.particle_group_manager.info['current_particle_buffer_size']))
        s += f'Buffer:{p:2d}% '
        return s











