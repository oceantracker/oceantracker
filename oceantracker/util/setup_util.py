import importlib
from os import  environ, path, mkdir
from copy import copy, deepcopy
from datetime import datetime
import shutil
from os import path, makedirs, walk, unlink
import traceback
from oceantracker.util import json_util, time_util
import  numpy as np
from oceantracker import definitions
from oceantracker.shared_info import  shared_info as si
from oceantracker.util import parameter_checking
import sys
from glob import glob

def setup_output_dir():
    # set up output folder, when root_output_dir and output_file_base are required settings
    # check output_file_base is not dir, just a test

    # cope with deprecated params
    if si.settings.run_output_dir is not None:
        run_output_dir = path.abspath(si.settings.run_output_dir)
    else:
        # cope with deprecated params
        if si.settings.root_output_dir is None or si.settings.output_file_base is None:
            si.msg_logger.msg(' settings "root_output_dir" or  "output_file_base" are not set, both are required',
                              hint='These settings are deprecated and replaced by single setting "run_output_dir", set both if you must use them!')

        run_output_dir = path.abspath(path.join(si.settings['root_output_dir'], si.settings['output_file_base']))

    if si.settings['add_date_to_run_output_dir']:
        run_output_dir += datetime.now().strftime("_%Y-%m-%d_%H-%M")

    # create basic  output file names
    output_files = dict(
                    run_output_dir= run_output_dir,
                    caseInfo_file= 'caseInfo.json',
                    saved_state_dir='saved_state',
                    completion_state_dir='completion_state',
                    grid = [] # may be more than one grid if nested
                    )
    if si.settings.restart_interval is not None \
            and path.isdir(output_files['saved_state_dir'])  \
            and path.isfile(path.join(output_files['saved_state_dir'],'state_complete.txt')):
                restarting = True
    else:
        restarting = False

    # kill old run if not restarting
    if not restarting :
        if path.isdir(run_output_dir):  shutil.rmtree(run_output_dir)
        makedirs(run_output_dir)  # make  new clean folder

    return output_files, restarting

def setup_restart_continuation():

    ml = si.msg_logger
    saved_state_info = None
    of = si.output_files

    if si.run_info.restarting:
        # load restart info
        fn = path.join(of['saved_state_dir'], 'state_info.json')
        if not path.isfile(fn):
            ml.msg('Cannot find save_state.json to restart run, to save state rerun with  setting restart_interval',
                   fatal_error=True, hint=f'missing file  {fn}')
        saved_state_info = json_util.read_JSON(fn)
        ml.msg(f'>>>>> restarting failed run at {time_util.seconds_to_isostr(saved_state_info["restart_time"])}')

    elif si.settings.continue_from is not None:
        # continue old run in new folder

        prior_run_output_dir = path.abspath(si.settings.continue_from)
        # find previous run
        if not path.isdir(prior_run_output_dir):
            ml.msg(f'Cannot find output dir of previous run to continue "{si.settings.continue_from}"',
                            fatal_error=True, hint= f'Check dir in continue_from setting')

        # check new run has different run_output dir
        if path.abspath(of['run_output_dir']) == prior_run_output_dir:
            ml.msg(f'The run continuation output cannot be written to same dir as the prevouis run "{si.settings.continue_from}"',
                       fatal_error=True, hint=f'Ensure output_file_base names for prio and continued run are different')

        # check if continuation state exists
        prior_state_dir = path.join(prior_run_output_dir, of['completion_state_dir'])
        if not path.isdir(prior_state_dir) :
            ml.msg( f'Cannot find completion_state dir in previous run"{prior_state_dir}"',
            fatal_error=True,  hint=f'To continue a run, previous run must have setting continuable=True')

        #load state info
        fn = path.join(prior_state_dir, 'state_info.json')
        if not path.isfile(fn):
            ml.msg('Cannot find save_state.json to continue the run',
                   fatal_error=True, hint=f'missing file  {fn}' )

        # load continuation state json file
        saved_state_info = json_util.read_JSON(fn)
        si.run_info.continuing = True

        # copy over files from prior run, but tweak file names to match
        # note msg logger restart copies over log file

        # copy netcdfs
        for fn in glob(path.join(prior_run_output_dir,'*.nc')):
            shutil.copy2(fn, si.run_info.run_output_dir)

    return saved_state_info


