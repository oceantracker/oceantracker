from  oceantracker.util import basic_util
import numpy as np
import traceback
from time import perf_counter
from oceantracker.shared_info import SharedInfoClass
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, merge_params_with_defaults
from oceantracker.util.message_and_error_logging import append_message, GracefulExitError, FatalError

# parameter dictionaries are nested dictionaries or lists of dictionaries

class ParameterBaseClass(object):
    # object with default parameters as class dictionary, that are check against expections
    # philosophy is that
    # 1) is that all the options that can be tweaked on an object are parameters, with defaults
    # 2) a class where defaults are checked against expectation
    # 3) parameter are merged merge_with_class_defaults at run time
    # 4) the terminal value in a default dic must be an instance of   ParamDictValueChecker
    # 5)  ParamDictValueChecker checks give value against expectation or inserts default
    # 6) Defaults must be set in .__init__()  using method ._update_default_param_dictionary({})
    # 7) children must call   super().__init__()   to get defaults of parent

    code_timer = basic_util.BlockTimer()
    shared_info = SharedInfoClass()  # for all to access

    def initialize(self): pass

        
    def close(self):  pass

    def __init__(self):

        self.params={}
        self.info={'time_spent_updating': 0., 'update_calls': 0,'time_first_update_call':0.}  # stores info about object
        self.docs={'description': None, 'role': None # role is only set in base class
                   }
        self.default_params={}
        self.add_default_params({'class_name': PVC(None,str, doc_str='Class name as string A.B.C, used to import this class from python path'),
                                 'name':  PVC(None, 'random_walk_varyingAz', doc_str='The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code'),
                                 'user_note': PVC(None, str),
                                 })

    def add_default_params(self,d=None):
        # add default as key word or dictionary
        if d is None: return
        if type(d) is not dict: raise ValueError('add_default_params : default param must be a dictionary')
        # deep update to defaults
        basic_util.deep_dict_update(self.default_params, d)

    def class_doc(self,description=None, role= None):
        self.docs['description']=description
        self.docs['role'] = role # only in base class


    def check_requirements(self):
        msg_list = self.check_class_required_fields_prop_etc()
        return msg_list

    def check_class_required_fields_prop_etc(self, required_props_list=[], required_fields_list=[], required_grid_var_list=[], requires3D=None, msg_list=[]):
        si = self.shared_info
        grid = si.classes['reader'].grid

        for name in required_grid_var_list:
            if name not in grid:
               append_message(msg_list, '     class ' + self.params['class_name'] + ', ' + self.params['name']
                                + ' requires grid variable  "' + name + '"' + ' to work', exception = GracefulExitError)

        for name in required_fields_list:
            if name not in si.classes['fields']:
                append_message(msg_list,'     class ' + self.params['class_name'] + ', "' + self.params['name']
                                + '" requires field  "' + name + '"' + ' to work, add to reader["field_variables"], or add to fields param list', exception = GracefulExitError)

        for name in required_props_list:
            if name not in si.classes['particle_properties']:
                append_message(msg_list,'     class ' + self.params['class_name'] + ', particle property "' + self.params['name']
                                + '" requires particle property  "' + name + '"'
                                + ' to work, add to reader["field_variables"], or add to fields param list, or add to particle_properties', exception = GracefulExitError)

        if requires3D and (requires3D and not si.hindcast_is3D):
                append_message(msg_list,'     class ' + self.params['class_name'] + ', ' + self.params['name'] + ' can only be used with 3D hindcast ', exception = GracefulExitError)

        return msg_list

    def remove_default_params(self, name_list):
        # used to get rid if paramters of parent class which are not used by a child class
        si=self.shared_info
        for key in name_list:
            if key in self.default_params:
                del self.default_params[key]

    def merge_with_class_defaults(self, case_param, base_case, msg_list=[], crumbs=None):
        # merge class defaults, base_case and given case_params
        if crumbs is None: crumbs = self.__class__.__module__ +'.' + self.__class__.__name__
        self.params, msg_list = merge_params_with_defaults(case_param, self.default_params, base_case, msg_list=msg_list,  crumbs = crumbs)

        return msg_list

    # below dynamical adds shared particle index buffers when first used within in a class instance
    # buffers are used to hold selections of particles, saving memory and time by reuse
    # use with care as returned view may refer to same buffer!!

    def get_particle_index_buffer(self):
        # return pointer to particle buffer of indcies
        # set up if not already attribute of class
        if not hasattr(self, 'particle_index_buffer_data'):
            self.particle_index_buffer_data = np.full((self.shared_info.particle_buffer_size,), -127, np.int32)

        return self.particle_index_buffer_data[:]

    def get_particle_subset_buffer(self):
        # return pointer to particle buffer of indcies
        # set up if not already attribute of class
        if not hasattr(self, 'particle_subset_buffer_data'):
            self.particle_subset_buffer_data = np.full((self.shared_info.particle_buffer_size,), -127, np.int32)

        return self.particle_subset_buffer_data[:]


    def start_update_timer(self): self.update_timer_t0 = perf_counter()

    def stop_update_timer(self):
        dt= perf_counter() -  self.update_timer_t0
        self.info['time_spent_updating'] += dt
        self.info['update_calls'] += 1

        # note effect of any numba compilation on first call
        if self.info['update_calls'] == 1: self.info['time_first_update_call'] = dt


    def write_msg(self,text,warning=False,note=False,exception=None, hint=None,traceback_str=None):
        si = self.shared_info
        if exception is None:
            crumbs= None
        else:
            n = str(self.params['name']) if 'name' in self.params else str(None)
            crumbs='Class: ' + self.__module__ + '.' + self.__class__.__name__ +'(internal name=' + n +')'

        si.case_log.write_msg(text, warning=warning,note=note, hint=hint,
                exception=exception,traceback_str=traceback_str, crumbs=crumbs)
