
from oceantracker.util.parameter_util import make_class_instance_from_params
from oceantracker.util.module_importing_util import import_module_from_string
from oceantracker import common_info_default_param_dict_templates as common_info
from oceantracker.util.parameter_checking import merge_params_with_defaults
from time import  perf_counter

class SharedInfoClass(object):
    # allows working classes access to instances of other classes to use their methods
    def __init__(self):
        self.reset()
        self.block_timers={}
        self.classes ={}

    def reset(self):
        self.classes = {}
        # fill in known user class and iterator names
        for key in common_info.class_dicts_list:
            self.classes[key] = {}

    def add_core_class(self, name, params, crumbs ='',initialise=False):

        ml= self.msg_logger
        crumb_base = f' >>> adding core class type >> "{name}" '

        # make instance  and merge params
        i = make_class_instance_from_params(name, params, ml, default_classID=name,
                                            crumbs=crumb_base + crumbs )

        self.classes[name] = i
        if initialise: i.initial_setup()
        return i

    def create_class_dict_instance(self,name,class_role, group, params,  crumbs='', initialise=False,default_classID=None):
        # dynamically  get instance of class from string eg oceantracker.solver.Solver
        ml= self.msg_logger

        instanceID = len(self.classes[class_role])

        crumb_base = f' >>> adding_class type >> "{class_role}"  (name=  "{name}" instance #{instanceID: 1d}), '

        # make instance  and merge params
        i = make_class_instance_from_params(name, params, self.msg_logger,   crumbs= crumb_base + crumbs,default_classID=default_classID)

        if class_role not in common_info.class_dicts_list :
            ml.msg(f'Class type = "{class_role}": name is not a known class_role=' + class_role ,
                   exception = True, crumbs =  crumb_base + crumbs)

        # now add to class lists and interators

        i.info['type'] = group

        # needed for release group identification info etc, zero based
        i.info['instanceID'] =  instanceID

        i.info['class_role'] = class_role

        if name in self.classes[class_role]:
            ml.msg('Class type"' + class_role + '" already has a class with name = "' + i.info['name']
                         + '", "name" parameter must be unique',  crumbs =crumb_base + crumbs,  fatal_error=True)
        else:
            self.classes[class_role][name] = i
        if initialise: i.initial_setup()
        return i

    def all_class_instance_pointers_iterator(self):
        # build list of all points for iteration, eg in calling all close methods
        p = []

        for name, item in self.classes.items():
           if name in common_info.class_dicts_list:
               # set of classes
               if item is not None:
                    for key, i in item.items():
                        if i is not None:  p.append(i)

           else:
                if item is not None:
                    p.append(item)

        return p

    def block_timer(self,name,t0):
        b = self.block_timers
        if name not in b:
            b[name] = dict(time=0.,calls=0)
        b[name]['time'] += perf_counter()-t0
        b[name]['calls'] += 1
