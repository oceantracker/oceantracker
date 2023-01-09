from  oceantracker.util import basic_util
import numpy as np
import traceback
from time import perf_counter
from oceantracker.shared_info import SharedInfoClass
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, merge_params_with_defaults
from oceantracker.util.message_and_error_logging import append_message, GracefulExitError, FatalError
from oceantracker.util.module_importing_util import import_module_from_string
from oceantracker.common_info_default_param_dict_templates import default_class_names, default_case_param_template

# parameter dictionaries are nested dictionaries or lists of dictionaries

def make_class_instance_from_params(params,class_type_name=None, base_case_params =None, msg_list=[], nseq=None, crumbs='', merge_params=True):
    # make a class insance from dynamically  get instance of class from string eg oceantracker.solver.Solver
    if base_case_params is None : base_case_params={}

    # add class sequence number, used for in class list
    if nseq is None:
        nseq= 0
        sequ_tag = ''
    else:
        sequ_tag = '[#' + str(nseq) + '] '
    crumbs += sequ_tag

    # work out class name
    if 'class_name' not in params:  params['class_name'] = None

    if params['class_name'] is None and class_type_name is not None:
        if 'class_name' in base_case_params and base_case_params['class_name'] is not None:
            params['class_name'] = base_case_params['class_name']
        elif class_type_name in default_class_names:
            params['class_name'] = default_class_names[class_type_name]
        else:
            append_message(msg_list, 'params for ' + crumbs + ' must contain class_name ' + class_type_name,
                           exception=GracefulExitError, nseq=nseq)
            return None, None, msg_list
    #else:
    #    # try to convert to long name
    #    if class_params['class_name'] in self.package_info['short_class_name_map']:
    #        class_params['class_name'] = self.package_info['short_class_name_map'][class_params['class_name']]

    i, msg = import_module_from_string(params['class_name'])
    if msg is not None:
        msg_list.append(msg)
        return i, msg_list



    i.info['nseq']= nseq
    i.info['class_type'] = class_type_name

    if merge_params:
        # merge template with base case first
        if class_type_name in default_case_param_template and type(default_case_param_template[class_type_name]) != list:
            base_case_params, msg_list = merge_params_with_defaults(base_case_params,
                                                    default_case_param_template[class_type_name], {},
                                                    check_for_unknown_keys=False,
                                                    crumbs=crumbs+'merging core clasess base case with case template',
                                                    msg_list=msg_list)

        i.params, msg_list = merge_params_with_defaults(params, i.default_params, base_case_params, msg_list=msg_list, crumbs=crumbs)

    return i, msg_list

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

    def check_class_required_fields_prop_etc(self, required_props_list=[], required_fields_list=[],
                                             required_grid_time_buffers_var_list=[],
                                             required_grid_var_list=[], requires3D=None, msg_list=[]):
        si = self.shared_info
        grid = si.classes['reader'].grid
        grid_time_buffers=  si.classes['reader'].grid_time_buffers

        for name in required_grid_var_list:
            if name not in grid:
               append_message(msg_list, '     class ' + self.params['class_name'] + ', ' + self.params['name']
                                + ' requires grid variable  "' + name + '"' + ' to work', exception = GracefulExitError)

        for name in required_grid_time_buffers_var_list:
            if name not in grid_time_buffers:
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
