# method to run ocean tracker from parameters
# eg run(params)
import sys



# todo kernal/numba based RK4 step
# todo short name map requires unique class names in package, this is checked on startup,add checks of uniqueness of user classes added from outside package

# Dev notes
# line debug?? python3.6 -m pyinstrument --show-all plasticsTrackOnLine_Main.py
# python -m cProfile
# python -m vmprof  <program.py> <program parameters>
# python -m cProfile -s cumtime

# do first to ensure its right
import multiprocessing

from copy import deepcopy
from datetime import datetime

from os import path, makedirs
from sys import version, version_info
import shutil
from time import perf_counter
from copy import  copy
import numpy as np
import difflib
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util import basic_util , get_versions_computer_info
from oceantracker.util import json_util ,yaml_util

from oceantracker.util.parameter_checking import merge_params_with_defaults


from oceantracker import common_info_default_param_dict_templates as common_info

from oceantracker.util.parameter_util import make_class_instance_from_params
from oceantracker.util.messgage_logger import GracefulError, MessageLogger
from oceantracker.reader.util import check_hydro_model

from oceantracker.util import  spell_check_util

import traceback
OTname = common_info.package_fancy_name

def run(params):
    ot= OceanTracker()
    case_info_files = ot._run_single(params)
    return case_info_files

def run_parallel(base_case_params, case_list_params=[{}]):
    ot= OceanTracker()
    case_info_files  = ot._run_parallel(base_case_params, case_list_params)
    return case_info_files

