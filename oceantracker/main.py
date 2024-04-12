# method to run ocean tracker from parameters
# eg run(params)
import sys

#


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
import shutil
from time import perf_counter
from copy import  copy
import numpy as np


from oceantracker.util import setup_util, class_importer_util
from oceantracker import definitions

from oceantracker.util import json_util ,yaml_util, get_versions_computer_info
from oceantracker.util.messgage_logger import GracefulError, MessageLogger
from oceantracker.reader.util import get_hydro_model_info

import traceback

from  oceantracker.shared_info import SharedInfo as shared_info

# use separate message logger for actions in main, cases use si.msg_logger
msg_logger = MessageLogger()

OTname = definitions.package_fancy_name
help_url_base = 'https://oceantracker.github.io/oceantracker/_build/html/info/'

def run(params):
    '''Run a single OceanTracker case using given parameters'''
    ot = _OceanTrackerRunner()
    case_info_files = ot.run(params)
    return case_info_files

def run_parallel(base_case_params, case_list_params=[{}]):
    ot = _OceanTrackerRunner()
    case_info_files  = ot.run(base_case_params, case_list_params)
    return case_info_files


class OceanTracker():
    def __init__(self,params=None):
        self.params= {}
        self.case_list_params=[]
        msg_logger.set_screen_tag('helper')
        msg_logger.print_line()
        msg_logger.msg('Starting OceanTracker helper class')
        self.has_run = False

    # helper methods
    def settings(self,case=None, **kwargs):
        # work out if to add to base params or case list params
        existing_params = self._get_case_params_to_work_on(case)
        for key in kwargs:
            existing_params[key]= kwargs[key]

    def add_class(self, class_role:str=None, class_name:str=None, name: str=None, case:int=None,  **kwargs):
        '''
        Add a class instance in given role to computational pipeline, or add settings to a core class
        :param class_role: The role to add or set eg 'release_group'
        :param class_name: Name of class to import, required in some cases. eg "oceantracker.release_groups.polygon_release import PolygonRelease" or short name "PolygonRelease"
        :param name: Name of this instance of added class, used in output and internally to refer to this instance, eg 'my_polygon release'
        :param case: Add this instance to this case ID (>=0) to be run in parallel.
        '''
        ml = msg_logger
        known_class_roles = shared_info.core_roles.possible_values() + shared_info.roles.possible_values()

        if class_role is None:
            ml.msg('oceantracker.add_class, must give first parameter as class role, eg. "release_group"', fatal_error=True, caller =self)
            return

        if type(class_role) != str:
            ml.msg(f'oceantracker.add_class, class_role must be a string', fatal_error=True, caller=self,
                   hint='Given type =' + str(type(class_role)))
            return

        if class_role not in known_class_roles:
            ml.spell_check(f'oceantracker.add_class, class_role parameter is not recognised, value ="{class_role}"',
                           class_role,known_class_roles, fatal_error=True)
            return

        existing_params = self._get_case_params_to_work_on(case)
        if class_role not in existing_params: existing_params[class_role] = {}

        #add class name  if given
        if class_name is not None: kwargs['class_name'] = class_name

        # add new params to core or other roles
        if class_role in shared_info.core_roles.possible_values():
            existing_params[class_role].update(kwargs)
        else:
            #add to mulit component role
            # auto name if needed with camel case role
            if name is None:
                s = class_role.split('_')
                s = [x.title() for x in s]
                s = ''.join(s)
                name = f'{s}_{len(existing_params[class_role]):04d}'

            if 'name' in existing_params[class_role]:# auto name
                msg_logger.msg(f'Class role  "{class_role}" already has a component named "{name}", only using last one given',   warning= True)

            # add users class name or None
            existing_params[class_role][name] = dict(class_name=class_name)
            # add other params to existing params for role and name
            for key in kwargs:
                  existing_params[class_role][name][key] = kwargs[key]
        return

    def _get_case_params_to_work_on(self, case):
        # work out whether to work on base of given case
        if case is None:
            return self.params
        else:
            if type(case) != int or case < 0:
                msg_logger.msg(f'Case keyword must be an integer >=0', fatal_error=True, hint=f'Got value :{str(case)}')


            if case < len(self.case_list_params):
                return self.case_list_params[case] # work on existing case
            elif case >= len(self.case_list_params):
                # expand and fill in any extra cases as empty
                for n in range(len(self.case_list_params), case + 1):  self.case_list_params.append({})
                return self.case_list_params[case] # work on new last one

            else:
                msg_logger.msg(f'Cases must be added in order, have case = {case}',
                               fatal_error=True, hint=f"This would be the {case + 1}'th case added, but only :{len(self.case_list_params)} cases have been added so far" )
                return {}

    def run(self):
        msg_logger.progress_marker('Starting run using helper class')
        ot= _OceanTrackerRunner()
        # todo print helper message here at end??

        case_info_file = ot.run(self.params, self.case_list_params)

        self.has_run = True
        # todo flag use so params can be reset if needed if same OceanTracker instance used more than once
        return case_info_file

