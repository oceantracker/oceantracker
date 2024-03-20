from os import  environ, path, mkdir
from oceantracker import common_info_default_param_dict_templates as common_info
from copy import copy, deepcopy
from datetime import datetime
import shutil
from os import path, makedirs, walk, unlink
import traceback
from oceantracker.util import json_util
from oceantracker.util import basic_util , get_versions_computer_info

def setup_output_dir(params, msg_logger, crumbs='', caller=None):

    # setus up params, opens log files/ error handling, required befor mesage loger can be used

    # merge required settings
    params = merge_settings_with_defaults(params,  ['root_output_dir','output_file_base','add_date_to_run_output_dir'],
                                         msg_logger, crumbs='setup_output_dir')

    # get output files location
    root_output_dir = path.abspath(path.normpath(params['root_output_dir']))
    run_output_dir = path.join(root_output_dir, params['output_file_base'])

    if params ['add_date_to_run_output_dir']:
        run_output_dir += datetime.now().strftime("_%Y-%m-%d_%H-%M")

    # clear existing folder
    if path.isdir(run_output_dir):
        shutil.rmtree(run_output_dir)
        for root, dirs, files in walk(run_output_dir):
            for f in files:
                unlink(path.join(root, f))
            for d in dirs:
                shutil.rmtree(path.join(root, d))
        msg_logger.msg('Deleted contents of existing output dir', warning=True)

    # make a new dir
    try:
        makedirs(run_output_dir)  # make  and clear out dir for output
    except OSError as e:
        # path may already exist, but if not through other error, exit
        msg_logger.msg(f'Failed to make run output dir:{run_output_dir}',fatal_error=True,
                       exception=e, traceback_str=traceback.print_exc(), exit_now=True)

    # write a copy of user given parameters, to help with debugging and code support
    fb =  'users_params_' + params['output_file_base']
    output_files  = {'root_output_dir': root_output_dir,
                      'run_output_dir': run_output_dir,
                      'output_file_base': params['output_file_base'],
                      'runInfo_file': params['output_file_base'] + '_runInfo.json',
                      'runLog_file': params['output_file_base'] + '_runScreen.log',
                      'run_error_file': params['output_file_base'] + '_run.err',
                      'users_params_json': fb + '.json',
                                      }
    return output_files

def  write_raw_user_params(output_files, params,msg_logger, case_list=None):

    # different if run in parallel
    if case_list is None:
        out = params
    else:
        out = {'base_case_params': params, 'case_list_params': case_list}

    fn= output_files['output_file_base']+'_raw_user_params.json'
    output_files['raw_user_params'] = fn
    json_util.write_JSON(path.join(output_files['run_output_dir'],fn),out)
    msg_logger.msg('to help with debugging, parameters as given by user  are in "' + fn + '"',  tabs=2, note=True)

def decompose_params(params, msg_logger, full_checks=True, crumbs='', caller=None):
  
    w = {'settings': {},
         'core_classes': {k: {} for k in common_info.core_class_list},  # insert full list and defaults
         'class_dicts': {k: {} for k in common_info.class_dicts_list},
         }

    known_top_level_keys = list(common_info.shared_settings_defaults.keys()) \
                           + list(common_info.case_settings_defaults.keys()) \
                           + common_info.class_dicts_list \
                           + common_info.core_class_list


    # split and check for unknown keys
    for key, item in params.items():
        k = copy(key)
        if len(k) != len(k.strip()):
            msg_logger.msg(f'Removing leading or trailing blanks from top level parameter key "{key}"', warning=True, crumbs=crumbs,caller=caller)
            k = key.strip()  # remove leading/trailing blanks

        if type(item) == tuple:
            # check item not a tuple
            msg_logger.msg(f'Top level parameters must be key : value pairs of a dictionary, got a tuple for key= "{key}", value= "{str(item)}"', fatal_error=True, crumbs=crumbs,
                   hint='is there an un-needed comma at the end of the parameter/line?, if a tuple was intentional, then use a list instead', caller=caller)

        elif k in common_info.shared_settings_defaults.keys() or k in common_info.case_settings_defaults.keys():
            w['settings'][k] = item

        elif k in common_info.core_class_list:
            w['core_classes'][k] = item

        elif k in common_info.class_dicts_list:
            if type(item) is not dict:
                msg_logger.msg('class dict type "' + key + '" must contain a dictionary, where key is name of class, value is a dictionary of parameters',
                       hint=' for this key got type =' + str(type(item)),
                       fatal_error=True, crumbs=crumbs)
            w['class_dicts'][k] = item
        else:
            msg_logger.spell_check(' top level parm./key, ignoring', key, known_top_level_keys, caller=caller,
                           crumbs=crumbs, link='parameter_ref_toc')

    msg_logger.exit_if_prior_errors('Errors in decomposing parameters into settings, and classes')

    return w

