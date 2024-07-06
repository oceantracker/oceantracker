from os import path
from copy import deepcopy
from oceantracker.util.parameter_checking import merge_params_with_defaults
from time import perf_counter
from oceantracker.util.__root_parameter_base_class__ import _RootParameterBaseClass
import pkgutil,inspect,importlib
from oceantracker import  definitions
import importlib
from timeit import  timeit
class ClassImporter():
    def __init__(self,shared_info, msg_logger, crumbs='', caller=None):
        self.shared_info = shared_info
        self.crumbs = crumbs
        self.msg_logger =msg_logger
        ml = msg_logger
        ml.msg(f'Starting package set up',tabs=2, caller=self)
        t0 = perf_counter()

        # build clas tree of al package parameter classes, with short, long name maps
        self.class_tree = self.scan_package_for_classes(crumbs='Package set up', caller=self)
        self.short_name_class_map, self.full_name_class_map =  self.build_short_and_full_name_maps(self.class_tree)

        ml.exit_if_prior_errors(f'"ClassImporter" setup errors', caller=caller)
        ml.progress_marker(f'Done package set up to setup ClassImporter', start_time=t0)

    def get_class_obj(self,class_role, name, params, default_classID=None, crumbs='',caller=None):
        ml = self.msg_logger
        crumbs += '> get_class_obj'

        cls_obj = self.get_class_obj_from_class_name(class_role, params['class_name'])

        if cls_obj is  None:
            ml.msg(f'No class_name param for "{name}" given, and no known default class for type  "{class_role}"', fatal_error=True)
            return
            # check class comes from expected type
        this_class_type = cls_obj.__module__.split('.')[1]
        if this_class_type != class_role:
            ml.msg(f'Class "{name}" of type "{this_class_type}", got "{cls_obj}", expected class with role "{class_role} ',
                   hint ='Has wrong class type or name been used for this type, or typo in "class_name" param?',fatal_error=True)
        pass

        return cls_obj

    def get_class_name(self,params,default_classID):
        si = self.shared_info
        if 'class_name' in params and params['class_name'] is not None:
            return params['class_name']
        elif default_classID in definitions.default_classes_dict :
            return definitions.default_classes_dict[default_classID]
        else:
            return None

    def get_class_obj_from_class_name(self, class_type, class_name):
        short_name = class_type + '.' + class_name
        if class_name in self.full_name_class_map:
            return  self.full_name_class_map[class_name]['class_obj']

        elif short_name in self.short_name_class_map:
            return self.short_name_class_map[short_name]['class_obj']

        elif '.' not in class_name:
            # error if not a known short name and error as not module.class form
            self.msg_logger.spell_check(f' Cannot find module and class for class_name="{class_name}"',
                        class_name,[x.split('.')[1] for x in self.short_name_class_map.keys()],
                        hint='A miss-spelt short class_name?',
                        fatal_error=True, exit_now=True)
            pass
        else:
            # split out package and module if class name as
            mod,_ ,c = class_name.rpartition('.')
            try:
                m = self._import_module_from_string(mod)
                return getattr(m,c) # get class as module attribute
            except Exception as e:
                self.msg_logger.spell_check(f' Cannot find module "{mod}" or class within it="{c}"',
                                            f'{mod}.{c}', [x.split('.')[1] for x in self.short_name_class_map.keys()],
                                            hint='A miss-spelt short class_name? or missing custimn class',
                                            fatal_error=True, exit_now=True)

    def new_make_class_instance_from_params(self, class_role, params, name = None,  default_classID=None,
                                    caller=None,   crumbs='', merge_params=True, check_for_unknown_keys=True):
        ml = self.msg_logger
        if class_role not in self.class_tree:
            self.msg_logger.msg(f'unknown class role "{class_role}" for class named "{name}"', crumbs= crumbs + ' make_class_instance_from_params',
                                hint= f'possible values={self.class_tree.keys()}',
                                fatal_error=True, exit_now=True, caller=caller)
        if default_classID is None: default_classID = class_role # try using clas role as defaultID, used for core classes mainly

        # get class name
        params['class_name'] = self.get_class_name(params, default_classID)
        if  params['class_name'] is  None:
            ml.msg(f'No class_name param for "{name}" given, and no known default class for type  "{class_role}"', fatal_error=True)
            return

        class_obj = self.get_class_obj_from_class_name(class_role, params['class_name'])

        if class_obj is None:
            return None
        i = class_obj() # make instance
        i.info['name'] = name
        i.info['class_role'] = class_role

        if merge_params:
            i.params  = merge_params_with_defaults(params, i.default_params, self.msg_logger, crumbs=crumbs,check_for_unknown_keys=check_for_unknown_keys, caller=i)

        # attach the current message loger to instance
        i.msg_logger = self.msg_logger
        return i

    def scan_package_for_classes(self, crumbs='', caller=None):
        # scan dir for sub pacakes that have classes which are children of ParameterBaseClass
        # to set up class tree on instances of  package classes
        ml= self.msg_logger
        crumbs += '> scan_package_for_classes '
        t0 = perf_counter()
        tree = dict()
        crumbs + '> scan_package_for_classes'
        for _, sub_pkg_name, ispkg in pkgutil.iter_modules([definitions.package_dir]):

            if ispkg and sub_pkg_name != 'util':
                # look at sub packages
                if sub_pkg_name not in tree: tree[sub_pkg_name] = {}

                #sub_pkg_str =f'{path.basename(definitions.package_dir)}.{sub_pkg_name}'
                #sub_pkg = self._import_module_from_string(sub_pkg_str)

                for _, mod_name, is_mod_a_pkg in pkgutil.iter_modules(path=[path.join(definitions.package_dir, sub_pkg_name)]):
                #for _, mod_name, is_mod_a_pkg in pkgutil.iter_modules(sub_pkg):

                    if not is_mod_a_pkg:
                        mod = f'{path.basename(definitions.package_dir)}.{sub_pkg_name}.{mod_name}'

                        # import class and get info
                        i_mod = self._import_module_from_string(mod)
                        for class_name, class_obj in inspect.getmembers(i_mod):
                            if inspect.isclass(class_obj) and issubclass(class_obj, _RootParameterBaseClass) and class_obj.__module__ == mod:
                                # local classes only
                                if class_obj.__name__ in tree[sub_pkg_name]:
                                    ml.msg(f'"{class_obj.__name__}" in module "{class_obj.__module__}" already found as "{tree[sub_pkg_name][class_obj.__name__]["mod_str"]}", duplicate class names in ocean tracker pacakage',
                                                hint=f'{definitions.package_fancy_name} in  dir {definitions.package_dir}',
                                                fatal_error = True,  crumbs=crumbs, caller=caller)
                                else:
                                    tree[sub_pkg_name][class_obj.__name__] = {}

                                mod_str = mod + '.' + class_obj.__name__  # full import string
                                info = dict(name=class_obj.__name__,
                                            class_obj=class_obj, base_class=None,
                                            mod_str=mod_str,
                                            file=inspect.getfile(class_obj))
                                # find base class
                                for i in class_obj.mro():
                                    if i.__name__.lower().startswith('_base'):
                                        info['base_classes'] = i.__name__
                                        break

                                # put class info in tree
                                tree[sub_pkg_name][class_obj.__name__] = info

                # sort keys into alphabetical order for documetation gerneration
                tree[sub_pkg_name] = dict(sorted(tree[sub_pkg_name].items()))
        ml.progress_marker(f'Built {definitions.package_fancy_name} package tree', start_time=t0,tabs=2)
        return tree

    def _import_module_from_string(self, mod):
        try:
            m = importlib.import_module(mod)
        except Exception as e:
            self.msg_logger.msg(f'Unexpected error dynamically loading module named "{mod}"',
                                hint='Got error'+str(e),
                                fatal_error=True,exit_now=True)
        return m
    def build_short_and_full_name_maps(self, class_tree):
        # build short and full name maps to oceantracker's parameter classes
        ml = self.msg_logger
        t0= perf_counter()
        short_name_class_map = {}
        full_name_class_map = {}
        for class_role, classes in class_tree.items():
            for name, info in classes.items():
                mod_str = info['mod_str']
                short_name = class_role + '.' + name

                if short_name in short_name_class_map:
                    ml.msg(f'short name of "{name}" of "{short_name}" is already found at "{short_name_class_map[short_name]["mod_str"]}", duplicate class names',
                                   fatal_error=True, hint='class names must be unique in core OceanTracker code')
                short_name_class_map[short_name] = info

                if class_role in full_name_class_map:
                    ml.msg(f'full name of "{name}" is already found at "{full_name_class_map[mod_str]["mod_str"]}", duplicate class names',
                                   fatal_error=True, hint='class names must be unique in core OceanTracker code'
                                   )
                full_name_class_map[mod_str] = info
        ml.progress_marker(f'Built {definitions.package_fancy_name} sort name map', start_time=t0, tabs=2)
        return short_name_class_map, full_name_class_map