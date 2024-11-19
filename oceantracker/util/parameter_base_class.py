from  oceantracker.util import basic_util
import numpy as np
import traceback
from time import perf_counter
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.shared_info import shared_info as si
# root class needed to avoid circular imports when building class trees
from .__root_parameter_base_class__ import _RootParameterBaseClass
from oceantracker.util.scheduler import Scheduler

class ParameterBaseClass(_RootParameterBaseClass):
    # parameter dictionaries are nested dictionaries or lists of dictionaries
    # object with default parameters as class dictionary, that are checked against expections
    # philosophy is that
    # 1) is that all the options that can be tweaked on an object are parameters, with defaults
    # 2) a class where defaults are checked against expectation
    # 3) parameter are merged merge_with_class_defaults at run time
    # 4) the terminal value in a default dic must be an instance of   ParamDictValueChecker
    # 5)  ParamDictValueChecker checks give value against expectation or inserts default
    # 6) Defaults must be set in .__init__()  using method ._update_default_param_dictionary({})
    # 7) children must call   super().__init__()   to get defaults of parent



    def initial_setup(self): pass

    def close(self):  pass

    def __init__(self):

        self.params={}
        self.info={'instanceID':0,
                    'time_spent_updating': 0.,
                   'update_calls': 0,
                   'time_first_update_call':0.}  # stores info about object

        self.docs={'description': None, 'role': None # role is only set in base class
                   }
        self.default_params={}
        self.add_default_params(class_name = PVC(None,str, doc_str='Class name as string A.B.C, used to import this class from python path'),
                                  user_note = PVC(None, str),
                                 name = PVC(None, str,doc_str='Name used to refer to class in code and output, = None for core claseses'),
                                 development = PVC(False, bool, expert=True,doc_str='Class is under development and testing'),
                                  )

        self.partID_buffers={} # dict of int32 ID number buffers
        self.shared_info = None
        self.schedulers ={}


    def add_required_classes_and_settings(self, settings, reader_builder, message_logger):
        # this adds classes required by this a class using si.add_class.
        # reader/custom fields are  added with field group manager methods
        pass



    def final_setup(self):
        # setup done after all other classes have intitial_setup, ie things that depend on settingas of othe classes
        # eg particle buffer size
        pass

    def add_default_params(self,*args, **kwargs):
        # add default as key word or dictionary
        if len(args) == 1 and len(kwargs) == 0:
            d = args[0]
        elif len(args) == 0:
            d = kwargs
        else:
            raise(f'Parameter class> add_default_params >> only one arg or kkwano default dict or kwargs given args = {str(args)} kwargs={str(kwargs)}')

        if type(d) is not dict: raise ValueError('add_default_params : default param must be a dictionary')
        # deep update to defaults
        basic_util.deep_dict_update(self.default_params, d)

    def role_doc(self,role):
        self.docs['role'] = role  # only in base class


    def check_requirements(self):
        self.check_class_required_fields_prop_etc()


    def check_class_required_fields_prop_etc(self, required_props_list=[],
                                             requires3D=None, crumbs=''):
        si = self.shared_info
        for name in required_props_list:
            if name not in si.class_roles.particle_properties:
                si.msg_logger.msg('     class ' + self.params['class_name'] + ', particle property "' + self.params['name']
                                + '" requires particle property  "' + name + '"'
                                + ' to work, add to reader["field_variables"], or add to fields param list, or add to particle_properties', fatal_error=True,crumbs=crumbs)

        if requires3D and not si.run_info.is3D_run:
                si.msg_logger.msg('     class ' + self.params['class_name'] + ', ' + self.params['name'] + ' can only be used with 3D hindcast ', fatal_error=True,crumbs=crumbs)

    def remove_default_params(self, name_list):
        # used to get rid if paramters of parent class which are not used by a child class
        for key in name_list:
            if key in self.default_params:
                del self.default_params[key]

    def clear_default_params(self, name_list):
        # used to clear all defaults when not needed
        for key in name_list:
            self.default_params[key] ={}

    # below dynamical adds shared particle index buffers when first used within in a class instance
    # buffers are used to hold selections of particles, saving memory and time by reuse
    # use with care as returned view may refer to same buffer!!

    def get_partID_buffer(self, name):
        # creates, expands and provides access to particle ID number buffers of this class
        # having these buffers aviods creating new memory every time
        #  a selection of particle IDs is made, eg status == moving
        # WARNING never refer directly to the partID_buffers, alawys use this method
        #         to access buffer, as buffer size is dynamically changing
        current_particle_buffer_size = si.core_class_roles.particle_group_manager.info['current_particle_buffer_size']

        if name not in self.partID_buffers:
            # create a new ID buffer
            self.partID_buffers[name] = np.full((current_particle_buffer_size,), -127, dtype=np.int32)

        elif self.partID_buffers[name].size < current_particle_buffer_size:
            # particle buffer must have increased so enlarge ID buffer to match
            new_index = np.zeros((current_particle_buffer_size,), dtype=np.int32)
            np.copyto(new_index[:self.partID_buffers[name].size], self.partID_buffers[name])
            self.partID_buffers[name] = new_index

        return self.partID_buffers[name] # return, new, expanded or existing buffer

    def get_partID_subset_buffer(self, name):
        # wrapper to help ensure a subset ID buffer is not the same as main buffer
        return self.get_partID_buffer(name +'_subset')

    def start_update_timer(self): self.update_timer_t0 = perf_counter()

    def stop_update_timer(self):
        dt= perf_counter() -  self.update_timer_t0
        self.info['time_spent_updating'] += dt
        self.info['update_calls'] += 1

        # note effect of any numba compilation on first call
        if self.info['update_calls'] == 1: self.info['time_first_update_call'] = dt

    def add_scheduler(self, name_scheduler :str, start=None, end=None, duration=None,
                                   interval =None, times=None,  caller=None, crumbs=''):
        ''' Add a scheduler object to given param_class_instance, with boolean task_flag attribute for each time step,
            which is true if  task is to be carried out.
            Rounds times interval and times to nearest time step'''
        s = Scheduler(si.settings, si.run_info, start=start, end=end, duration=duration,
                                                    interval =interval, times=times, caller=caller,
                                                    msg_logger=si.msg_logger, crumbs=crumbs + f'> adding scheduler {name_scheduler}')
        self.schedulers[name_scheduler]  = s
        return s
