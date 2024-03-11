import pkgutil,inspect,importlib
from os import path
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.common_info_default_param_dict_templates import default_classes_dict
from copy import deepcopy
from oceantracker.util.parameter_checking import merge_params_with_defaults
from time import perf_counter

from oceantracker.util.package_util import  scan_package_for_param_classes


class ClassImporter(object):
    def __init__(self,package_root_dir, msg_logger=None):

        self.class_tree= scan_package_for_param_classes(package_root_dir)
        self.msg_logger =msg_logger

        # build short and full name maps to oceantracker's parameter classes
        self.short_name_class_map = {}
        self.full_name_class_map = {}
        for class_role, classes in self.class_tree.items():
            for name, info in classes.items():

                mod_str = info['mod_str']
                short_name = class_role + '.' + name

                if short_name in self.short_name_class_map:
                    msg_logger.msg(f'short name of "{name}" of "{short_name}" is already found at "{self.short_name_class_map[short_name]["mod_str"]}", duplicate class names',
                                   fatal_error= True, hint= 'class names must be unique in core OceanTracker code')
                self.short_name_class_map[short_name] = info

                if class_role in self.full_name_class_map:
                    msg_logger.msg(f'full name of "{name}" is already found at "{self.short_to_full_name_map[mod_str]["mod_str"]}", duplicate class names',
                                      fatal_error=True, hint= 'class names must be unique in core OceanTracker code'
                                      )
                self.full_name_class_map[mod_str] = info

        msg_logger.exit_if_prior_errors('"class_name" errors')

    def get_class_obj(self,class_role, name, params, default_classID=None, crumbs=''):
        ml = self.msg_logger
        if 'class_name' in params and params['class_name'] is not None:
            cls_obj = self.get_class_obj_from_class_name(class_role, params['class_name'])
            if cls_obj is None:
                # try direct import from full string
                try:
                    s = params['class_name'].rsplit('.',1)
                    mod = importlib.import_module(s[0])
                    cls_obj = getattr(mod,s[1])

                except Exception as e:
                    ml.spell_check( 'checking known full class names',params["class_name"], self.class_maps['full_name_map'].keys(),
                                        crumbs=crumbs+ f' checking class_name "{params["class_name"]}"')
                    ml.spell_check( 'checking known short class names',params["class_name"], self.short_name_class_map.keys(),
                                                 crumbs= crumbs+ f' checking class_name "{params["class_name"]}"')

                    ml.msg(f'For "{class_role}" named "{name}", could not find class_name "{params["class_name"]}"',
                           fatal_error=True)

        else:
            # try default
            cls_obj = self.get_default_class(default_classID)
            if cls_obj is None:
                ml.msg(f'No class_name param for "{name}" given, and no known default class for type  "{class_role}"', fatal_error=True)

        # check class comes from expected type
        if cls_obj is not None:
            this_class_type = cls_obj.__module__.split('.')[1]
            if this_class_type != class_role:
                ml.msg(f'Class "{name}" of type "{this_class_type}", got "{cls_obj}", expected class with role "{class_role} ',
                       hint ='Has wrong class type or name been used for this type, or typo in "class_name" param?',fatal_error=True)

            pass

        return cls_obj

    def new_make_class_instance_from_params(self,params, class_role, name = None,  default_classID=None,
                                        crumbs='', merge_params=True, check_for_unknown_keys=True):

        if class_role not in self.class_tree:
            self.msg_logger.msg(f'unknown class role "{class_role}" for class named "{name}"', crumbs= crumbs + ' make_class_instance_from_params',
                                hint= f'possible values={self.class_tree.keys()}',
                                fatal_error=True, exit_now=True)

        if default_classID is None: default_classID = class_role
        class_obj = self.get_class_obj(class_role, name, params, default_classID=default_classID)

        if class_obj is None:
            return None
        i = class_obj() # make instance
        i.info['name'] = name
        i.info['class_role'] = class_role

        if merge_params:
            i.params  = merge_params_with_defaults(params, i.default_params, self.msg_logger, crumbs=crumbs,check_for_unknown_keys=check_for_unknown_keys)

        # attach the current message loger
        i.msg_logger = self.msg_logger
        return i

    def get_default_class(self,default_classID=None):

        cls_name=  default_classes_dict[default_classID] if default_classID in  default_classes_dict else None
        if cls_name is None:
            return None
        else:
            return self.full_name_class_map[cls_name]['class_obj']

    def get_class_obj_from_class_name(self, class_type, class_name):
        short_name = class_type + '.' + class_name
        if class_name in self.full_name_class_map:
            return  self.full_name_class_map[class_name]['class_obj']

        elif short_name in self.short_name_class_map:
            return self.short_name_class_map[short_name]['class_obj']
        else:
            return None

if __name__ == "__main__":
    # test code for errors
    from oceantracker.util.json_util import read_JSON
    from oceantracker.util.messgage_logger import MessageLogger
    ml =msg_logger=MessageLogger('Core developer:')
    d =ClassImporter(path.dirname(__file__), ml)

    params= read_JSON(r'C:\Work\oceantracker\demos\demo_param_files\demo56_SCHISM_3D_resupend_crtitical_friction_vel.json')
    params['particle_statistics']['test1'] = deepcopy( params['particle_statistics']['grid1'])
    params['particle_statistics']['test1']['class_name']   = params['particle_statistics']['test1']['class_name'].split('.')[-1]

    params['particle_statistics']['test2'] = deepcopy( params['particle_statistics']['grid1'])
    params['particle_statistics']['test2']['class_name']   = params['particle_statistics']['test1']['class_name'][2:]
    params['release_groups']['p3'] = deepcopy(params['release_groups']['P1'])
    params['release_groups']['p3']['class_name']   = 'PolygonRelease'

    params['particle_statistics']['test3'] =  params['event_loggers']['inoutpoly']
    # remove one map to test raw importing
    del d.class_maps['full_name_map']['oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit']
    del d.class_maps['short_name_map']['event_loggers.LogPolygonEntryAndExit']

    print('--------------')
    t0 = perf_counter()
    for c in ['dispersion','resuspension']:
        i = d.make_class_instance_from_params(c,c, params[c],default_classID=c)
        print(c,i)

    for c in ['particle_properties','particle_statistics','event_loggers','release_groups']:
        for name, c_params in params[c].items():
            i = d.make_class_instance_from_params(c,name, c_params, default_classID=c)
            print(c,name,i)
    print('time',perf_counter()-t0)
