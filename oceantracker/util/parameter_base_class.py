from  oceantracker.util import basic_util
import numpy as np
import traceback
from time import perf_counter
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, merge_params_with_defaults
from oceantracker.shared_info import SharedInfo as si
# parameter dictionaries are nested dictionaries or lists of dictionaries

class ParameterBaseClass(object):
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
        self.add_default_params({'class_name': PVC(None,str, doc_str='Class name as string A.B.C, used to import this class from python path'),
                                  'user_note': PVC(None, str),
                                 'user_instance_info': PVC(None, [str,int, float, tuple,list],doc_str='a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple'),
                                 })

        self.partID_buffers={} # dict of int32 ID number buffers
    def intitial_setup(self):
        # setup done before other classes set
        pass

    def final_setup(self):
        # setup done after all other classes have intitial_setup, ie things that depend on settingas of othe classes
        # eg particle buffer size
        pass

    def add_default_params(self,d=None):
        # add default as key word or dictionary
        if d is None: return
        if type(d) is not dict: raise ValueError('add_default_params : default param must be a dictionary')
        # deep update to defaults
        basic_util.deep_dict_update(self.default_params, d)

    def role_doc(self,role):
        self.docs['role'] = role  # only in base class
    def class_doc(self,description):
        self.docs['description']=description



    def check_requirements(self):
        self.check_class_required_fields_prop_etc()


    def check_class_required_fields_prop_etc(self, required_props_list=[],
                                             requires3D=None, crumbs=''):
        for name in required_props_list:
            if name not in si.classes['particle_properties']:
                si.msg_logger.msg('     class ' + self.params['class_name'] + ', particle property "' + self.info['name']
                                + '" requires particle property  "' + name + '"'
                                + ' to work, add to reader["field_variables"], or add to fields param list, or add to particle_properties', fatal_error=True,crumbs=crumbs)

        if requires3D and not si.is3D_run:
                si.msg_logger.msg('     class ' + self.params['class_name'] + ', ' + self.info['name'] + ' can only be used with 3D hindcast ', fatal_error=True,crumbs=crumbs)

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
        current_particle_buffer_size = si.classes['particle_group_manager'].info['current_particle_buffer_size']

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

