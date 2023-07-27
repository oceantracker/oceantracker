import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.particle_properties.util import particle_operations_util
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.common_info_default_param_dict_templates import particle_info
from oceantracker.util import spell_check_util
from  oceantracker.particle_group_manager.util import  pgm_util

# holds and provides access to different types a group of particle properties, eg position, feild properties, custom properties
class ParticleGroupManager(ParameterBaseClass):

    def __init__(self):
        # set up info/attributes
        super().__init__()  # requir+ed in children to get parent defaults
        self.add_default_params( { 'particle_buffer_chunk_size': PVC(500_000, int, min=1)})

        # set up pointer dict and lists
        si = self.shared_info
        self.status_flags= particle_info['status_flags']
        self.known_prop_types = particle_info['known_prop_types']

    def initial_setup(self):
        si= self.shared_info

        info=self.info
        # is data 3D
        info['particles_in_buffer'] = 0
        info['particles_released'] = 0
        info['num_alive'] = 0
        nDim = 3 if si.hydro_model_is3D else  2
        info['current_particle_buffer_size'] = self.params['particle_buffer_chunk_size']

        #  time dependent core  properties
        self.add_time_varying_info('time', description='time in seconds, since 1/1/1970') #time has only one value at each time step
        self.add_time_varying_info('num_part_released_so_far', description='number of particles released up to the given time',
                                   dtype=np.int32)  # time has only one value at each time step

        # core particle props. , write at each required time step
        self.create_particle_property('x','manual_update',dict(vector_dim=nDim))  # particle location
        self.create_particle_property('particle_velocity','manual_update',dict(vector_dim=nDim))
        self.create_particle_property('velocity_modifier','manual_update', dict(vector_dim=nDim))

        self.create_particle_property('status','manual_update',dict( dtype=np.int8,   fill_value=si.particle_status_flags['notReleased']))
        self.create_particle_property('age','manual_update',dict(  initial_value=0.))

        # parameters are set once and then don't change with time
        self.create_particle_property('ID','manual_update',dict( dtype=np.int32, initial_value=-1, time_varying= False,
                                      description='unique particle ID number, zero based'))
        self.create_particle_property('IDrelease_group', 'manual_update',dict( dtype=np.int32, initial_value=-1, time_varying=False,
                                           description='ID of group release particle is part of  is in, zero based'))
        self.create_particle_property('user_release_groupID', 'manual_update',dict( dtype=np.int32, initial_value=-1, time_varying= False,
                                      description='user given integer ID of release group'))
        self.create_particle_property('IDpulse','manual_update',dict(  dtype=np.int32, initial_value=-1, time_varying= False,
                                      description='ID of pulse particle was released within its release group, zero based'))
        self.create_particle_property('time_released', 'manual_update',dict(time_varying= False, description='time (sec) each particle was released'))
        self.create_particle_property('x_last_good','manual_update',dict( write=True, vector_dim=nDim))  # location when last moving
        self.create_particle_property('x0','manual_update',dict(  vector_dim=nDim, time_varying=False,
                                      description='initial location of each particle'))  # exact location released including any randomization

        self.status_count_array= np.zeros((256,),np.int32) # array to insert status counts for a
        self.screen_msg = ''

    def final_setup(self):
        # make a single block of memory from all particle properties
        # as numpy dtype structured array
        si = self.shared_info
        info = self.info

        # set up array with max age for each release group, for use in killing old particles
        rg = si.classes['release_groups']
        info['max_age_for_each_release_group']= np.zeros((len(rg),), dtype=np.float64)
        for n, i in enumerate(rg.values()):
            info['max_age_for_each_release_group'][n] = np.inf if i.params['max_age'] is None else i.params['max_age']

        pass


    #@function_profiler(__name__)
    def release_particles(self, time_sec):
        # see if any group is ready to release
        si = self.shared_info
        new_buffer_indices = np.full((0,), 0, np.int32)

        for name, g in si.classes['release_groups'].items():
            ri = g.info['release_info']
            sel =  time_sec * si.model_direction >= ri['release_times'][ri['index_of_next_release']: ] * si.model_direction# any  puleses not release
            num_pulses= np.count_nonzero(sel)
            for n in range(num_pulses):
                x0, IDrelease_group, IDpulse, user_release_groupID, n_cell_guess = g.release_locations()
                new_index = self.release_a_particle_group_pulse(time_sec, x0, IDrelease_group, IDpulse, user_release_groupID, n_cell_guess)
                new_buffer_indices = np.concatenate((new_buffer_indices,new_index), dtype=np.int32)
                ri['index_of_next_release'] += 1
            pass
        # for all new particles update cell and bc cords for new particles all at same time
        part_prop = si.classes['particle_properties']

        #todo does this setup_interp_time_step have to be here?
        si.classes['field_group_manager'].setup_time_step(time_sec, part_prop['x'].data, new_buffer_indices)  # new time is at end of sub step fraction =1

        # initial values  part prop derived from fields
        for name, i  in si.classes['particle_properties'].items():
            if i.info['group'] =='from_fields':
                i.initial_value_at_birth(new_buffer_indices)

        # give user/custom prop their initial values at birth, eg zero distance, these may require interp that is setup above
        for name, i  in si.classes['particle_properties'].items():
            if i.info['group'] == 'user':
                i.initial_value_at_birth(new_buffer_indices)

        # update new particles props
        # todo does this update_PartProp have to be here as setup_interp_time_step and update_PartProp are run immediately after this in pre step bookkeeping ?
        self.update_PartProp(time_sec, new_buffer_indices)

        # flag if any bad initial locations
        if si.settings['open_boundary_type'] > 0:
            bad = part_prop['status'].find_subset_where(new_buffer_indices, 'lt', si.particle_status_flags['outside_open_boundary'], out=self.get_partID_buffer('B1'))
        else:
            bad = part_prop['status'].find_subset_where(new_buffer_indices, 'lt', si.particle_status_flags['frozen'], out=self.get_partID_buffer('B1'))

        if bad.shape[0] > 0:
            si.msg_logger.msg(str(bad.shape[0]) + ' initial locations are outside grid domain, or NaN, or outside due to random selection of locations outside domain',warning=True)
            si.msg_logger.msgg(' Status of bad initial locations' + str(part_prop['status'].get_values(bad)),warning=True)
        return new_buffer_indices #indices of all new particles

    def release_a_particle_group_pulse(self, t, x0, IDrelease_group, IDpulse, user_release_groupID, n_cell_guess):
        # release one pulse of particles from given group
        si = self.shared_info

        info= self.info

        smax = info['particles_in_buffer'] + x0.shape[0]

        if smax > si.settings['max_particles']: return

        if smax >= self.info['current_particle_buffer_size']:
            self._expand_particle_buffers(smax)

        # get indices within particle buffer where new particles will go, as in compact mode particle ID is not the buffer index
        new_buffer_indices= np.arange(info['particles_in_buffer'], smax).astype(np.int32)  # indices of particles IN BUFFER to add ( zero base)
        num_released = new_buffer_indices.shape[0]

        # before doing manual updates, ensure initial values are set for
        # manually updated particle prop, so their initial value is correct,
        # as in compact mode cant rely on initial value set at array creation, due to re use of buffer
        # important for prop, for which initial values is meaning full, eg polygon events writer, where initial -1 means in no polygon

        for name, i in si.classes['particle_properties'].items():  # catch any not manually updated with their initial value
            if i.info['group'] == 'manual_update':
                i.initial_value_at_birth(new_buffer_indices)

        #  set initial conditions/properties of new particles
        # do manual_update updates
        part_prop = si.classes['particle_properties']
        part_prop['x'].set_values(x0, new_buffer_indices)
        part_prop['x_last_good'].set_values(x0, new_buffer_indices)
        part_prop['x0'].set_values(x0, new_buffer_indices)  # record exact release location including any randomisation

        part_prop['n_cell'].set_values(n_cell_guess, new_buffer_indices)  # use x0's best guess  for starting point cell

        part_prop['status'].set_values(si.particle_status_flags['moving'], new_buffer_indices)  # set  status of released particles

        # below two needed for reruns of same solver to prevent contamination by last run
        part_prop['time_released'].set_values(t, new_buffer_indices)  # time released for each particle, needed to calculate age

        part_prop['ID'].set_values(info['particles_released'] + np.arange(num_released), new_buffer_indices)

        part_prop['user_release_groupID'].set_values(user_release_groupID, new_buffer_indices)  # ID of release location
        part_prop['IDrelease_group'].set_values(IDrelease_group, new_buffer_indices)  # ID of release location
        part_prop['IDpulse'].set_values(IDpulse, new_buffer_indices)  # gives a unique release ID, so that each pulse can be tracked

        # set interp memory properties if present
        info['particles_released'] += num_released # total released
        info['particles_in_buffer'] += num_released # number in particle buffer
        return new_buffer_indices

    def _expand_particle_buffers(self,num_particles):
        si = self.shared_info
        info = self.info
        # get number of chunks required rounded up
        n_chunks = max(1,int(np.ceil(num_particles/self.params['particle_buffer_chunk_size'])))
        info['current_particle_buffer_size']  = n_chunks*self.params['particle_buffer_chunk_size']
        num_in_buffer = info['particles_in_buffer']
        #print('xxy',num_particles,n_chunks,num_in_buffer,info['current_particle_buffer_size'])
        # copy property data
        for key, i in si.classes['particle_properties'].items():
            #debug_util.print_referers(i.data,tag=key)
            s= list(i.data.shape)
            s[0] = info['current_particle_buffer_size']
            new_data = np.zeros(s, dtype=i.data.dtype) # the new buffer
            np.copyto(new_data[:num_in_buffer, ...], i.data[:num_in_buffer, ...])
            i.data = new_data

        si.msg_logger.msg(f'Expanded particle property and index buffers to hold = {info["current_particle_buffer_size"]:4,d} particles', tabs=1)

    def add_time_varying_info(self,name, **kwargs):
        # property for group of particles, ie not properties of individual particles, eg time, number released
        # **karwgs must have at least name
        params = kwargs
        params['class_name'] = 'oceantracker.particle_properties._base_properties.TimeVaryingInfo'
        si = self.shared_info
        i = si.create_class_dict_instance(name,'time_varying_info', 'manual_update', params, crumbs=' setup time varing reader info')
        i.initial_setup()

        if si.write_tracks and i.params['write']:
            w = si.classes['tracks_writer']
            w.create_variable_to_write(name, 'time', None,i.params['vector_dim'], attributes=None, dtype=i.params['dtype'] )

    def create_particle_property(self, name, prop_group, prop_params, crumbs=''):
        si = self.shared_info
        ml= si.msg_logger

        # todo make name first colpulsory argument of this function and create_class_dict_instance
        if name is None:
            ml.msg('ParticleGroupManager.create_particle_property, prop name cannot be None, must be unique str',
                   hint='got prop_type of type=' + str(type(prop_group)),
                   fatal_error=True, exit_now=True)

        if type(prop_group) != str :
            ml.msg('ParticleGroupManager.create_particle_property, prop_type must be type =str',
                   hint='got prop_type of type=' + str(type(prop_group)),
                   fatal_error=True, exit_now=True)

        if type(prop_params) != dict:
            ml.msg('ParticleGroupManager.create_particle_property, parameters must be type dict ',
                    hint= 'got parameters of type=' + str(type(prop_params)) +',  values='+str(prop_params), fatal_error=True, exit_now=True)

        if prop_group not in self.known_prop_types:    #todo move all raise exception to msglogger
            ml.msg('ParticleGroupManager.create_particle_property, unknown prop_group name',
                   hint='prop_group must be one of ' + str(self.known_prop_types),   fatal_error=True, exit_now=True)
        # set default class
        if 'class_name' not in prop_params:
            prop_params['class_name'] = 'oceantracker.particle_properties._base_properties.ParticleProperty'


        i = si.create_class_dict_instance(name, 'particle_properties', prop_group, prop_params,
                                          crumbs=crumbs +' adding "particle_properties of type=' + prop_group)
        i.initial_setup()

        if si.write_tracks:
            # tweak write flag if in param lists
            w = si.classes['tracks_writer']
            if name in w.params['turn_off_write_particle_properties_list']: i.params['write'] = False
            if name in w.params['turn_on_write_particle_properties_list']:  i.params['write'] = True
            if i.params['write']:
                w.create_variable_to_write(name, is_time_varying=i.params['time_varying'],
                                           is_part_prop=True,
                                           fill_value= i.params['fill_value'],
                                           vector_dim=i.params['vector_dim'],
                                           attributes={'description': i.params['description']},
                                           dtype=i.params['dtype'])

    def get_particle_time(self): return self.time_varying_group_info['time'].get_values()

    #@function_profiler(__name__)
    def update_PartProp(self, t, active):
        # updates particle properties which can be updated automatically. ie those derive from reader fields or custom prop. using .update() method
        si = self.shared_info
        si.classes['time_varying_info']['time'].set_values(t)
        si.classes['time_varying_info']['num_part_released_so_far'].set_values(self.info['particles_released'])
        part_prop =si.classes['particle_properties']

        self.screen_msg= ''
        #  calculate age particle property = t-time_released
        particle_operations_util.set_value_and_add(part_prop['age'].used_buffer(), t,
                                                   part_prop['time_released'].used_buffer(), active, scale= -1.)

        # first interpolate to give particle properties from reader derived  fields
        for key,i in si.classes['particle_properties'].items():
            if i.info['group'] == 'from_fields':
                si.classes['field_group_manager'].interp_named_field_at_particle_locations(key, active)

        # user/custom particle prop are updated after reader based prop. , as reader prop.  may be need for their update
        for key, i in si.classes['particle_properties'].items():
            if i.info['group'] == 'user':
                i.update(active)

    def status_counts_and_kill_old_particles(self, t,):
        # deactivate old particles for each release group
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        info = self.info

        num_alive =pgm_util._status_counts_and_kill_old_particles(part_prop['age'].data,
                                    part_prop['status'].data,
                                    part_prop['IDrelease_group'].data,
                                    info['max_age_for_each_release_group'],
                                    self.status_count_array,
                                    info['particles_in_buffer'])
        info['num_alive'] = num_alive
        return num_alive

    def remove_dead_particles_from_memory(self):
        # in comapct mode, if too many   dead particles remove then from buffer
        si= self.shared_info
        info = self.info
        part_prop = si.classes['particle_properties']

        ID_alive = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags['frozen'], out=self.get_partID_buffer('B1'))
        num_alive = ID_alive.shape[0]
        nDead = info['particles_in_buffer'] - num_alive

        # kill if fraction of buffer are dead or > 20% active particles are, only if buffer at least 25% full
        if nDead > 100_000 and nDead >= 0.20*info['particles_in_buffer']:
                # if too many dead then delete from memory
                si.msg_logger.msg(f'removing dead {nDead:,3d} particles from memory, as more than 20% are dead', tabs=3)

                # only  retain alive particles in buffer
                for pp in part_prop.values():
                        pp.data[:num_alive,...] = pp.get_values(ID_alive)

                # mark remaining not released to make inactive
                notReleased = np.arange(num_alive, si.particle_buffer_size)
                part_prop['status'].set_values(si.particle_status_flags['notReleased'], notReleased)

                info['particles_in_buffer'] = num_alive # record new number in buffer

    def get_release_group_userIDmaps(self):
        # make dict masp from userId and user_release_group_name to sequence number
        releaseGroups_user_maps = {'particle_release_userRelease_groupID_map': {} , 'particle_release_user_release_group_name_map': {}}

        #todo use i.info['nsequence'] for rg id
        for n, i in enumerate(self.shared_info.classes['release_groups'].values()):
            releaseGroups_user_maps['particle_release_userRelease_groupID_map'][str(i.params['user_release_groupID'])] = n
            releaseGroups_user_maps['particle_release_user_release_group_name_map'][str(i.params['user_release_group_name'])] = n

        return releaseGroups_user_maps

    # below return  info about particle group
    #__________________________________

    def is_particle_property(self,name, crumbs=''):
        #todo make si.classes['particle_properties'] = self.particle_properties
        si = self.shared_info
        if name in list( si.classes['particle_properties'].keys()):
            return   True
        else:
            spell_check_util.spell_check(name,list( si.classes['particle_properties'].keys()),
                                         si.msg_logger,
                                         ' particle property, ignoring', crumbs = crumbs)
            return False
    def status_counts(self):
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        count_array = self.status_count_array
        pgm_util.do_status_counts(part_prop['status'].used_buffer(), count_array)


        # put numba counts back in dict with proper names
        counts={'active': 0}
        for name, val in si.particle_status_flags.items():
            c= count_array[val + 128]
            counts[name] = c
            counts['active'] += c
        return counts


    def screen_info(self):
        si = self.shared_info
        sf= si.particle_status_flags
        info = self.info
        counts =self.status_count_array

        s =  f' Rel.:{info["particles_released"]:8,d}: '
        s += f'Active:{info["num_alive"]:05d} M:{counts[sf["moving"]-128]:05d} '
        s += f'S:{counts[sf["stranded_by_tide"]-128]:05d}  B:{counts[sf["on_bottom"]-128]:05d} '
        s += f'D:{counts[sf["dead"] - 128]:03d} O:{counts[sf["outside_open_boundary"] - 128]:02d} '
        s += f'N:{counts[sf["bad_cord"] - 128]:03d} Buffer:{info["particles_in_buffer"]:04d} '
        s += '-%3.0f%%' % (100. * info['particles_in_buffer'] / si.classes['particle_group_manager'].info['current_particle_buffer_size'])
        s += self.screen_msg
        return s











