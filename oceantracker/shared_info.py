
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
        for key in common_info.class_lists.keys():
            self.classes[key] = {}

    def add_core_class(self, class_type, params,  check_if_core_class=True, crumbs =''):

        ml= self.msg_logger

        #todo make check if in common.shared_info_default_params
        if class_type not in common_info.core_classes and check_if_core_class:
            ml.msg('add_core_class, name is not a known core class, name=' + class_type,
                         crumbs='Adding core class type=' + class_type,
                         exception = True)
        # make instance  and merge params
        i = make_class_instance_from_params(params, ml, class_type_name=class_type,
                                            crumbs=crumbs + ' adding core class, type =  ' + class_type)
        if i.params['requires_3D'] and not self.is_3D_run :
                # dont add a 3D class if i not a 3D run
                self.msg_logger.msg(' Not using add core class,' + i.params['name'] + ' as it can only be used with 3D hydro-models', note=True, crumbs=crumbs + ' adding core class')
        else:
            self.classes[class_type]= i
        return i


    def create_class_dict_instance(self, class_type, iteration_group, params, crumbs=''):
        # dynamically  get instance of class from string eg oceantracker.solver.Solver
        ml= self.msg_logger

        instanceID = len(self.classes[class_type])

        crumbs += f' >>> adding_class type >> {class_type}  (group=  {iteration_group} #{instanceID: 1d})'

        # make instance  and merge params
        i = make_class_instance_from_params(params, self.msg_logger, crumbs='user fields')

        if class_type not in common_info.class_lists.keys():
            ml.msg('add_to_class_list: name is not a known class list,class_type=' + class_type , exception = True, crumbs = crumbs)

        # now add to class lists and interators
        # todo  check it is known interation group

        # needed for release group identification info etc, zero based
        i.info['instanceID'] =  instanceID

        if 'name' not in i.params or i.params['name'] is None:
            i.params['name'] = f"instanceID{ i.info['instanceID']:04d}"

        name = i.params['name']
        if name in self.classes[class_type]:
            ml.msg('Class type"' + class_type + '" already has a class with name = "' + i.params['name']
                         + '", "name" parameter must be unique',
                         crumbs =   crumbs,  fatal_error=True)

        if i.params['requires_3D'] and not self.is_3D_run:
                # dont add a 3D class if i not a 3D run
                self.msg_logger.msg(' Not using user  class,' + i.params['name'] + ' as it can only be used with 3D hydro-models', note=True, crumbs=crumbs + ' adding core class')
        else:
            self.classes[class_type][name] = i
        return i

    def all_class_instance_pointers_iterator(self, asdict=False):
        # build list of all points for iteration, eg in calling all close methods
        if asdict:  p={}
        else:  p = []

        for name, item in self.classes.items():
           if type(item) != dict:
                if item is not None:
                    if asdict: p[name] = item
                    else: p.append(item)
           else:
               # must be list  dict
               for key, i in item.items():
                    if i is not None:
                        if asdict: p[name] = i
                        else:  p.append(i)
        return p