def write_raw_user_params(output_files, params,msg_logger):
    fn= 'raw_user_params.json'
    output_files['raw_user_params'] = fn
    json_util.write_JSON(path.join(output_files['run_output_dir'],  fn),params)
    msg_logger.msg(f'to help with debugging, parameters as given by user  are in "{output_files["raw_user_params"]}"',  tabs=2, note=True)

def build_working_params(params, msg_logger,  caller=None):

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
            msg_logger.msg(f'Removing leading or trailing blanks from top level parameter key "{key}"', warning=True, caller=caller)
            k = key.strip()  # remove leading/trailing blanks

        if type(item) == tuple:
            # check item not a tuple
            msg_logger.msg(f'Top level parameters must be key : value pairs of a dictionary, got a tuple for key= "{key}", value= "{str(item)}"',
                    error=True, caller=caller,
                   hint='is there an un-needed comma at the end of the parameter/line?, if a tuple was intentional, then use a list instead')

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
                                       error=True)
            working_params['class_roles'][k] = item
        else:
            msg_logger.spell_check('Unknown setting or role as top level param./key, ignoring', key, known_top_level_keys, caller=caller,
                                        link='parameter_ref_toc')

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
            ml.msg('Oceantracker requires Python 3 , version >= 3.10',
                         hint=install_hint, warning=True, tabs=1)

def config_numba_environment_and_random_seed(settings, msg_logger, caller = None):
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
                       warning=True,caller=caller)
    else:
        environ['NUMBA_NUM_THREADS']  = str(max_threads)

    from numba import njit, set_num_threads
    set_num_threads(max_threads)
    settings['processors'] = max_threads # adjust setting thread number to match max possible


    msg_logger.hori_line()
    msg_logger.msg(f'Numba setup: applied settings, max threads = {max_threads}, physical cores = {physical_cores}',
                    caller = caller ,
                    hint=f" cache code = { settings['NUMBA_cache_code']}, fastmath= {settings['NUMBA_fastmath']}")
    msg_logger.hori_line()
    # make buffer to hold indicies found by each thread

    @njit
    def set_seed(value):
        np.random.seed(value)

    if settings['use_random_seed']:
            np.random.seed(0)  # set numpy
            set_seed(0) # set numba seed which is different from numpys
            msg_logger.msg('Using numpy.random.seed(0),seed_numba_random(0) makes results reproducible (only use for testing developments give the same results!)',
             caller=caller,warning=True)



def _build_working_params(params, msg_logger):
    # slit params into settings, core_class_params and close_role params and merge settings

    ml = msg_logger
    if type(params) != dict:
        ml.msg('Parameters must be of type dict, ', hint=f'Got type {str(type(params))} ',
               fatal_error=True)

    # check for reader classes
    if 'reader' not in params or len(params['reader']) < 2:
        ml.msg('Parameter "reader" is required, or missing required parameters',
               hint='Add a "reader" top level key to parameters with a dictionary containing  at least "input_dir" and "file_mask" keys and values',
               error=True)

    # split apart params and case list

    if 'case_list' in params:
        ml.msg(
            'Cases run as separate parallel processes are no longer supported, computations are now parallelized within a single process using threads',
            hint='Remove case_list argument and merge parameters with base case and computations  will automatically be run on parallel threads by default',
            fatal_error=True)

    working_params = build_working_params(params, msg_logger=ml)

    # get defaults of settings only
    working_params['settings'] = parameter_checking.merge_params_with_defaults(working_params['settings'],
                                                        si.default_settings.asdict(), ml)
    return working_params