class OceanTracker():
    def __init__(self,params=None):
        self.params= param_template() if params is None else params
        self.msg_logger = MessageLogger('helper')
    # helper methods
    def settings(self, **kwargs):
        for key in kwargs:
            self.params[key]= kwargs[key]

    def add_class(self, class_role, **kwargs):
        ml = self.msg_logger
        known_classes = list(common_info.class_dicts.keys()) \
                     + list(common_info.core_classes.keys())
        if class_role in common_info.core_classes:
            # single class
            self.params[class_role] = kwargs

        elif class_role in common_info.class_dicts:
            # can have more than one classs
            if 'name' not in kwargs:
                ml.msg(f'add_class_dict() : for class_role"{class_role}" must have a name parameter, eg. name=my_{class_role}1, ignoring this class' ,
                       fatal_error=True,
                       hint= f'the can be more than one {"{class_role}"}, so each must have a unique name')
                return
            name =kwargs["name"]
            if name in self.params[class_role]:
                ml.msg(f'class type "{class_role}" already has a class named "{name}", ignoring later versions', warning=True)
            else:
                # add params to  class type of given name
                self.params[class_role][name]={} # add blank param dict
                for key in kwargs:
                    if key != 'name':
                        self.params[class_role][name][key] = kwargs[key]
        else:
            spell_check_util.spell_check(class_role, known_classes, ml, 'in add_class(), ignoring this class',
                        crumbs=f'class type "{class_role}"')
        pass

    def run(self):
        # helper method to rub single case of oceantracker
        params = self.params
        case_info_file = self._run_single(params)
        return case_info_file

    #  other, non helper methods
    def _run_single(self, user_given_params):
        self.helper_msg_logger = self.msg_logger  # keep references to write message at end as runs has main message logger

        ml = self.msg_logger
        # keep oceantracker_case_runner out of main namespace
        from oceantracker.oceantracker_case_runner import OceanTrackerCaseRunner

        working_params = self._main_run_set_up(user_given_params)

        # make instance of case runer and run it with decomposed working params
        ot = OceanTrackerCaseRunner()
        case_info_file, case_msg = ot.run(working_params)

        if case_info_file is None:
            ml.msg('case_info_file is None, run may not have completed', fatal_error=True)

        self._main_run_end(case_info_file, len(case_msg['errors']), len(case_msg['warnings']), len(case_msg['notes']))

        return case_info_file

    def _main_run_set_up(self,user_given_params, case_list_params=None,full_checks=True):
        # set up new messagelogger to allow reruns of helper method
        self.msg_logger = MessageLogger('main')
        ml =self.msg_logger

        ml.insert_screen_line()
        ml.msg(OTname +'- preliminary setup')
        self._check_python_version()

        ml.exit_if_prior_errors('parameters have errors')

        self.start_t0 = perf_counter()
        self.start_date = datetime.now()

        params = deepcopy(user_given_params)

        working_params = self._decompose_params(params, full_checks=full_checks)
        working_params, reader_params = self._get_hindcast_file_info(working_params)
        working_params = self._setup_output_folders(params, working_params)
        self._write_raw_user_params(working_params['output_files'],user_given_params, case_list=case_list_params)

        o = working_params['output_files']
        o['run_log'], o['run_error_file'] = ml.set_up_files(o['run_output_dir'], o['output_file_base'])
        ml.exit_if_prior_errors('errors in top level settings parameters')

        return working_params

    def _main_run_end(self,case_info_files, num_case_errors,num_case_warnings,num_case_notes):
        # final info output
        ml = self.msg_logger
        self._write_run_info_json(case_info_files, self.start_t0)

        ml.show_all_warnings_and_errors()

        # rewite any help class error/warnings
        ml_helper = self.helper_msg_logger
        for l in ml_helper.errors_list:
            ml.msg(l)
        for l in ml_helper.warnings_list:
            ml.msg(l)

        ml.insert_screen_line()
        ml.msg(f'OceanTracker summary:  elapsed time =' + str(datetime.now() - self.start_date),)

        ml.msg(f'Cases - {num_case_errors:3d} errors, {num_case_warnings:3d} warnings, {num_case_notes:3d} notes, check above', tabs=3)
        ml.msg(f'Helper- {len(ml_helper.errors_list):3d} errors, {len(ml_helper.warnings_list):3d} warnings, {len(ml_helper.notes_list):3d} notes, check above', tabs=3)
        ml.msg(f'Main  - {len(ml.errors_list):3d} errors, {len(ml.warnings_list):3d} warnings, {len(ml.notes_list):3d} notes, check above', tabs=3)

        ml.insert_screen_line()
        ml.close()

    def _run_parallel(self,base_case_params, case_list_params):
        # run list of case params
        self.helper_msg_logger = self.msg_logger  # keep references to write message at end as runs has main message logger

        # set up using base case, which must have reader
        # first put base_case into the te,plate, to ensure all keys are present
        base_case_params_full = param_template()
        base_case_params_full.update(base_case_params)
        working_bc =self._main_run_set_up(base_case_params_full, full_checks=False)
        ml = self.msg_logger
        ml.exit_if_prior_errors('base case parameter errors')

        # get defaults for setting of base case shared settings used for all cases
        for key, item in common_info.shared_settings_defaults.items():
            working_bc['shared_settings'] =   working_bc['shared_settings']  if item is not None else item.get_default()

        # work out how many processors to use
        c =get_versions_computer_info.get_computer_info()
        if working_bc['shared_settings']['processors'] is None:
            working_bc['shared_settings']['processors']  = min(max(c['CPUs_hardware']-1,1),  len(case_list_params))


        # get list working params, with setting merged with defaults
        working_case_list = []
        for n_case, p in enumerate(case_list_params):
            # decompose params but ignore share params , as they come from first case
            # overwrite shared params from first case
            msg_tag = ' Building parallel run case #' + str(n_case)

            # remove reader if present in case, will get base case reader below
            if 'reader' in p :
                if len(p['reader']) > 0:
                    ml.msg(f'Reader class can only be set in base case', crumbs=msg_tag, warning=True, hint='ignoring this cases reader class')
                p.pop('reader')
            working_params = self._decompose_params(p, full_checks=False)

            # build up full params
            # copy shared setting from base case, merging with defaults
            for key, item in working_bc['shared_settings'].items():
                if key in p and p[key] is not None: # check if present and given by template
                    ml.msg(f'Setting "{key}" must be the same for all cases', crumbs=msg_tag,  warning=True, hint='ignoring the setting in case list and using base case setting ')
                # get given base case or default value
                working_params['shared_settings'][key] = item if item is not None else common_info.shared_settings_defaults[key].get_default()

            # for other settings, use the case list if presents, or use default if not in bas case
            for key, item in working_bc['case_settings'].items():
                if key in p and p[key] is not None:
                    working_params['case_settings'][key] = p[key]
                else:
                    working_params['case_settings'][key] = item if item is not None else common_info.case_settings_defaults[key].get_default()

            # copy over core classes
            for key, item in working_bc['core_roles'].items():
                if key == 'reader':
                    working_params['core_roles']['reader'] = item
                else:
                    working_params['core_roles'][key] = deepcopy(item)
                    if key in p:
                        # update base case with any case key-value pairs
                        working_params['core_roles'][key].update(p[key])

            # add class dict to full case
            for role in working_bc['role_dicts'].keys():
                # add with base case names
                for name, item in working_bc['role_dicts'][role].items():
                    working_params['role_dicts'][role][name] = item

                # add case list named classes if role in p
                for name, item in working_params['role_dicts'][role].items():
                    if name in base_case_params_full[role]:
                        ml.msg(f'For the  class role "{role}", the named class "{name}" has been used in the base for case' , warning=True,
                                   hint= 'names should be unique, will ignore class in the base case', crumbs=msg_tag)
                        working_params['role_dicts'][role][name] = item

            # check at least one release group from base or case params
            if len(working_params['role_dicts']['release_groups']) ==0:
                ml.msg(f'Must have at lest one release group from base case parms or case list', fatal_error=True,
                       hint='check "release_groups" key in both base and case list parameters', crumbs=msg_tag)

            ml.exit_if_prior_errors('parameter errors case ' + msg_tag)

            # add and tweak output file info
            working_params['caseID'] = n_case
            working_params['output_files'] = deepcopy(working_bc['output_files'])
            working_params['output_files']['output_file_base'] += '_C%03.0f' % (n_case)
            working_params['hindcast_is3D'] = working_bc['hindcast_is3D']
            working_params['file_info'] = working_bc['file_info']

            # now add to list to run
            working_case_list.append(deepcopy(working_params))

        # do runs
        num_proc = working_bc['shared_settings']['processors']
        ml.progress_marker(' oceantracker:multiProcessing: processors:' + str(num_proc))

        # run // cases
        with multiprocessing.Pool(processes=num_proc) as pool:
            case_results = pool.map(self._run1_case, working_case_list)

        ml.progress_marker('parallel pool complete')

        # get case files and  error/warning counts
        case_msg=[]
        num_warnings= 0
        num_errors = 0
        num_notes = 0
        case_info_files =[]
        for n, c in  enumerate(case_results):
            if c[0] is None:
                ml.msg(f'Case #{n:03}, failed to finish', fatal_error=True, hint='hint see above, any case errors detected are listed below')
                for m in c[1]['errors']:
                    ml.msg(m, tabs =2)
            case_info_files.append(c[0])
            case_msg.append(c[1])
            num_errors += len(c[1]['errors'])
            num_warnings += len(c[1]['warnings'])
            num_notes += len(c[1]['notes'])

        self._main_run_end(case_info_files,num_errors,num_warnings,num_notes)
        return case_info_files

    @staticmethod
    def _run1_case(working_params):
        # run one process on a particle based on given family class parameters
        # by creating an independent instances of  model classes, with given parameters

        # keep oceantracker_case_runner out of main namespace
        from oceantracker.oceantracker_case_runner import OceanTrackerCaseRunner

        ot = OceanTrackerCaseRunner()
        caseInfo_file, return_msgs= ot.run(deepcopy(working_params))
        return caseInfo_file, return_msgs

    def _decompose_params(self, params, full_checks=True, crumbs=None):
        ml = self.msg_logger
        w={'caseID':0, 'shared_settings':{},'case_settings':{},
           'core_roles':deepcopy(common_info.core_classes), # insert full lis and defaults
           'role_dicts': deepcopy(common_info.class_dicts),
           }

        known_top_level_keys= list(common_info.shared_settings_defaults.keys())\
                            + list(common_info.case_settings_defaults.keys()) \
                            + list(common_info.class_dicts.keys()) \
                            +list(common_info.core_classes.keys())

        # check for compulsory classes
        # check require classes are given
        if full_checks:
            if len(params['reader']) < 2:
                ml.msg('Parameter "reader" is required, got ' +str(params['reader']),
                       hint='Add a "reader" top level key to parameters with a dictionary containing  at least "input_dir" and "file_mask" keys and values',
                       fatal_error=True, crumbs=crumbs)

        if full_checks:
            if  'release_groups' not in  params or len(params['release_groups']) < 1:
                ml.msg('Parameter "release_groups" is required, with at least one named release group',
                       hint=' add a least one named release group class to the "release_groups" key',
                       fatal_error=True,crumbs=crumbs)

        # split and check for unknown keys
        for key, item in params.items():
            k = copy(key)
            if len(k) != len(k.strip()):
                ml.msg(f'Removing leading or trailing blanks from top level parameter key "{key}"', warning=True)
                k = key.strip() # remove leading/trailing blanks

            if type(item) is tuple:
                # check item not a tuple
                ml.msg(f'Top level setting or class must be "key" : value pairs, got a tuple for key= "{key}", value= "{str(item)}"', fatal_error=True,crumbs=crumbs,
                               hint='is there an un-needed comma at the end of the parameter/line?, if a tuple was intentional, then use a list instead')

            elif k in common_info.shared_settings_defaults.keys():

                if key not in common_info.all_default_settings.keys():
                    spell_check_util.spell_check(key, common_info.all_default_settings.keys(), ml,'ignoring this setting',
                                crumbs=crumbs + f' setting "{key}"')
                else:
                    w['shared_settings'][k] = item

            elif k in common_info.case_settings_defaults.keys():
                    w['case_settings'][k] = item
            elif k in common_info.core_classes.keys():
                w['core_roles'][k].update(item)

            elif k in common_info.class_dicts.keys():
                if type(item) is not dict:
                    ml.msg('class dict type "' + key +'" must contain a dictionary, where key is name of class, value is a dictionary of parameters',
                                     hint = ' for this key got type =' +str(type(item)),
                                   fatal_error=True, crumbs=crumbs)
                w['role_dicts'][k] = item

            else:
                spell_check_util.spell_check(key,known_top_level_keys,ml,' top level parm./key, ignoring')

        ml.exit_if_prior_errors('Errors in decomposing parameters')
        # merge settings params
        w['shared_settings'] = merge_params_with_defaults(w['shared_settings'],  common_info.shared_settings_defaults,
                                ml, crumbs='merging settings and checking against defaults')
        w['case_settings'] = merge_params_with_defaults(w['case_settings'], common_info.case_settings_defaults,
                                                          ml, crumbs='merging settings and checking against defaults')
        return w


    def _get_hindcast_file_info(self, working_params ):
        # created a dict which can be used to build a reader
        t0= perf_counter()
        ml = self.msg_logger
        reader_params =  working_params['core_roles']['reader']

        if 'input_dir' not in reader_params or 'file_mask' not in reader_params:
            ml.msg('Reader class requires settings, "input_dir" and "file_mask" to read the hindcast',fatal_error=True, exit_now=True )

        if 'class_name' not in reader_params:
            # infer class name from netcdf files if possible
            reader_params= check_hydro_model.check_fileformat(reader_params, ml)

        reader = make_class_instance_from_params('reader', reader_params, ml,  class_role_name='reader')
        ml.exit_if_prior_errors() # class name missing or missing requied variables

        working_params['file_info'] ,working_params['hindcast_is3D'] = reader.get_hindcast_files_info(ml) # get file lists

        ml.progress_marker('sorted hyrdo-model files in time order', start_time=t0)

        return working_params, reader_params


    def _setup_output_folders(self, user_given_params,working_params):
        # setus up params, opens log files/ error handling, required befor mesage loger can be used
        ml = self.msg_logger
        settings= working_params['shared_settings']
        # get output files location
        root_output_dir = path.abspath(path.normpath(settings['root_output_dir']))
        run_output_dir = path.join(root_output_dir, settings['output_file_base'])

        if settings['add_date_to_run_output_dir']:
            run_output_dir += datetime.now().strftime("_%Y-%m-%d_%H-%M")

        # kill existing folder
        if path.isdir(run_output_dir):  shutil.rmtree(run_output_dir)

        try:
            makedirs(run_output_dir)  # make  and clear out dir for output
        except OSError as e:
            # path may already exist, but if not through other error, exit
            ml.msg(f'Failed to make run output dir:{run_output_dir}',
                           exception=e, traceback_str=traceback.print_exc())

        # write a copy of user given parameters, to help with debugging and code support
        fb = 'users_params_' + settings['output_file_base']
        json_util.write_JSON(path.join(run_output_dir, fb), user_given_params)

        working_params['output_files'] = {'root_output_dir': root_output_dir,
                                       'run_output_dir': run_output_dir,
                                       'output_file_base': settings['output_file_base'],
                                       'runInfo_file': settings['output_file_base'] + '_runInfo.json',
                                       'runLog_file': settings['output_file_base'] + '_runScreen.log',
                                       'run_error_file': settings['output_file_base'] + '_run.err',
                                       'users_params_json': fb + '.json',
                                       }
        ml.msg('output is in dir= ' + run_output_dir,tabs=2, note=True)
        return working_params

    def  _write_raw_user_params(self,output_files, params, case_list=None):
        ml = self.msg_logger

        # different if run in parallel
        if case_list is None:
            out = params
        else:
            out = {'base_case_params': params, 'case_list_params': case_list}

        fn= output_files['output_file_base']+'_raw_user_params.json'
        output_files['raw_user_params'] = fn
        json_util.write_JSON(path.join(output_files['run_output_dir'],fn),out)
        ml.msg('to help with debugging, parameters as given by user  are in "' + fn + '"',  tabs=2, note=True)

    def _check_python_version(self):
            # set up log files for run
            ml = self.msg_logger
            v = get_versions_computer_info.get_code_version()
            ml.msg(' Python version: ' + v['python_version'], tabs=2)
            p_major =v['python_major_version']
            p_minor= v['python_minor_version']
            install_hint = 'Install Python 3.10 or used environment.yml to build a Conda virtual environment named oceantracker'
            if not ( p_major > 2 and p_minor >= 9):
                ml.msg(common_info.package_fancy_name + ' requires Python 3 , version >= 3.9  and < 3.11',
                             hint=install_hint, warning=True, tabs=1)
            if (p_major == 3 and p_minor >= 11):
                ml.msg(common_info.package_fancy_name + ' is not yet compatible with Python 3.11, as not all imported packages have been updated, eg Numba')

            ml.exit_if_prior_errors()


    def _write_run_info_json(self, case_info_files, t0):
        # read first case info for shared info
        ml = self.msg_logger
        ci = deepcopy(case_info_files) # dont alter input
        if type(ci) is not list: ci= [ci]

        # finally get run totals of steps and particles across al cases and write
        n_time_steps = 0.
        total_alive_particles = 0
        case_info_list=[]
        # load log files to get info on run from solver info
        for n, case_file  in enumerate(ci) :

            if case_file is not None :
                c= json_util.read_JSON(case_file)
                sinfo = c['class_roles_info']['solver']
                n_time_steps += sinfo['time_steps_completed']
                total_alive_particles += sinfo['total_alive_particles']
                case_info_list.append(path.basename(case_file))
            else:
                case_info_list.append((None))
                ml.msg(f'Case #{n:d} has no case info file, likley has crashed',warning=True)

        num_cases = len(ci)

        # JSON parallel run info data
        d = {'output_files' :{},
            'version_info': get_versions_computer_info.get_code_version(),
            'computer_info': get_versions_computer_info.get_computer_info(),
            'num_cases': num_cases,
            'elapsed_time' :perf_counter() - t0,
            'average_active_particles': total_alive_particles / num_cases if num_cases > 0 else None,
            'average_number_of_time_steps': n_time_steps/num_cases  if num_cases > 0 else None,
            'particles_processed_per_second': total_alive_particles /(perf_counter() - t0)
             }

        # get output file names
        c0= json_util.read_JSON(ci[0])
        o = c0['output_files']
        d['output_files'] = {'root_output_dir': o['root_output_dir'],
                            'run_output_dir': o['run_output_dir'],
                            'output_file_base': o['output_file_base'],
                            'runInfo_file': o['runInfo_file'],
                            'runLog_file': o['runLog_file'],
                            'run_error_file': o['run_error_file'],
                            'users_params_json': o['raw_user_params'],
                             'caseInfo_files':case_info_list
                             }
        json_util.write_JSON(path.join(o['run_output_dir'],o['runInfo_file']),  d)
        ml.msg('run summary with case file names   "' + o['runInfo_file'] + '"',
                       tabs=2, note=True)

def param_template():
    # return an empty parameter dictionary, with important class keys

    d = {}
    for key in sorted(common_info.all_default_settings.keys()):
        if type(common_info.all_default_settings[key]) is dict:
            d[key] = {}
        else:
            d[key] = None

    for key in sorted(common_info.core_classes.keys()):
        d[key] = {}
    for key in sorted(common_info.class_dicts.keys()):
        d[key] = {}
    return deepcopy(d)