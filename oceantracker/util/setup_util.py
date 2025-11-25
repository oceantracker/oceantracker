import importlib
from os import  environ, path, mkdir
from copy import copy, deepcopy
from datetime import datetime
import shutil
from os import path, makedirs, walk, unlink
import traceback
from oceantracker.util import json_util
import  numpy as np
from oceantracker import definitions
from oceantracker.shared_info import  shared_info as si
import sys

def setup_output_dir(settings, crumbs='', caller=None):
    # setus up params, opens log files/ error handling, required before message loger can be used
    crumbs += '> setup_output_dir'

    # check output_file_base is not dir, just a test
    if len(path.dirname(settings['output_file_base'])) > 0:
        si.msg_logger.msg(
            f'The setting "output_file_base" cannot include a directory only a text label, given output_file_base ="{settings["output_file_base"]}"',
            error=True,
            hint='Use setting "root_output_dir" to designate which dir. to place output files in',
            crumbs=crumbs, caller=caller,
            fatal_error=True)

    # get output files location
    root_output_dir = path.abspath(path.normpath(settings['root_output_dir']))
    run_output_dir = path.join(root_output_dir, settings['output_file_base'])

    if settings['add_date_to_run_output_dir']:
        run_output_dir += datetime.now().strftime("_%Y-%m-%d_%H-%M")

    # if restable and no folder exists them make a new restart folder  existing folder and make a new dir, if not restarting
    saved_state_dir = path.join(run_output_dir, 'saved_state')
    si.run_info.restarting = False
    if si.settings.restart_interval is not None \
            and path.isdir(saved_state_dir)  \
            and path.isfile(path.join(saved_state_dir,'state_complete.txt')):
                si.run_info.restarting = True

    # new run if  not restarting or incomplete saved state
    if not si.run_info.restarting:
        if path.isdir(run_output_dir):  shutil.rmtree(run_output_dir)
        makedirs(run_output_dir)  # make  new clean folder

    # write a copy of user given parameters, to help with debugging and code support
    fb = 'users_params_' + settings['output_file_base']
    output_files = {'root_output_dir': root_output_dir,
                    'run_output_dir': run_output_dir,
                    'saved_state_dir': saved_state_dir,
                    'output_file_base': settings['output_file_base'],
                    'raw_output_file_base': copy(settings['output_file_base']),
                    # this is needed for grid file so it does not get a case number in // runs
                    'caseInfo_file': settings['output_file_base'] + '_caseInfo.json',
                    'users_params_json': fb + '.json',
                    }
    return output_files

def write_raw_user_params(output_files, params,msg_logger):
    fn= output_files['output_file_base']+'_raw_user_params.json'
    output_files['raw_user_params'] = fn
    json_util.write_JSON(path.join(output_files['run_output_dir'],  output_files['raw_user_params']),params)
    msg_logger.msg(f'to help with debugging, parameters as given by user  are in "{output_files["raw_user_params"]}"',  tabs=2, note=True)

def build_working_params(params, msg_logger, crumbs='', caller=None):

    crumbs += '> decompose_params'
    working_params = dict(settings= {},
             core_class_roles = {k: None for k in si.core_class_roles.possible_values()},  # insert full list and defaults
             class_roles = {k: [] for k in si.class_roles.possible_values()},
             reader = {},
             nested_readers= [],
             )

    setting_keys = si.default_settings.possible_values()
    core_role_keys = si.core_class_roles.possible_values()
    role_keys =  si.class_roles.possible_values()
    known_top_level_keys =  setting_keys + core_role_keys + role_keys

    # split and check for unknown keys
    for key, item in params.items():
        k = copy(key)
        if len(k) != len(k.strip()):
            msg_logger.msg(f'Removing leading or trailing blanks from top level parameter key "{key}"', warning=True, crumbs=crumbs,caller=caller)
            k = key.strip()  # remove leading/trailing blanks

        if type(item) == tuple:
            # check item not a tuple
            msg_logger.msg(f'Top level parameters must be key : value pairs of a dictionary, got a tuple for key= "{key}", value= "{str(item)}"', error=True, crumbs=crumbs,
                   hint='is there an un-needed comma at the end of the parameter/line?, if a tuple was intentional, then use a list instead', caller=caller)

        elif key == 'reader':
            working_params['reader']= item
        elif key == 'nested_readers':
            working_params['nested_readers'] = item

        elif k in setting_keys:
            working_params['settings'][k] = item

        elif k in core_role_keys:
            working_params['core_class_roles'][k] = item

        elif k in role_keys:
            if type(item) != list:
                msg_logger.msg(f'Params under role key "{k}" must be a list of parameter dictionaries with "class_name" and optional internal "name"'
                               +'\n Roles changed from dict type to list type in new version',
                                       hint =f'Got type {str(type(item))}, value={str(item)}' ,
                                       crumbs=crumbs, error=True)
            working_params['class_roles'][k] = item
        else:
            msg_logger.spell_check('Unknown setting or role as top level param./key, ignoring', key, known_top_level_keys, caller=caller,
                           crumbs=crumbs, link='parameter_ref_toc')

    msg_logger.exit_if_prior_errors('Errors in decomposing parameters into settings, and classes')

    return working_params