def check_python_version(msg_logger):
        # set up log files for run
        ml = msg_logger
        v = get_versions_computer_info.get_code_version()
        ml.msg(' Python version: ' + v['python_version'], tabs=2)
        p_major =v['python_major_version']
        p_minor= v['python_minor_version']
        install_hint = 'Install Python 3.10 or used environment.yml to build a Conda virtual environment named oceantracker'
        if not ( p_major > 2 and p_minor >= 9):
            ml.msg(common_info.package_fancy_name + ' requires Python 3 , version >= 3.9  and < 3.11',
                         hint=install_hint, warning=True, tabs=1)
        if (p_major == 3 and p_minor >= 11):
            ml.msg(common_info.package_fancy_name + ' is not yet compatible with Python 3.11, as not all imported packages have been updated, eg Numba', warning=True)

        ml.exit_if_prior_errors()

def config_numba_environment(params, msg_logger, crumbs='', caller = None):
    # set numba config via enviroment variables,
    # this must be done before first import of numba

    settings_list = [name for name in common_info.all_setting_defaults.keys() if name.lower().startswith('numba')]
    params= merge_settings_with_defaults(params, settings_list, msg_logger, crumbs= crumbs+ '> setting Nunba environment', caller=caller)

    environ['numba_function_cache_size'] = str(params['numba_function_cache_size'])

    if 'numba_cache_code' in params  and params['numba_cache_code']:
       environ['OCEANTRACKER_NUMBA_CACHING'] = '1'
       environ['NUMBA_CACHE_DIR'] = path.join(params['root_output_dir'], 'numba_cache')
    else:
        environ['OCEANTRACKER_NUMBA_CACHING'] = '0'


    if  'debug' in params and params['debug']:
        environ['NUMBA_BOUNDSCHECK'] = '1'
        environ['NUMBA_FULL_TRACEBACKS'] = '1'
        
def merge_settings_with_defaults(params, settings_list, msg_logger, crumbs='', caller=None):
    # check setting or set equal to  default value if not in params
    # used for simple settings only no dict or list
    #todo replace thsoi with merge_params_with_defaults, with added list of keys to keck
    if type(settings_list) != list: settings_list= [settings_list]
    for name in settings_list:
        pvc = common_info.shared_settings_defaults[name]
        if name not in params or params[name] is None:
            params[name] = pvc.get_default()
        else:
            params[name] = pvc.check_value(params[name], msg_logger, crumbs = crumbs + f'{crumbs} setting "{name}"', caller=caller)
    return params

def merge_base_and_case_working_params(base_working_run_builder, case_working_params, msg_logger, crumbs='', caller=None):

    # check any case settings are not in the ones that can only be shared
    for key in case_working_params['settings'].keys():
        pass
        if key in common_info.shared_settings_defaults:
            msg_logger.msg(f'Setting {key} cannot be set with a case', crumbs= crumbs,
                          hint='Move parameter from cases to the base case', caller=caller, fatal_error=True)

    # merge the settings first
    for key, item in base_working_run_builder['settings'].items():
        if key not in case_working_params:
            case_working_params['settings'][key] = item

    # merge core classes
    for key, item in base_working_run_builder['core_classes'].items():
        if key not in case_working_params:
            case_working_params['core_classes'][key]= item
    # class dicts
    for role, role_dict in base_working_run_builder['class_dicts'].items():
        # loop over named base case classes
        for name, item in  base_working_run_builder['class_dicts'][role].items():
            if name not in case_working_params['class_dicts'][role]:
                case_working_params['class_dicts'][role][name] = item
            else:
                # name appears in both base and case params
                msg_logger.msg(f'In role {role} the classes named {name} is in both the case and base case params, ignoring base case version',
                               crumbs=f'{crumbs} > case number {case_working_params["caseID"]}',
                               hint='Delete either base case or case parameters of this name to remove this warning',  warning=True)

        pass
    return case_working_params