
from oceantracker.util.parameter_util import make_class_instance_from_params
from oceantracker.util.module_importing_util import import_module_from_string
from oceantracker import common_info_default_param_dict_templates as common_info
from oceantracker.util.parameter_checking import merge_params_with_defaults


class SharedInfoClass(object):
    # allows working classes access to instances of other classes to use their methods
    def __init__(self):
        self.reset()

    def reset(self):
        self.classes = {}
        # fill in known user class and iterator names
        for key in list(common_info.class_dicts.keys()):
            self.classes[key] = {}

    def add_core_class(self, name, params, crumbs =''):

        ml= self.msg_logger
        crumb_base = f' >>> adding core class type >> "{name}" '

        # make instance  and merge params
        i = make_class_instance_from_params(name, params, ml, class_role_name=name,
                                            crumbs=crumb_base + crumbs )

        if i.params['requires_3D'] and not self.is_3D_run :
                # dont add a 3D class if i not a 3D run
                self.msg_logger.msg(' Not using add core class,' + i.info['name'] + ' as it can only be used with 3D hydro-models', note=True, crumbs=crumbs + ' adding core class')
        else:
            self.classes[name] = i
        return i


    def create_class_dict_instance(self,name,class_role, group, params,  crumbs=''):
        # dynamically  get instance of class from string eg oceantracker.solver.Solver
        ml= self.msg_logger

        instanceID = len(self.classes[class_role])

        crumb_base = f' >>> adding_class type >> "{class_role}"  (name=  "{name}" instance #{instanceID: 1d}), '

        # make instance  and merge params
        i = make_class_instance_from_params(name, params, self.msg_logger,
                                            crumbs= crumb_base + crumbs)

        if class_role not in common_info.class_dicts.keys() :
            ml.msg(f'Class type = "{class_role}": name is not a known class_role=' + class_role ,
                   exception = True, crumbs =  crumb_base + crumbs)

        # now add to class lists and interators

        i.info['group'] = group

        # needed for release group identification info etc, zero based
        i.info['instanceID'] =  instanceID

        i.info['class_role'] = class_role

        if name in self.classes[class_role]:
            ml.msg('Class type"' + class_role + '" already has a class with name = "' + i.info['name']
                         + '", "name" parameter must be unique',
                         crumbs =    crumb_base + crumbs,  fatal_error=True)

        if i.params['requires_3D'] and not self.is_3D_run:
                # dont add a 3D class if i not a 3D run
                self.msg_logger.msg(' Not using user  class,' + i.info['name'] + ' as it can only be used with 3D hydro-models',
                                    note=True, crumbs= crumb_base + crumbs)
        else:
            self.classes[class_role][name] = i
        return i

    def all_class_instance_pointers_iterator(self):
        # build list of all points for iteration, eg in calling all close methods
        p = []

        for name, item in self.classes.items():
           if name in common_info.class_dicts.keys():
               # set of classes
               if item is not None:
                    for key, i in item.items():
                        if i is not None:  p.append(i)

           else:
                if item is not None:
                    p.append(item)

        return p

