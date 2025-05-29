from os import path
from copy import deepcopy
from oceantracker.util.parameter_checking import merge_params_with_defaults
from time import perf_counter
from oceantracker.util.__root_parameter_base_class__ import _RootParameterBaseClass
import pkgutil,inspect,importlib
from oceantracker import  definitions
import importlib, traceback
from timeit import  timeit

class ClassImporter():
    def __init__(self,msg_logger, crumbs='', caller=None):
        self.crumbs = crumbs
        self.msg_logger =msg_logger
        ml = msg_logger
        ml.msg(f'Starting package set up',tabs=2, caller=self)


    def _build_class_tree_ans_short_name_map(self, caller=None):
        t0 = perf_counter()
        # build class tree of al package parameter classes, with short, long name maps
        self.class_tree = self.scan_package_for_classes(crumbs='Package set up', caller=self)
        self.short_name_class_map, self.full_name_class_map,self.short_name_list =  self.build_short_and_full_name_maps(self.class_tree)
        ml = self.msg_logger
        ml.exit_if_prior_errors(f'"ClassImporter" setup errors', caller=caller)
        ml.progress_marker(f'Done package set up to setup ClassImporter', start_time=t0)
    def make_class_instance_from_params(self, class_role, params, name = None, default_classID=None, initialize=False,
                                        add_required_classes_and_settings=True, caller=None, crumbs='', merge_params=True, check_for_unknown_keys=True):
        ml = self.msg_logger

        if params is None: params = {}
        if name is not None: params['name'] = name

        if class_role not in self.class_tree:
            ml.msg(f'unknown class role "{class_role}" for class named "{name}"', crumbs= crumbs + ' make_class_instance_from_params',
                                hint= f'possible values={self.class_tree.keys()}',
                                fatal_error=True, caller=caller)

        # get class name
        params['class_name'] = self._get_class_name(class_role, params, default_classID,crumbs)

        class_obj = self._get_class_obj_from_class_name(params['class_name'])

        if class_obj is None:
            #todo not needed?
            return None
        i = class_obj() # make instance

        i.info['class_role'] = class_role

        if merge_params:
            i.params = merge_params_with_defaults(params, i.default_params, ml, crumbs=crumbs, check_for_unknown_keys=check_for_unknown_keys, caller=i)

        # attach the current message loger to instance
        i.msg_logger = self.msg_logger

        # add classes required by this class
        if add_required_classes_and_settings:
            i.add_required_classes_and_settings()

        if initialize:
            i.initial_setup()
        return i

    def scan_package_for_classes(self, crumbs='', caller=None):
        # scan dir for sub pacakes that have classes which are children of ParameterBaseClass
        # to set up class tree on instances of  package classes
        ml= self.msg_logger
        crumbs += '> scan_package_for_classes '
        t0 = perf_counter()
        tree = dict()
        crumbs + '> scan_package_for_classes'
        self.module_list=[]

        for _, sub_pkg_name, ispkg in pkgutil.iter_modules([definitions.package_dir]):

            if ispkg and sub_pkg_name != 'util':
                # look at sub packages
                if sub_pkg_name not in tree: tree[sub_pkg_name] = {}

                for _, mod_name, is_mod_a_pkg in pkgutil.iter_modules(path=[path.join(definitions.package_dir, sub_pkg_name)]):

                    if not is_mod_a_pkg:
                        mod = f'{path.basename(definitions.package_dir)}.{sub_pkg_name}.{mod_name}'
                        self.module_list.append(mod)
                        # import class and get info
                        i_mod = self._import_module_from_string(mod)

                        for class_name, class_obj in inspect.getmembers(i_mod):
                            if inspect.isclass(class_obj) and issubclass(class_obj, _RootParameterBaseClass) and class_obj.__module__ == mod:
                                # local classes only
                                class_name = mod + '.' + class_obj.__name__  # full import string

                                if class_obj.__name__ in tree[sub_pkg_name]:
                                    ml.msg(f'"{class_obj.__name__}" in module "{class_obj.__module__}" already found as "{tree[sub_pkg_name][class_obj.__name__]["class_name"]}", duplicate class names in ocean tracker pacakage?',
                                                hint=f'{definitions.package_fancy_name} in  dir {definitions.package_dir}',
                                                error = True,  crumbs=crumbs, caller=caller)
                                else:
                                    tree[sub_pkg_name][class_obj.__name__] = {}

                                info = dict(name=class_obj.__name__,
                                            class_obj=class_obj, base_class=None,
                                            class_name=class_name,
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

        self.module_list = list(set(self.module_list))
        ml.progress_marker(f'Built {definitions.package_fancy_name} package tree', start_time=t0,tabs=2)
        return tree


    def _get_class_name(self,class_role, params,default_classID,crumbs):

        ml = self.msg_logger

        if default_classID is None: default_classID = class_role # try using clas role as defaultID, used for core classes mainly
        class_name= params['class_name'] if 'class_name' in params else None

        if class_name is None and default_classID in definitions.default_classes_dict:
            return definitions.default_classes_dict[default_classID]

        if class_name is None:
            ml.msg(f'No class_name param for "{params["name"]}" given, and no known default class for type  "{class_role}"',
                    fatal_error=True, crumbs=crumbs)

        short_name= f'{class_role}.{class_name}'
        if short_name in self.short_name_class_map:
            return self.short_name_class_map[short_name]['class_name']

        if '.' not in class_name:
            ml.spell_check(f'Class name "{class_name}" is not a recognised short class_name',
                        class_name, self.short_name_list,
                        hint='A miss-spelt short class_name? if a user written class, class_name must be of as "module.class" import string, ie have at least one "."',
                        )
        # use give class name
        return params['class_name']

    def _get_class_obj_from_class_name(self, class_name):

        if class_name in self.full_name_class_map:
            return  self.full_name_class_map[class_name]['class_obj']
        else:
            # class not in the pre-assembled tree of inbuilt classes
            # split out package and module if class name as
            mod,_ ,c = class_name.rpartition('.')

            # import module/file

            m = self._import_module_from_string(mod, c)


            # now return get class within module/file
            try:
                return getattr(m, c)  # get class as module attribute
            except Exception as e:
                self.msg_logger.spell_check(f'Cannot find class "{c}" within module/file "{mod}"',
                                            f'{mod}.{c}', list(self.full_name_class_map.keys()),
                                            hint='A miss-spelt short class_name? or missing custom class?',
                                            )
                raise(e)
    def _import_module_from_string(self, mod, c = None):

        # check module exists before import
        mod_spec= importlib.util.find_spec(mod)
        if mod_spec is None:
            self.msg_logger.spell_check(f'Cannot find module "{mod}"',
                                    f'{mod}.{c}', self.module_list)

        try:
            m = importlib.import_module(mod)

            return m
        except Exception as e:
            # try a spell check
            self.msg_logger.msg(f'Possible syntax error in module "{mod}"',fatal_error=True,
                            exception =e, traceback_str=traceback.format_exc())

    def build_short_and_full_name_maps(self, class_tree):
        # build short and full name maps to oceantracker's parameter classes
        ml = self.msg_logger
        t0= perf_counter()
        short_name_list = []
        short_name_class_map = {}
        full_name_class_map = {}
        for class_role, classes in class_tree.items():
            for name, info in classes.items():
                class_name = info['class_name']
                short_name_list.append(name)
                short_name = class_role + '.' + name

                if short_name in short_name_class_map:
                    ml.msg(f'short name of "{name}" of "{short_name}" is already found at "{short_name_class_map[short_name]["class_name"]}", duplicate class names',
                                   error=True, hint='class names must be unique in core OceanTracker code')
                short_name_class_map[short_name] = info

                if class_role in full_name_class_map:
                    ml.msg(f'full name of "{name}" is already found at "{full_name_class_map[class_name]["class_name"]}", duplicate class names',
                                   error=True, hint='class names must be unique in core OceanTracker code'
                                   )
                full_name_class_map[class_name] = info
        ml.progress_marker(f'Built {definitions.package_fancy_name} sort name map', start_time=t0, tabs=2)
        return short_name_class_map, full_name_class_map, short_name_list