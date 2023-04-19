from oceantracker.common_info_default_param_dict_templates import default_case_param_template, default_class_names
from oceantracker.util.parameter_util import make_class_instance_from_params
from oceantracker.util.module_importing_util import import_module_from_string

class SharedInfoClass(object):
    # allows working classes access to instances of other classes to use their methods
    def __init__(self):
        self.reset()

    def reset(self):
        self.classes = {}
        self.core_class_interator = {}
        # fill in known user class and iterator names
        for key, item in default_case_param_template.items():
            if type(item) == list:
                self.classes[key] = {}

    def add_core_class(self,class_type, params,  check_if_core_class=True, crumbs =''):

        ml= self.msg_logger

        #todo make check if in common.shared_info_default_params
        if class_type not in default_case_param_template and check_if_core_class:
            ml.msg('add_core_class, name is not a known core class, name=' + class_type,
                         crumbs='Adding core class type=' + class_type,
                         exception = True)
        i = make_class_instance_from_params(params, self.msg_logger, crumbs=crumbs + ' adding core class, type =  ' + class_type)


        if i.params['requires_3D'] and not self.case_runner_params['is_3D_run'] :
                # dont add a 3D class if i not a 3D run
                self.msg_logger.msg(' Not using add core class,' + i.params['name'] + ' as it can only be used with 3D hydro-models', note=True, crumbs=crumbs + ' adding core class')
        else:
            self.classes[class_type]= i
            self.core_class_interator[class_type] = i

        return i


    def create_class_instance_as_interator(self, class_type, iteration_group, params, crumbs=''):
        # dynamically  get instance of class from string eg oceantracker.solver.Solver
        ml= self.msg_logger

        instance_index = len(self.classes[class_type])

        crumbs += f' >>> adding_class type >> {class_type}  (group=  {iteration_group} #{instance_index+1: 1d})'

        i = make_class_instance_from_params(params, self.msg_logger, crumbs='user fields')

        known_list_classes= []
        for key, item in default_case_param_template.items():
            if type(item) == list:
                known_list_classes.append(key)

        if class_type not in known_list_classes:
            ml.msg('add_to_class_list: name is not a known class list,class_type=' + class_type , exception = True, crumbs = crumbs)

        # now add to class lists and interators
        # todo  check it is known interation group

        i.info['instance_index'] = instance_index  # needed for release group identification info etc, zero based
        i.info['instance_number'] =  instance_index + 1 # external facing number starting at 1

        if 'name' not in i.params or i.params['name'] is None:
            i.params['name'] = f"instance_number{ i.info['instance_number']:04d}"

        name = i.params['name']
        if name in self.classes[class_type]:
            ml.msg('Class type"' + class_type + '" already has a class with name = "' + i.params['name']
                         + '", "name" parameter must be unique',
                         crumbs =   crumbs,  fatal_error=True)

        if i.params['requires_3D'] and not self.case_runner_params['is_3D_run']:
                # dont add a 3D class if i not a 3D run
                self.msg_logger.msg(' Not using user  class,' + i.params['name'] + ' as it can only be used with 3D hydro-models', note=True, crumbs=crumbs + ' adding core class')
        else:
            self.classes[class_type][name] = i
        return i

    def delete_add_class_instance_to_interators(self, name, class_type, iteration_group, i):
        i.info['instance_index'] = len(self.classes[class_type]) # needed for release group identification info etc
        self.classes[class_type][name] = i

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

