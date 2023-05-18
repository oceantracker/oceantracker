import numpy as np
from numba import njit
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.particle_properties import particle_operations_util
from oceantracker.util import time_util
from oceantracker.util.profiling_util import function_profiler
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.common_info_default_param_dict_templates import particle_info
from oceantracker.util import numpy_util
# holds and provides access to different types a group of particle properties, eg position, feild properties, custom properties

class ParticleGroupManager(ParameterBaseClass):

    def __init__(self):
        # set up info/attributes
        super().__init__()  # requir+ed in children to get parent defaults
        self.add_default_params( { 'name': PVC('particle_group_manager', str) , 'max_age': PVC(10.0E10, float,min=0.)})

        # set up pointer dict and lists
        si = self.shared_info
        self.status_flags= particle_info['status_flags']
        self.known_prop_types = particle_info['known_prop_types']

    def initial_setup(self):
        si= self.shared_info

        info=self.info
        # is data 3D
        self.particles_in_buffer = 0
        self.particles_released = 0
        nDim = 3 if si.hydro_model_is3D else  2

        #  time dependent core  properties
        self.add_time_varying_info(name = 'time', description='time in seconds, since 1/1/1970') #time has only one value at each time step
        #todo put core properteis in a numpy dtype block
        # core particle props. , write at each required time step
        self.create_particle_property('manual_update',dict(name='x',  vector_dim=nDim))  # particle location
        self.create_particle_property('manual_update',dict(name='particle_velocity',  vector_dim=nDim))
        self.create_particle_property('manual_update', dict(name='velocity_modifier', vector_dim=nDim))

        self.create_particle_property('manual_update',dict(name='status', dtype=np.int8,
                                      initial_value=si.particle_status_flags['notReleased']))
        self.create_particle_property('manual_update',dict(name='age',  initial_value=0.))

        # parameters are set once and then don't change with time
        self.create_particle_property('manual_update',dict(name='ID', dtype=np.int32, initial_value=-1, time_varying= False,
                                      description='unique particle ID number, zero based'))
        self.create_particle_property('manual_update',dict(name='IDrelease_group',  dtype=np.int32, initial_value=-1, time_varying=False,
                                           description='ID of group release particle is part of  is in, zero based'))
        self.create_particle_property('manual_update',dict(name='user_release_groupID',  dtype=np.int32, initial_value=-1, time_varying= False,
                                      description='user given integer ID of release group'))
        self.create_particle_property('manual_update',dict(name='IDpulse',  dtype=np.int32, initial_value=-1, time_varying= False,
                                      description='ID of pulse particle was released within its release group, zero based'))

        self.create_particle_property('manual_update',dict(name='time_released',time_varying= False,
                                      description='time (sec) each particle was released'))
        self.create_particle_property('manual_update',dict(name='x_last_good', write=False, vector_dim=nDim))  # location when last moving
        self.create_particle_property('manual_update',dict(name='x0',  vector_dim=nDim, time_varying=False,
                                      description='initial location of each particle'))  # exact location released including any randomization

        self.status_count_array= np.zeros((256,),np.int32) # array to insert status counts for a
        self.screen_msg = ''

    def final_setup(self):
        # make a single block of memory from all particle properties
        # as numpy dtype structured array
        si = self.shared_info

        part_prop = si.classes['particle_properties']
        pp ={}
        for name,i in part_prop.items():
           pp[name] = i.data
        self.part_prop_as_structure = numpy_util.numpy_structure_from_dict(pp)

        # point property.data at new memory strcture
        for name, i in part_prop.items():
            i.data = self.part_prop_as_structure[name]

    #@function_profiler(__name__)
    def release_particles(self, time_sec):
        # see if any group is ready to release
        si = self.shared_info
        new_buffer_indices = np.full((0,), 0, np.int32)

        for g in si.classes['particle_release_groups'].values():
            ri = g.info['release_info']
            sel =  time_sec* si.model_direction >= ri['release_times'][ri['index_of_next_release']: ] * si.model_direction# any  puleses not release
            num_pulses= np.count_nonzero(sel)
            for n in range(num_pulses):
                x0, IDrelease_group, IDpulse, user_release_groupID, n_cell_guess = g.release_locations()
                new_index = self.release_a_particle_group_pulse(time_sec, x0, IDrelease_group, IDpulse, user_release_groupID, n_cell_guess)
                new_buffer_indices = np.concatenate((new_buffer_indices,new_index),dtype=np.int32)
                ri['index_of_next_release'] += 1

        # for all new particles update cell and bc cords for new particles all at same time
        part_prop = si.classes['particle_properties']

        #todo does this setup_interp_time_step have to be here?
        si.classes['field_group_manager'].setup_time_step(time_sec, part_prop['x'].data, new_buffer_indices)  # new time is at end of sub step fraction =1

        # initial values  part prop derived from fields
        for name, i  in si.classes['particle_properties'].items():
            if i.info['prop_type'] =='from_fields':
                i.initial_value_at_birth(new_buffer_indices)

        # give user/custom prop their initial values at birth, eg zero distance, these may require interp that is setup above
        for name, i  in si.classes['particle_properties'].items():
            if i.info['prop_type'] == 'user':
                i.initial_value_at_birth(new_buffer_indices)

        # update new particles props
        # todo does this update_PartProp have to be here as setup_interp_time_step and update_PartProp are run immediately after this in pre step bookkeeping ?
        self.update_PartProp(time_sec, new_buffer_indices)

        # flag if any bad initial locations
        if si.settings['open_boundary_type'] > 0:
            bad = part_prop['status'].find_subset_where(new_buffer_indices, 'lt', si.particle_status_flags['outside_open_boundary'], out=self.get_particle_index_buffer())
        else:
            bad = part_prop['status'].find_subset_where(new_buffer_indices, 'lt', si.particle_status_flags['frozen'], out=self.get_particle_index_buffer())

        if bad.shape[0] > 0:
            si.msg_logger.msg(str(bad.shape[0]) + ' initial locations are outside grid domain, or NaN, or outside due to random selection of locations outside domain',warning=True)
            si.msg_logger.msgg(' Status of bad initial locations' + str(part_prop['status'].get_values(bad)),warning=True)
        return new_buffer_indices #indices of all new particles

    def release_a_particle_group_pulse(self, t, x0, IDrelease_group, IDpulse, user_release_groupID, n_cell_guess):
        # release one pulse of particles from given group
        si = self.shared_info

        info= self.info

        smax = self.particles_in_buffer + x0.shape[0]

        if smax >= si.particle_buffer_size:
            self.screen_msg += '; Out of particle buffer'
            si.msg_logger.msg('Ran out of particle buffer- no more releases, increase parameter "particle_buffer_size", size=' \
                               + str(si.particle_buffer_size) +' at ' + time_util.seconds_to_isostr(t), warning=True)
            return  np.full((0,),0)# return if no more space

        # get indices within particle buffer where new particles will go, as in compact mode particle ID is not the buffer index
        new_buffer_indices= np.arange(self.particles_in_buffer, smax).astype(np.int32)  # indices of particles IN BUFFER to add ( zero base)
        num_released = new_buffer_indices.shape[0]

        # before doing manual up dates, ensure initial values are set for
        # manually updated particle prop, so their initial value is correct,
        # as in compact mode cant rely on initial value set at array creation, due to re use of buffer
        # important for prop, for which initial values is meaning full, eg polygon events writer, where initial -1 means in no polygon

        for name, i in si.classes['particle_properties'].items():  # catch any not manually updated with their initial value
            if i.info['prop_type'] == 'manual_update':
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

        part_prop['ID'].set_values(self.particles_released + np.arange(num_released), new_buffer_indices)

        part_prop['user_release_groupID'].set_values(user_release_groupID, new_buffer_indices)  # ID of release location
        part_prop['IDrelease_group'].set_values(IDrelease_group, new_buffer_indices)  # ID of release location
        part_prop['IDpulse'].set_values(IDpulse, new_buffer_indices)  # gives a unique release ID, so that each pulse can be tracked

        # set interp memory properties if present
        self.particles_released  += num_released # total released
        self.particles_in_buffer += num_released # number in particle buffer
        return new_buffer_indices

    def add_time_varying_info(self,**kwargs):
        # property for group of particles, ie not properties of individual particles, eg time, number released
        # **karwgs must have at least name
        params = kwargs
        params['class_name'] = 'oceantracker.particle_properties._base_properties.TimeVaryingInfo'
        si = self.shared_info
        i = si.create_class_instance_as_interator('time_varying_info', 'manual_update', params, crumbs=' setup time varing reader info')
        i.initial_setup()

        if si.write_tracks and i.params['write']:
            w = si.classes['tracks_writer']
            w.create_variable_to_write(i.params['name'], 'time', None,i.params['vector_dim'], attributes_dict=None, dtype=i.params['dtype'] )

    def create_particle_property(self,prop_type, prop_params, crumbs=''):
        si = self.shared_info

        if type(prop_type) != str or type(prop_params) !=dict:
            #todo move all raise exception to msglogger
            raise Exception('ParticleGroupManager.create_particle_property, must be create_particle_property(prop_type(str), prop_params(dict))' )
        if prop_type not in self.known_prop_types:
            Exception('Create_particle_property: type is "' + prop_type + '", must be one of ' + str(self.known_prop_types))

        # set default class
        if 'class_name' not in prop_params: prop_params['class_name'] = 'oceantracker.particle_properties._base_properties.ParticleProperty'
        i = si.create_class_instance_as_interator('particle_properties', prop_type, prop_params,
                                                  crumbs=crumbs +' adding "particle_properties" name= "' + str(prop_params['name']) + '" of type=' +   prop_type)
        i.initial_setup()
        i.info['prop_type'] = prop_type
        name = i.params['name']
        if si.write_tracks:
            # tweak write flag if in param lists
            w = si.classes['tracks_writer']
            if name in w.params['turn_off_write_particle_properties_list']: i.params['write'] = False
            if name in w.params['turn_on_write_particle_properties_list']:  i.params['write'] = True
            if i.params['write']:
                w.create_variable_to_write(i.params['name'], is_time_varying=i.params['time_varying'],
                                           is_part_prop=True,
                                           vector_dim=i.params['vector_dim'],
                                           attributes_dict={'description': i.params['description']},
                                           dtype=i.params['dtype'])

    def get_particle_time(self): return self.time_varying_group_info['time'].get_values()

    #@function_profiler(__name__)
    def update_PartProp(self, t, active):
        # updates particle properties which can be updated automatically. ie those derive from reader fields or custom prop. using .update() method
        si = self.shared_info
        si.classes['time_varying_info']['time'].set_values(t)
        part_prop =si.classes['particle_properties']

        self.screen_msg= ''
        #  calculate age particle property = t-time_released
        particle_operations_util.set_value_and_add(part_prop['age'].used_buffer(), t,
                                                   part_prop['time_released'].used_buffer(), active, scale= -1.)

        # first interpolate to give particle properties from reader derived  fields
        for key,i in si.classes['particle_properties'].items():
            if i.info['prop_type'] == 'from_fields':
                si.classes['field_group_manager'].interp_named_field_at_particle_locations(key, active)

        # user/custom particle prop are updated after reader based prop. , as reader prop.  may be need for their update
        for key, i in si.classes['particle_properties'].items():
            if i.info['prop_type'] == 'user':
                i.update(active)


    def kill_old_particles(self, t):
        # deactivate old particles for each release group
        si = self.shared_info
        part_prop = si.classes['particle_properties']

        for n,p in enumerate(si.classes['particle_release_groups'].values()):

            if p.params['maximum_age'] is not None:

                in_group = part_prop['IDrelease_group'].compare_all_to_a_value('eq', n, out=self.get_particle_index_buffer())

                if in_group.shape[0] > 0:

                    if si.backtracking:
                        sel = part_prop['age'].find_subset_where(in_group, 'lt', -abs(p.params['maximum_age']), out=self.get_particle_subset_buffer())
                    else:
                        sel = part_prop['age'].find_subset_where(in_group, 'gt', abs(p.params['maximum_age']), out=self.get_particle_subset_buffer())

                    part_prop['status'].set_values(si.particle_status_flags['dead'], sel)
                    if not si.retain_culled_part_locations:
                        part_prop['x'].set_values(np.nan, sel)

    def remove_dead_particles_from_memory(self):
        # in comapct mode, if too many   dead particles remove then from buffer
        si= self.shared_info
        part_prop = si.classes['particle_properties']


        ID_alive = part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags['frozen'], out=self.get_particle_index_buffer())
        num_active = ID_alive.shape[0]
        nDead = self.particles_in_buffer - num_active

        # kill if fraction of buffer are dead or > 15% active particles are, only if buffer at least 25% full
        if nDead > 0 and self.particles_in_buffer > 0.25*si.particle_buffer_size:
            if  nDead >= 0.15*num_active  or self.particles_in_buffer > 0.9*si.particle_buffer_size:
                # if too many dead then delete from memory
                si.msg_logger.msg('removing dead ' + str(nDead)
                                        +' particles from memory, as more than 15% are dead or buffer 90% full', tabs=3)

                # only  retain alive particles in buffer
                for pp in part_prop.values():
                        pp.data[:num_active,...] = pp.get_values(ID_alive)

                # mark remaining not released to make inactive
                notReleased = np.arange(num_active, si.particle_buffer_size)
                part_prop['status'].set_values(si.particle_status_flags['notReleased'], notReleased)

                self.particles_in_buffer = num_active # record new number in buffer



    def get_release_group_userIDmaps(self):
        # make dict masp from userId and user_release_group_name to sequence number
        releaseGroups_user_maps = {'particle_release_userRelease_groupID_map': {} , 'particle_release_user_release_group_name_map': {}}

        #todo use i.info['nsequence'] for rg id
        for n, i in enumerate(self.shared_info.classes['particle_release_groups'].values()):
            releaseGroups_user_maps['particle_release_userRelease_groupID_map'][str(i.params['user_release_groupID'])] = n
            releaseGroups_user_maps['particle_release_user_release_group_name_map'][str(i.params['user_release_group_name'])] = n

        return releaseGroups_user_maps

    # below return  info about particle group
    #__________________________________

    def status_counts(self):
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        count_array = self.status_count_array
        self._do_status_counts(part_prop['status'].used_buffer(), count_array)


        # put numba counts back in dict with proper names
        counts={'active': 0}
        for name, val in si.particle_status_flags.items():
            c= count_array[val + 128]
            counts[name] = c
            counts['active'] += c
        return counts

    @staticmethod
    @njit
    ##@njit(nbtypes.int32[:](nbtypes.int8[:],nbtypes.int32[:]))
    def _do_status_counts(status, status_counts):
        # do count into array of all possible status values -128 <= val <= 127
        for m in range(status_counts.size): status_counts[m] = 0
        for n in range(status.shape[0]):
            status_counts[status[n]-128] += 1


    def screen_info(self):
        si = self.shared_info
        counts =self.status_counts()
        s =  ' Rel.:%06.0f' % self.particles_released
        s += ': Active:%05.0f' % counts['active'] + ' M:%05.0f' % counts['moving']
        s += ' S:%05.0f' % counts['stranded_by_tide'] + ' B:%05.0f' % counts['on_bottom'] + ' D:%03.0f' % counts['dead']
        s += ' O:%02.0f' % counts['outside_open_boundary'] + ' N:%01.0f' % counts['bad_cord']
        s += ' Buffer:%4.0f' %  self.particles_in_buffer
        s += '-%3.0f%%' % (100. * self.particles_in_buffer / si.particle_buffer_size)
        s += self.screen_msg
        return s


    def  create_particle_prop_memory_block(self):
        # todo create_particle_prop_memory_block is development work
        si=self.shared_info

        # get all names sizes and dtypes of all particle properties
        array_types=[]
        for name,prop in si.classes['particle_properties'].items():

            if prop.params['vector_dim'] > 1:
                s = (prop.params['vector_dim'],)
            else:
                s = (1,)

            # third matrix dim, so far only used recording vertical cell at each node  3D for 2 time steps
            if prop.params['prop_dim3'] > 0 and prop.params['prop_dim3'] > 1:
                s += (prop.params['prop_dim3'],)

            array_types.append((name,prop.params['dtype'],s  ))

        # make array of sub arrays with all properties stored next to each other in memory
        #todo this is in development
        #self.particle_prop_memory_block = np.full((si.particle_buffer_size,),0,dtype=array_types)

        # make pointer from each variable to its named block/sub array
        for name, prop in si.classes['particle_properties'].items():
            prop.data=self.particle_prop_memory_block[name]

            # make pointer to data without any trailing unit dimension to be compatible with numba particle operations on 1D  vectors
            if prop.data.size > 1 and prop.data.shape[-1] == 1:
                prop.data = prop.data.reshape(prop.data.shape[:-1])

            prop.data[:] = prop.params['initial_value']

        si.particle_prop_memory_block= self.particle_prop_memory_block