class _OceanTrackerRunner(object):
    def __init__(self):
        pass
    
    def run(self, params, case_list_params = None):
        ml = msg_logger
        ml.reset()
        ml.set_screen_tag('Main')

        self.start_t0 = perf_counter()
        self.start_date = datetime.now()

        ml.print_line()
        ml.msg(f'{OTname} starting main:')
        # add package tree to shared info


        # start forming the run builder
        crumbs = 'Forming run builder'
        run_builder = dict(working_params=setup_util.decompose_params(shared_info, deepcopy(params), ml, crumbs= crumbs, caller=self))
        run_builder['version'] = definitions.version

        #  merge defaults of settings which have to be the same for all cases
        critical_settings = ['root_output_dir', 'output_file_base', 'processors', 'max_warnings',
                             'backtracking','add_date_to_run_output_dir','debug','use_random_seed']
        working_params = run_builder['working_params']
        working_params['settings'], self.settings_only_set_in_base_case = setup_util.merge_critical_settings_with_defaults(
                                                                                            working_params['settings'], shared_info.default_settings,
                                                                                            critical_settings,ml, crumbs=crumbs, caller=self)
        ml.exit_if_prior_errors('Errors in merge_critcal_settings_with_defaults',caller=self, crumbs=crumbs)

        # setup output dir and msg files
        t0 = perf_counter()
        o = setup_util.setup_output_dir(working_params['settings'], ml, crumbs= crumbs + '> Setting up output dir')

        o['run_log'], o['run_error_file'] = ml.set_up_files(o['run_output_dir'], o['output_file_base']+'_run') # message logger output file setup
        run_builder['output_files'] = o
        ml.msg(f'Output is in dir "{o["run_output_dir"]}"', hint='see for copies of screen output and user supplied parameters, plus all other output')

        # write raw params to a file
        setup_util.write_raw_user_params(run_builder['output_files'], params, ml, case_list=case_list_params)

        # set numba config environment variables, before any import of numba, eg by readers,
        setup_util.config_numba_environment_and_random_seed(working_params['settings'], ml, crumbs='main setup', caller=self)  # must be done before any numba imports

        ml.print_line()
        ml.msg(f' {OTname} version {definitions.version["str"]} - preliminary setup')

        self._prelimary_checks(params)
        ml.exit_if_prior_errors('parameters have errors')

        # get list of files etc in time order
        run_builder['reader_builder'] = self._get_hindcast_file_info(run_builder)

        if case_list_params is  None or len(case_list_params) == 0:
            # no case list
            case_info_file = self._run_single(run_builder)
        else:
            # run // case list with params as base case defaults for each run
            case_info_file = self._run_parallel(params, case_list_params, run_builder)

        ml.close()
        return case_info_file

    def _run_single(self, run_builder):

        ml = msg_logger
        run_builder['caseID'] = 0 # tag case

        # try catch is needed in notebooks to ensure mesage loger file is close,
        # which allows rerunning in notebook without  permission file errors
        try:
            # keep oceantracker_case_runner out of main namespace
            from oceantracker.oceantracker_case_runner import OceanTrackerCaseRunner
            # make instance of case runer and run it with decomposed working params
            ot_case_runner = OceanTrackerCaseRunner()
            case_summary= ot_case_runner.run_case(run_builder)

        except Exception as e:
            # ensure message loggers are closed

            print(str(e))
            traceback.print_exc()
            return None

        # check is case ran
        if  case_summary['case_info_file'] is None:
            ml.msg('case_info_file is None, run may not have completed', fatal_error=True)

        case_info_files = self._main_run_end( case_summary,run_builder)

        return case_info_files

    def _prelimary_checks(self,params):
        ml = msg_logger

        setup_util.check_python_version(ml)
        # check for compulsory classes
        # check reader params
        if 'reader' not in params or len(params['reader']) < 2:
            ml.msg('Parameter "reader" is required, or missing required parameters',
                           hint='Add a "reader" top level key to parameters with a dictionary containing  at least "input_dir" and "file_mask" keys and values',
                           fatal_error=True, crumbs='case_run_set_up', caller=self)

    def _main_run_end(self,case_summary,run_builder):
        # final info output

        ml = msg_logger
        ml.set_screen_tag('End')
        ml.print_line('Summary')
        ml.msg('Run summary with case file names in "*_runInfo.json"',  tabs=2, note=True)
        ml.show_all_warnings_and_errors()
        ml.print_line( )

        # count total messages
        num_case_errors,num_case_warnings,num_case_notes = 0,0,0
        for c in case_summary if type(case_summary) ==list else [case_summary]:
            m = c['msg_counts']
            num_case_errors +=  m['errors']
            num_case_warnings += m['warnings']
            num_case_notes += m['notes']

        case_info_files= self._write_run_info_json(case_summary,run_builder, self.start_t0)

        ml.print_line()
        ml.msg(f'OceanTracker summary:  elapsed time =' + str(datetime.now() - self.start_date),)
        ml.msg(f'Cases - {num_case_errors:3d} errors, {num_case_warnings:3d} warnings, {num_case_notes:3d} notes, check above', tabs=3)
        ml.msg(f'Main  - {ml.error_count:3d} errors, {ml.warning_count:3d} warnings, {ml.note_count:3d} notes, check above', tabs=3)
        ml.msg(f'Output in {shared_info.run_info.run_output_dir}', tabs=1)
        ml.print_line()
        total_errors = num_case_errors + len(ml.errors_list)
        if total_errors > 0:
            ml.print_line('Found errors, so some cases may not have completed')
            ml.print_line(' ** see above or  *_caseLog.txt and *_caseLog.err files')
            ml.print_line()
        ml.close()
        return case_info_files

    def _run_parallel(self,base_case_params, case_list_params, run_builder):
        # run list of case params
        ml = msg_logger
        # below setting can only be set in base case , and not in parralel cases
        shared_settings_list = [
            'root_output_dir', 'output_file_base', 'add_date_to_run_output_dir',
            'backtracking', 'debug', 'dev_debug_plots',
            'EPSG_code_metres_grid', 'write_tracks', 'display_grid_at_start',
            'NUMBA_cache_code', 'NUMBA_function_cache_size',
            'processors', 'multiprocessing_case_start_delay',
            'max_warnings', 'use_random_seed',
            'write_dry_cell_flag']

        # split base_case_params into shared and case params
        base_working_params = setup_util.decompose_params(shared_info, base_case_params, ml, caller=self, crumbs='_run_parallel decompose base case params')

        comp_info= get_versions_computer_info.get_computer_info()

        bs= base_working_params['settings']
        num_processors = bs['processors'] if 'processors' in bs and bs['processors'] is not None else  max(int(.75*comp_info['CPUs_hardware']),1)

        case_run_builder_list=[]

        for n_case, case_params in enumerate(case_list_params):

            case_working_params = setup_util.decompose_params(shared_info,case_params, msg_logger=ml, caller=self)
            case_working_params =  setup_util.merge_base_and_case_working_params(base_working_params, case_working_params, ml,
                                                                                 crumbs=f'_run_parallel case #[{n_case}]', caller=None)


            ml.exit_if_prior_errors(f'Errors in setting up case #{n_case}')
            case_run_builder = deepcopy(run_builder)
            case_run_builder['caseID'] = n_case
            case_run_builder['working_params'] = case_working_params

            # add and tweak output file info
            case_run_builder['output_files']['output_file_base'] += '_C%03.0f' % (n_case)

            # now add builder to list to run
            case_run_builder_list.append(case_run_builder)

        # do runs num_processors
        ml.progress_marker(' oceantracker:multiProcessing: processors:' + str(num_processors))

        # run // cases
        with multiprocessing.Pool(processes=num_processors) as pool:
            case_summaries = pool.map(self._run1_case, case_run_builder_list)

        ml.progress_marker('parallel pool complete')

        case_info_files = self._main_run_end(case_summaries,run_builder)
        return case_info_files

    @staticmethod
    def _run1_case(working_params):
        # run one process on a particle based on given family class parameters
        # by creating an independent instances of  model classes, with given parameters

        # keep oceantracker_case_runner out of main namespace
        from oceantracker.oceantracker_case_runner import OceanTrackerCaseRunner

        ot = OceanTrackerCaseRunner()
        case_summary= ot.run_case(deepcopy(working_params))
        return case_summary


    def _get_hindcast_file_info(self, run_builder ):
        # created a dict which can be used to build a reader

        ml = msg_logger
        working_params = run_builder['working_params']
        reader_params =  working_params['core_roles']['reader']
        crumbs = 'Getting hydro-model file info.'
        class_importer = class_importer_util.ClassImporter(shared_info, msg_logger, crumbs=crumbs +'> build class_importer', caller=self)

        t0 = perf_counter()
        if 'input_dir' not in reader_params or 'file_mask' not in reader_params:
            ml.msg('Reader class requires settings, "input_dir" and "file_mask" to read the hindcast',
                                    fatal_error=True, exit_now=True , crumbs=crumbs)
        # check input dir exists

        if path.isdir(reader_params['input_dir']):
            ml.progress_marker(f'Found input dir "{reader_params["input_dir"]}"')
        else:
            ml.msg(f' Could not find input dir "{reader_params["input_dir"]}"',
                   hint ='Check reader parameter "input_dir"', fatal_error=True, exit_now=True)

        reader_params, file_list = get_hydro_model_info.find_file_format_and_file_list(reader_params, class_importer, ml)

        reader = class_importer.new_make_class_instance_from_params('reader', reader_params, default_classID='reader', crumbs= crumbs + '> primary reader import',caller=self)

        ml.exit_if_prior_errors('failed to get  hydo-model file info') # class name missing or missing required variables
        reader_builder =dict(params=reader_params, file_info= reader.get_hindcast_files_info(file_list, ml) )

        ml.progress_marker('sorted hyrdo-model files in time order', start_time=t0)

        # get file info for nested readers
        run_builder['nested_reader_builders']= {}
        if 'nested_readers' not in working_params: working_params['nested_readers'] ={}

        for name, params in working_params['nested_readers'].items():
            t0 = perf_counter()
            nested_params, nested_file_list = get_hydro_model_info.find_file_format_and_file_list(params,class_importer, ml)
            nested_reader = class_importer.new_make_class_instance_from_params( nested_params,'reader', default_classID='reader', crumbs=f'nested reader{name}>')

            d= dict(params=nested_params,
                    file_info= nested_reader.get_hindcast_files_info(nested_file_list, ml)
                    )
            run_builder['nested_reader_builders'][name]=d
            ml.progress_marker(f'sorted nested hyrdo-model files in time order{name}', start_time=t0)

        return reader_builder

    def _write_run_info_json(self, case_summary,run_builder, t0):
        # read first case info for shared info
        ml = msg_logger
        o = run_builder['output_files']
        ci = deepcopy(case_summary) # dont alter input
        if type(ci) is not list: ci= [ci]

        # finally get run totals of steps and particles across al cases and write
        n_time_steps = 0.
        total_alive_particles = 0
        case_info_list=[]
        # load log files to get info on run from solver info
        for n, c  in enumerate(ci) :
            n_time_steps += c['run_info']['current_model_time_step']
            total_alive_particles += c['run_info']['total_alive_particles']
            if c['case_info_file'] is not None :
                case_info_list.append(path.join(path.basename(c['case_info_file'])))
            else:
                case_info_list.append(None)
                ml.msg(f'Case #{n:d} has no case info file, likely has crashed',warning=True)

        num_cases = len(ci)

        # JSON parallel run info data
        d = {'output_files' :{},
            'version_info': definitions.version,
            'computer_info': get_versions_computer_info.get_computer_info(),
            'num_cases': num_cases,
            'elapsed_time' :perf_counter() - t0,
            'average_active_particles': total_alive_particles / num_cases if num_cases > 0 else None,
            'average_number_of_time_steps': n_time_steps/num_cases  if num_cases > 0 else None,
            'particles_processed_per_second': total_alive_particles /(perf_counter() - t0),
             'case_summary' : case_summary
             }

        # get output file names

        d['output_files'] = {'root_output_dir':  o['root_output_dir'],
                            'run_output_dir': o['run_output_dir'],
                            'output_file_base': o['output_file_base'],
                            'runInfo_file': o['runInfo_file'],
                            'runLog_file': o['runLog_file'],
                            'run_error_file': o['run_error_file'],
                            'users_params_json': o['raw_user_params'],
                             'caseInfo_files':case_info_list
                             }
        json_util.write_JSON(path.join(o['run_output_dir'],o['runInfo_file']),  d)


        case_files= [path.join(run_builder['output_files']['run_output_dir'],f) for f in case_info_list]
        return case_files if len(case_files) > 1 else case_files[0]

    def close(self):

        msg_logger.close()