def check_python_version(msg_logger):
        # set up log files for run
        ml = msg_logger
        v = definitions.version
        ml.msg(' Python version: ' + v['python_version'], tabs=2)
        p_major =v['python_major_version']
        p_minor= v['python_minor_version']
        install_hint = 'Install Python 3.10 or used environment310.yml to build a Conda virtual environment named oceantracker'
        if not ( p_major > 2 and p_minor >= 9):
            ml.msg('Oceantracker requires Python 3 , version >= 3.10  and < 3.11',
                         hint=install_hint, warning=True, tabs=1)
        if (p_major == 3 and p_minor >= 12):
            ml.msg(f'Oceantracker is compatible with Python {p_major}{p_minor},  however not all external imported packages have been updated to be compatible with 3.12', warning=True,
                   hint='Down grade to python 3.11 if unexplained issues in external packages')

def config_numba_environment_and_random_seed(settings, msg_logger, crumbs='', caller = None):
    # set numba config via environment variables,
    # this must be done before first import of numba

    environ['NUMBA_function_cache_size'] = str(settings['NUMBA_function_cache_size'])

    if settings['NUMBA_cache_code']:
        # use defaul cache location, as setting it fails for some reason
        environ['OCEANTRACKER_NUMBA_CACHING'] = '1'
    else:
        environ['OCEANTRACKER_NUMBA_CACHING'] = '0'

    if settings['debug']:
        environ['NUMBA_DEVELOPER_MODE'] = '1'
        environ['NUMBA_BOUNDSCHECK'] = '1'
        environ['NUMBA_FULL_TRACEBACKS'] = '1'
        environ['NUMBA_DEVELOPER_MODE'] = '1'

    # maxium threads used
    from psutil import cpu_count
    physical_cores=cpu_count( logical=False)
    max_threads = max(physical_cores, 1)
    max_threads = max_threads if settings['processors'] is None else settings['processors']

    # let numba know if using threads, ie processors > 1
    environ['OCEANTRACKER_USE_PARALLEL_THREADS'] = str(int(max_threads >1))

    environ['NUMBA_FASTMATH'] = str(int(settings['NUMBA_fastmath']))

    #environ['NUMBA_PARALLEL_DIAGNOSTICS']= '4'
    #environ['NUMBA_DEBUG'] = '1'

    #  environment variable settings must be used before numbas is first imported
    if 'numba' in sys.modules:
        msg_logger.msg('Numba has already been imported, some numba options may not be used (ignore SVML warning)',
                       hint='Ensure any code using Numba is imported after Oceantracker is run, eg Oceantrackers "load_output_files.py" and "read_ncdf_output_files.py"',
                       warning=True)
    else:
        environ['NUMBA_NUM_THREADS']  = str(max_threads)

    from numba import njit, set_num_threads
    set_num_threads(max_threads)
    settings['processors'] = max_threads # adjust setting thread number to match max possible


    msg_logger.hori_line()
    msg_logger.msg(f'Numba setup: applied settings, max threads = {max_threads}, physical cores = {physical_cores}',
                    hint=f" cache code = { settings['NUMBA_cache_code']}, fastmath= {settings['NUMBA_fastmath']}")
    msg_logger.hori_line()
    # make buffer to hold indicies found by each thread

    @njit
    def set_seed(value):
        np.random.seed(value)

    if settings['use_random_seed']:
            np.random.seed(0)  # set numpy
            set_seed(0) # set numba seed which is different from numpys
            msg_logger.msg('Using numpy.random.seed(0),seed_numba_random(0) makes results reproducible (only use for testing developments give the same results!)', warning=True)



def merge_settings(settings, default_settings, msg_logger, settings_to_merge=None, crumbs='', caller=None):
    crumbs += '> merge_settings'
    all_settings = default_settings.possible_values()

    # for base case merge all settings
    if settings_to_merge is None:
        settings_to_merge = all_settings

    for key in settings_to_merge:
        pvc = getattr(default_settings, key)
        c = f'{crumbs}{key}> setting = "{key}"'

        if key not in settings or settings[key] is None:
            if pvc.is_required:
                msg_logger.msg(f'Settings "{key}" is required.', error=True, caller=caller, crumbs=c)
            else:
                settings[key] = pvc.get_default()
        elif key in all_settings:
            settings[key] = pvc.check_value(key, settings[key], msg_logger,
                                             crumbs= crumbs + f'> setting = "{key}"', caller=caller)
        else:
            msg_logger.spell_check(f'Unrecognized setting "{key}"',key, all_settings,
                            crumbs = crumbs + f'> {key}', caller=caller)
        pass
    return settings

def _build_working_params(params, msg_logger, crumbs=''):
    # slit params into settings, core_class_params and close_role params and merge settings
    crumbs += 'build_working_params'
    ml = msg_logger
    if type(params) != dict:
        ml.msg('Parameters must be of type dict, ', hint=f'Got type {str(type(params))} ',
               fatal_error=True)

    # check for reader classes
    if 'reader' not in params or len(params['reader']) < 2:
        ml.msg('Parameter "reader" is required, or missing required parameters',
               hint='Add a "reader" top level key to parameters with a dictionary containing  at least "input_dir" and "file_mask" keys and values',
               error=True, crumbs='case_run_set_up')

    # split apart params and case list

    if 'case_list' in params:
        ml.msg(
            'Cases run as seperate parallel processes are no longer supported, computations are now parallelized within a single process using threads',
            hint='Remove case_list argument and merge parameters with base case and computations  will automatically be run on parallel threads by default',
            fatal_error=True)

    working_params = build_working_params(params, msg_logger=ml,
                                          crumbs=crumbs + ' Forming working params ')

    # get defaults of settings only
    working_params['settings'] = merge_settings(working_params['settings'], si.default_settings,
                                                           ml, crumbs=crumbs)
    return working_params






