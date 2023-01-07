from oceantracker.common_info_default_param_dict_templates import default_case_param_template, default_class_names
from oceantracker.util.message_and_error_logging import GracefulExitError, FatalError
from oceantracker.util.module_importing_util import import_module_from_string

class SharedInfoClass(object):
    # allows working classes access to instances of other classes to use their methods
    def __init__(self):
        self.reset()

    def reset(self):
        self.classes = {}
        self.class_interators_using_name = {}
        self.core_class_interator = {}
        self.classes_as_lists ={}
        # fill in known user class and iterator names
        for key, item in default_case_param_template.items():
            if type(item) == list:
                self.classes[key] = {}
                self.classes_as_lists[key] = []
                self.class_interators_using_name[key] = {'all': {}, 'user': {} , 'manual_update':{}}


    def add_core_class(self,class_type, instance,  check_if_core_class=True):
        cl= self.case_log

        if class_type not in default_case_param_template and check_if_core_class:
            cl.write_msg('add_core_class, name is not a known core class, name=' + class_type,
                         crumbs='Adding core class type=' + class_type,
                         exception = GracefulExitError)

        self.classes[class_type]= instance
        self.core_class_interator[class_type] = instance


    def create_class_interator(self,class_type, known_iteration_groups=None):
        if class_type not in self.classes: self.classes[class_type] = {}
        if class_type not in self.class_interators_using_name: self.class_interators_using_name[class_type] = {'all': {}}

        if known_iteration_groups is not None:
            for g in known_iteration_groups:
                self.class_interators_using_name[class_type].update({g :{}})

    def add_class_instance_to_interator_lists(self, class_type, iteration_group, i, crumbs=''):
        # dynamically  get instance of class from string eg oceantracker.solver.Solver
        cl= self.case_log
        crumbs += ' >>> Adding_class type >> ' + class_type + '(group= ' + iteration_group +')'

        known_list_classes= []
        for key, item in default_case_param_template.items():
            if type(item) == list:
                known_list_classes.append(key)

        if class_type not in known_list_classes:
            cl.write_msg('add_to_class_list: name is not a known class list,class_type=' + class_type , exception = GracefulExitError, crumbs = crumbs)

        # now add to class lists and interators
        # firts check it is known interation group
        if iteration_group not in self.class_interators_using_name[class_type]:
            cl.write_msg('add_to_class_list: iteration_group  for class_type=' + class_type + ', group="'
                         + iteration_group + '", is not one of known types=' + str(
                self.class_interators_using_name[class_type].keys()), exception=GracefulExitError)

        i.info['instanceID'] = len(self.classes[class_type])  # needed for release group identification info etc, zero based

        if 'name' not in i.params or i.params['name'] is None:
            i.params['name'] = f"{ i.info['instanceID']:04}"

        name = i.params['name']
        if name in self.classes[class_type]:
            cl.write_msg('Class type"' + class_type + '" already has a class with name = "' + i.params['name']
                         + '", "name" parameter must be unique',
                         crumbs = ' Checking for unique class names >>> '+  crumbs, exception = FatalError)


        self.classes[class_type][name] = i
        self.classes_as_lists[class_type].append(i)

        self.class_interators_using_name[class_type]['all'][name] = i
        self.class_interators_using_name[class_type][iteration_group][name] = i

    def delete_add_class_instance_to_interators(self, name, class_type, iteration_group, i):
        i.info['instanceID'] = len(self.classes[class_type]) # needed for release group identification info etc
        self.classes[class_type][name] = i
        self.classes_as_lists[class_type].append(i)

        self.class_interators_using_name[class_type]['all'][name] = i
        self.class_interators_using_name[class_type][iteration_group][name] = i




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

