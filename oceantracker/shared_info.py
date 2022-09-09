from oceantracker.common_info_default_param_dict_templates import default_case_param_template, default_class_names
from oceantracker.util.parameter_checking import GracefulExitError
from oceantracker.util.module_importing_util import import_module_from_string

class SharedInfoClass(object):
    # allows working classes access to instances of other classes to use their methods
    def __init__(self):
        self.reset()

    def reset(self):
        self.classes = {}
        self.class_list_interators = {}
        self.core_class_interator = {}
        # fill in known user class and iterator names
        for key, item in default_case_param_template.items():
            if type(item) == list:
                self.classes[key] = {}
                self.class_list_interators[key] = {'all': {}, 'user': {} ,'manual_update':{}}

    def add_core_class(self,class_type,class_params,  make_core=False):
        cl= self.case_log
        if class_type not in default_case_param_template and not make_core:
            cl.write_msg('add_core_class, name is not a known core class, name=' + class_type,
                         crumbs='Adding core class type=' + class_type,
                         exception = GracefulExitError, raiseerrors=True)

        i, msg = import_module_from_string(class_params['class_name'].strip())
        cl.add_messages(msg, raiseerrors=True)

        # merge params
        msg_list = i.merge_with_class_defaults(class_params, {}, crumbs='Merging core classes with defaults >>> ' + class_type )
        self.case_log.add_messages(msg_list, raiseerrors=True)

        self.classes[class_type]= i
        self.core_class_interator[class_type] = i


    def create_class_interator(self,class_type, known_iteration_groups=None):
        if class_type not in self.classes: self.classes[class_type] = {}
        if class_type not in self.class_list_interators: self.class_list_interators[class_type] = {'all': {}}

        if known_iteration_groups is not None:
            for g in known_iteration_groups:
                self.class_list_interators[class_type].update({g :{}})

    def add_class_instance_to_list_and_merge_params(self, class_type, iteration_group, class_params, crumbs=''):
        # dynamically  get instance of class from string eg oceantracker.solver.Solver
        cl= self.case_log
        crumbs += ' >>> Adding_class type >> ' + class_type + '(group= ' + iteration_group +')'

        known_types= []
        for key, item in default_case_param_template.items():
            if type(item) == list:
                known_types.append(key)

        if class_type not in known_types:
            cl.write_msg('add_to_class_list: name is not a known class list,class_type=' + class_type , exception = GracefulExitError, crumbs = crumbs, raiseerrors=True)

        if 'class_name' not in class_params and class_type in default_class_names:
            class_params['class_name']= default_class_names[class_type]

        i, msg = import_module_from_string(class_params['class_name'])
        cl.write_msg(msg, raiseerrors=True, crumbs= 'Importing class >>> '+  crumbs)

        i.info['instanceID'] = len(self.class_list_interators[class_type][iteration_group])
        nseq = i.info['instanceID']  + 1

        # merge to get any default class name and params
        msg_list = i.merge_with_class_defaults(class_params, {}, crumbs = crumbs+ ' >>> Merging with class defaults >>> ' + class_type + '[#' + str(nseq) + '] ')
        self.case_log.add_messages(msg_list, raiseerrors=True)

        if i.params['name'] is None or i.params['name'] =='':
            if iteration_group == 'user':
                i.params['name'] = 'unnamed%03.0f' %  (len(self.class_list_interators[class_type]['user'])+1)
            else:
                # this may be redundent if name param is required by class
                cl.write_msg('Only user added classes can be unnamed, all others must must have param["name"]' , exception = GracefulExitError, raiseerrors=True,
                             crumbs= crumbs + ' >>> ' + class_params['class_name'] )

        name = i.params['name']

        if name in self.classes[class_type]:
            cl.write_msg('Class type"' + class_type + '" already has a class with name = "' + i.params['name']
                         + '", "name" parameter must be unique',
                         crumbs = ' Checking for unique class names >>> '+  crumbs, exception = GracefulExitError, raiseerrors=True)

        # check class type OK
        known_types= []
        for key, item in default_case_param_template.items():
            if type(item) == list:
                known_types.append(key)

        if class_type not in known_types:
            return  cl.write_msg('add_to_class_list: name is not a known class list,class_type=' + class_type + ', name=' + name, exception = GracefulExitError)

        # now add to class lists and interators

        if iteration_group not in self.class_list_interators[class_type]:
            cl.write_msg('add_to_class_list: iteration_group  for class_type=' + class_type + ', group="'
                                    + iteration_group + '", is not one of known types=' + str(self.class_list_interators[class_type].keys()), exception = GracefulExitError)

        return i


    def add_class_instance_to_interators(self, name, class_type, iteration_group, i):
        i.info['instanceID'] = len(self.classes[class_type]) # needed for release group identification info etc
        self.classes[class_type][name] = i
        self.class_list_interators[class_type]['all'][name] = i
        self.class_list_interators[class_type][iteration_group][name] = i



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

