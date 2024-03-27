from os import  environ, path, mkdir
from oceantracker import definitions as common_info
from copy import copy, deepcopy
from datetime import datetime
import shutil
from os import path, makedirs, walk, unlink
import traceback
from oceantracker.util import json_util
from oceantracker.util import basic_util , get_versions_computer_info
from numba import  njit
import  numpy as np

def setup_output_dir(params, msg_logger, crumbs='', caller=None):

    # setus up params, opens log files/ error handling, required befor mesage loger can be used
    crumbs += '> setup_output_dir'
    # get output files location
    root_output_dir = path.abspath(path.normpath(params['root_output_dir']))
    run_output_dir = path.join(root_output_dir, params['output_file_base'])

    if params['add_date_to_run_output_dir']:
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
                       crumbs=crumbs, caller= caller,
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

def write_raw_user_params(output_files, params,msg_logger, case_list=None):

    # different if run in parallel
    if case_list is None:
        out = params
    else:
        out = {'base_case_params': params, 'case_list_params': case_list}

    fn= output_files['output_file_base']+'_raw_user_params.json'
    output_files['raw_user_params'] = fn
    json_util.write_JSON(path.join(output_files['run_output_dir'],fn),out)
    msg_logger.msg('to help with debugging, parameters as given by user  are in "' + fn + '"',  tabs=2, note=True)

def decompose_params(shared_info, params, msg_logger, crumbs='', caller=None):
    si = shared_info
    crumbs += '> decompose_params'
    w = {'settings': {},
         'core_roles': {k: {} for k in si.core_roles.possible_values()},  # insert full list and defaults
         'roles_dict': {k: {} for k in si.roles.possible_values()},
         }

    setting_keys = si.default_settings.possible_values()
    core_role_keys = si.core_roles.possible_values()
    role_keys =  si.roles.possible_values()
    known_top_level_keys =  setting_keys + core_role_keys + role_keys

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

        elif k in setting_keys:
            w['settings'][k] = item

        elif k in core_role_keys:
            w['core_roles'][k] = item

        elif k in role_keys:
            if type(item) is not dict:
                msg_logger.msg('class dict type "' + key + '" must contain a dictionary, where key is name of class, value is a dictionary of parameters',
                       hint=' for this key got type =' + str(type(item)),
                       fatal_error=True, crumbs=crumbs)
            w['roles_dict'][k] = item
        else:
            msg_logger.spell_check('Unkown setting or role as top level param./key, ignoring', key, known_top_level_keys, caller=caller,
                           crumbs=crumbs, link='parameter_ref_toc', fatal_error=True)

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
            ml.msg(common_info.package_fancy_name + ' is not yet compatible with Python 3.11, as not all imported packages have been updated, eg netcdf4', warning=True)


def config_numba_environment_and_random_seed(settings, msg_logger, crumbs='', caller = None):
    # set numba config via environment variables,
    # this must be done before first import of numba

    environ['NUMBA_function_cache_size'] = str(settings['NUMBA_function_cache_size'])

    if 'NUMBA_cache_code' in settings  and settings['NUMBA_cache_code']:
       environ['OCEANTRACKER_NUMBA_CACHING'] = '1'
       environ['NUMBA_CACHE_DIR'] = path.join(settings['root_output_dir'], 'numba_cache')
    else:
        environ['OCEANTRACKER_NUMBA_CACHING'] = '0'

    if  'debug' in settings and settings['debug']:
        environ['NUMBA_BOUNDSCHECK'] = '1'
        environ['NUMBA_FULL_TRACEBACKS'] = '1'

    if settings['USE_random_seed']:
            np.random.seed(0)  # set numpy
            set_seed(0) # set numba seed which is different from numpys
            msg_logger.msg('Using numpy.random.seed(0),seed_numba_random(0) makes results reproducible (only use for testing developments give the same results!)', warning=True)
@njit
def set_seed(value):
    np.random.seed(value)
@njit
def test_random():
    return  np.random.rand()
def merge_critical_settings_with_defaults(settings, default_settings, critical_settings, msg_logger, crumbs='', caller=None):
    # check setting or set equal to  default value if not in params
    # used for simple settings only no dict or list
    crumbs += '> merge_critical_settings_with_defaults'
    # add numba settings to critical settings
    critical_settings += [key for key in default_settings.possible_values() if 'numba' in key.lower()]
    settings= merge_settings(settings, default_settings, critical_settings, msg_logger, crumbs='', caller=None)
    return settings, critical_settings

def merge_settings(settings, default_settings, settings_to_merge, msg_logger, crumbs='', caller=None):
    crumbs += '> merge_settings'
    all_settings = default_settings.possible_values()
    for name in settings_to_merge:
        pvc = getattr(default_settings, name)
        if name not in settings or settings[name] is None:
            settings[name] = pvc.get_default()
        elif name in all_settings:
            settings[name] = pvc.check_value(settings[name], msg_logger,
                                             crumbs= crumbs + f'> setting = "{name}"', caller=caller)
        else:
            msg_logger.spell_check(f'Unrecognized setting "{name}"',name, all_settings,
                            crumbs = crumbs + f'> {name}', caller=caller, fatal_error=True)
        pass
    return settings

def merge_base_and_case_working_params(base_working_params, case_working_params, msg_logger, crumbs='', caller=None):

    # check any case settings are not in the ones that can only be shared
    for key in case_working_params['settings'].keys():
        pass
        if key in common_info.shared_settings_defaults:
            msg_logger.msg(f'Setting {key} cannot be set with a case', crumbs= crumbs,
                          hint='Move parameter from cases to the base case', caller=caller, fatal_error=True)

    # merge the settings first
    for key, item in base_working_params['settings'].items():
        if key not in case_working_params:
            case_working_params['settings'][key] = item

    # merge core classes
    for key, item in base_working_params['core_roles'].items():
        if key not in case_working_params:
            case_working_params['core_roles'][key]= item
    # class dicts
    for role, role_dict in base_working_params['roles_dict'].items():
        # loop over named base case classes
        for name, item in  base_working_params['roles_dict'][role].items():
            if name not in case_working_params['roles_dict'][role]:
                case_working_params['roles_dict'][role][name] = item
            else:
                # name appears in both base and case params
                msg_logger.msg(f'In role {role} the classes named {name} is in both the case and base case params, ignoring base case version',
                               crumbs=f'{crumbs} > case number {case_working_params["caseID"]}',
                               hint='Delete either base case or case parameters of this name to remove this warning',  warning=True)

        pass
    return case_working_params



