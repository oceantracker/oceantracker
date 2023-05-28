from  oceantracker.util import basic_util
import numpy as np
import traceback
from time import perf_counter
from oceantracker.shared_info import SharedInfoClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, merge_params_with_defaults
from oceantracker.util.module_importing_util import import_module_from_string

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

    shared_info = SharedInfoClass()  # for all to access

    def initial_setup(self): pass

    def close(self):  pass

    def __init__(self):

        self.params={}
        self.info={'time_spent_updating': 0., 'update_calls': 0,'time_first_update_call':0.}  # stores info about object
        self.docs={'description': None, 'role': None # role is only set in base class
                   }
        self.default_params={}
        self.add_default_params({'class_name': PVC(None,str, doc_str='Class name as string A.B.C, used to import this class from python path'),
                                 'name':  PVC(None, str, doc_str='The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code'),
                                 'user_note': PVC(None, str),
                                 'requires_3D': PVC(False, bool)
                                 })


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

    def class_doc(self,description=None, role= None):
        self.docs['description']=description
        self.docs['role'] = role # only in base class


    def check_requirements(self):
        self.check_class_required_fields_prop_etc()


    def check_class_required_fields_prop_etc(self, required_props_list=[], required_fields_list=[],
                                             required_grid_var_list=[], requires3D=None):
        si = self.shared_info
        grid = si.classes['reader'].grid

        for name in required_grid_var_list:
            if name not in grid:
               si.msg_logger.msg('     class ' + self.params['class_name'] + ', ' + self.params['name']
                                + ' requires grid variable  "' + name + '"' + ' to work', fatal_error=True)

        for name in required_fields_list:
            if name not in si.classes['fields']:
                si.msg_logger.msg('     class ' + self.params['class_name'] + ', "' + self.params['name']
                                + '" requires field  "' + name + '"' + ' to work, add to reader["field_variables"], or add to fields param class list', fatal_error=True)

        for name in required_props_list:
            if name not in si.classes['particle_properties']:
                si.msg_logger.msg('     class ' + self.params['class_name'] + ', particle property "' + self.params['name']
                                + '" requires particle property  "' + name + '"'
                                + ' to work, add to reader["field_variables"], or add to fields param list, or add to particle_properties', fatal_error=True)

        if requires3D and not si.is_3D_run:
                si.msg_logger.msg('     class ' + self.params['class_name'] + ', ' + self.params['name'] + ' can only be used with 3D hindcast ', fatal_error=True)

    def remove_default_params(self, name_list):
        # used to get rid if paramters of parent class which are not used by a child class
        si=self.shared_info
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

    def get_particle_index_buffer(self):
        # return pointer to particle buffer of indcies
        # set up if not already attribute of class
        if not hasattr(self, 'particle_index_buffer_data'):
            self.particle_index_buffer_data = np.full((self.shared_info.particle_buffer_size,), -127,dtype= np.int32)

        return self.particle_index_buffer_data[:]

    def get_particle_subset_buffer(self):
        # return pointer to particle buffer of indcies
        # set up if not already attribute of class
        if not hasattr(self, 'particle_subset_buffer_data'):
            self.particle_subset_buffer_data = np.full((self.shared_info.particle_buffer_size,), -127, dtype= np.int32)

        return self.particle_subset_buffer_data[:]


    def start_update_timer(self): self.update_timer_t0 = perf_counter()

    def stop_update_timer(self):
        dt= perf_counter() -  self.update_timer_t0
        self.info['time_spent_updating'] += dt
        self.info['update_calls'] += 1

        # note effect of any numba compilation on first call
        if self.info['update_calls'] == 1: self.info['time_first_update_call'] = dt


