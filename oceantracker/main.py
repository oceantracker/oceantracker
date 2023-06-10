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

from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util import basic_util , get_versions_computer_info
from oceantracker.util import json_util ,yaml_util

from oceantracker.util.parameter_checking import merge_params_with_defaults


from oceantracker import common_info_default_param_dict_templates as common_info

from oceantracker.util.parameter_util import make_class_instance_from_params
from oceantracker.util.messgage_logger import GracefulError, MessageLogger
from oceantracker.reader.util import check_hydro_model

import traceback
OTname = common_info.package_fancy_name

def run(params):
    ot= OceanTracker(params)
    case_info_files, has_errors = ot.run()
    return case_info_files, has_errors



class OceanTracker():
    def __init__(self,params=None):
        self.params= param_template() if params is None else params
        self.msg_logger = MessageLogger('startup:')

    def settings(self, **kwargs):
        ml = self.msg_logger
        for key in kwargs:
            if key not in common_info.all_default_settings.keys():
                ml.msg(f'setting "{key}" is not recognised, ignoring', warning=True,link=None)
            else:
                self.params[key]= kwargs[key]

    def add_class(self, class_type, **kwargs):
        ml = self.msg_logger
        if class_type in common_info.core_classes:
            # single class
            self.params[class_type] = kwargs

        elif class_type in common_info.class_dicts:
            # can have more than one classs
            if 'name' not in kwargs:
                ml.msg(f'add_class_dict() : for class_type"{class_type}" must have a name parameter, eg. name=my_{class_type}1' ,
                       fatal_error=True, hint= f'the can be more than one {"{class_type}"}, so each must have a unique name')
            name =kwargs["name"]
            if 'name' in self.params[class_type]:
                ml.msg(f'class type "{class_type}" already has a class named "{name}", igoring later versions', warning=True)
            else:
                # add params to  class type of given name
                self.params[class_type][name]={} # add blank param dict
                for key in kwargs:
                    if key != 'name':
                        self.params[class_type][name][key] = kwargs[key]
        else:
            ml.msg(f'class type "{class_type}" is not recognised ', fatal_error=True,link=None)

    def run(self):
        # run oceantracker
        params = self.params
        ml =self.msg_logger
        ml.exit_if_prior_errors('parameters have errors')

        ml.insert_screen_line()
        ml.msg(OTname +'- preliminary setup')
        self._check_python_version()
        t0 = perf_counter()

        if type(params) == dict:
            # single case
            case_info_files, has_errors =self._run_single(params)

        elif type(params) == list:
            #run list of cases in  parallel
            case_info_files, has_errors = self._run_parallel(params)
        else:
            ml.msg('parameters must be a parameter dictionary, or a list parameter dictionaries, params is type = ' + str(type(params)),
                           crumbs='oceantracker.main.run(params',fatal_error=True, exit_now=True)

        # final info output
        self._write_run_info_json(case_info_files, has_errors,t0)
        ml.close()

        return case_info_files, has_errors

    def _run_single(self, user_given_params):
        ml = self.msg_logger
        # keep oceantracker_case_runner out of main namespace
        from oceantracker.oceantracker_case_runner import OceanTrackerCaseRunner

        params = deepcopy(user_given_params)

        working_params = self._decompose_params(params)

        working_params = self._get_hindcast_file_info(working_params)
        working_params= self._setup_output_folders(params, working_params)
        self._write_raw_user_params(user_given_params, working_params)
        o = working_params['output_files']
        o['run_log'],o['run_error_file']= ml.set_up_files(o['run_output_dir'],o['output_file_base'])
        ml.exit_if_prior_errors('errors in top level settings parameters')
        ot = OceanTrackerCaseRunner()
        case_info_file, has_errors = ot.run(working_params)
        return case_info_file, has_errors

    def _run_parallel(self,user_given_params):
        # run list of case params
        ml = self.msg_logger
        params = deepcopy(user_given_params)
        w0 = self._decompose_params(params[0])
        ml.exit_if_prior_errors('first case parameter errors')
        w0 = self._get_hindcast_file_info(w0)
        w0 = self._setup_output_folders(params, w0)
        self._write_raw_user_params(user_given_params, w0)

        o = w0['output_files']
        o['run_log'], o['run_error_file'] = ml.set_up_files(o['run_output_dir'], o['output_file_base'])

        # get list working params, with setting merged with defaults
        working_params_list = []
        for n_case, p in enumerate(params):
            # decompose params but innore share params , as they come from first case
            # overwrite shared params from first case
            tag = 'case #' + str(n_case)
            working_params = self._decompose_params(p, add_shared_settings=False)
            ml.exit_if_prior_errors('parameter errors case ' + tag)
            working_params['shared_settings'] = w0['shared_settings'] # used first cases shared settings
            working_params['processorID'] = n_case

            working_params['output_files'] = deepcopy(w0['output_files'])
            working_params['output_files']['output_file_base'] += '_C%03.0f' % (n_case)
            working_params['hindcast_is3D'] = w0['hindcast_is3D']
            working_params['file_info'] = w0['file_info']
            working_params_list.append(working_params)

        num_proc = working_params_list[0]['shared_settings']['processors']
        num_proc = min(num_proc, len(working_params_list))
        ml.progress_marker('oceantracker:multiProcessing: processors:' + str(num_proc))

        # run // cases
        with multiprocessing.Pool(processes=num_proc) as pool:
            case_results = pool.map(self._run1_case, working_params_list)

        ml.progress_marker('parallel pool complete')

        # write run info json

        case_info_files=[x[0] for x in case_results]
        has_errors = [x[1] for x in case_results]
        return case_info_files, has_errors

    def _run1_case(self,working_params):
        # run one process on a particle based on given family class parameters
        # by creating an independent instances of  model classes, with given parameters

        # keep oceantracker_case_runner out of main namespace
        from oceantracker.oceantracker_case_runner import OceanTrackerCaseRunner

        ot = OceanTrackerCaseRunner()
        caseInfo_file, case_error = ot.run(deepcopy(working_params))
        return caseInfo_file, case_error

    def _decompose_params(self, params, add_shared_settings=True):
        ml = self.msg_logger
        w={'processorID':0, 'shared_settings':{},'case_settings':{},
           'core_classes':deepcopy(common_info.core_classes), # insert full lis and defaults
           'class_dicts': deepcopy(common_info.class_dicts),
           }

        # split and check for unknown keys
        for key, item in params.items():
            k = key

            if type(item) is tuple:
                # check item not a tuple
                ml.msg(f'Top level setting or class must be "key" : value pairs, got a tuple for key= "{key}", value= "{str(item)}"', fatal_error=True,
                               hint='is there an un-needed comma at the end of the parameter/line?, if a tuple was intentional, then use a list instead ')

            elif k in common_info.shared_settings_defaults.keys():
                if add_shared_settings:
                    w['shared_settings'][k] = item
            elif k in common_info.case_settings_defaults.keys():
                    w['case_settings'][k] = item
            elif k in common_info.core_classes.keys():
                w['core_classes'][k].update(item)

            elif k in common_info.class_dicts.keys():
                if type(item) is not dict:
                    ml.msg('class dict type "' + key +'" must contain a dictionary, where key is name of class, value is a dictionary of parameters',
                                     hint = ' for this key got type =' +str(type(item)),
                                   fatal_error=True)
                w['class_dicts'][k] = item

            else:
                ml.msg('Unknown top level parameter "' + key +'"', warning=True)

        # check require classes are given
        if 'reader' not in w['core_classes'] :
            ml.msg( 'Parameter "reader_class" or "reader" or  is required',
                           hint='Add a "reader_class" top level key to parameters with a dictionary containing  at least "input_dir" and file mask keys and values', fatal_error=True)

        if 'release_groups' not in w['class_dicts'] :
            ml.msg( 'Parameter "release_groups_dict" or "release_groups" or  is required',
                           hint=' add a least one named release group class to the "release_groups_dict" key', fatal_error=True)

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
        reader_params =  working_params['core_classes']['reader']

        if 'input_dir' not in reader_params or 'file_mask' not in reader_params:
            ml.msg('Reader requires settings, "input_dir" and "file_mask" to read the hindcast',fatal_error=True, exit_now=True )

        if 'class_name' not in  reader_params:
            # infer class name from netcdf files if possible
            reader_params= check_hydro_model.check_fileformat(reader_params, ml)


        reader = make_class_instance_from_params(reader_params, ml,  class_type_name='reader')
        ml.exit_if_prior_errors() # class name missing or missimg requied variables

        #todo check hindacst dir exists??
        working_params['file_info'] ,working_params['hindcast_is3D'] = reader.get_hindcast_files_info() # get file lists

        ml.progress_marker('sorted hyrdo-model files in time order', start_time=t0)

        return working_params


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

    def  _write_raw_user_params(self, params, working_params):
        ml = self.msg_logger
        o= working_params['output_files']
        fn= o['output_file_base']+'_raw_user_params.json'
        o['raw_user_params'] = fn
        json_util.write_JSON(path.join(o['run_output_dir'],fn),params)
        ml.msg('to help with debugging, parameters as given by user  are in "' + fn + '"',
                       tabs=2, note=True)

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


    def _write_run_info_json(self, case_info_files, has_errors,  t0):
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
                sinfo = c['class_info']['solver']
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