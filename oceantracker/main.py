# method to run ocean tracker from parameters
# eg run(params)
import sys

code_version = '0.4.00.000 2023-03-29'

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
from oceantracker.util import basic_util
from oceantracker.util import json_util

from oceantracker.util.parameter_checking import merge_params_with_defaults, check_top_level_param_keys_and_structure
from oceantracker.oceantracker_case_runner import OceanTrackerCaseRunner
from oceantracker.common_info_default_param_dict_templates import  default_case_param_template, run_params_defaults_template, default_class_names, package_fancy_name
from oceantracker.util.parameter_base_class import make_class_instance_from_params
from oceantracker.util.messgage_logger import GracefulError, MessageLogger

import subprocess
import traceback


def run(user_params):
    OT = _RunOceanTrackerClass()
    full_runInfoJSON_file_name, has_errors = OT.run(user_params)
    return  full_runInfoJSON_file_name, has_errors

class _RunOceanTrackerClass(object):

    def run(self,params):

        # prelim set up to get output dir, to make message logger


        try:
            print('--' + package_fancy_name + ' preliminary set up')
            run_builder= self.setup_output_folders_and_run_builder(params)

        except GracefulError as e:
            # errors thrown by msg_logger
            raise(Exception('preliminary setup had fatal errors, see hints above'))

        except Exception as e:
            # unexpected errors
            print(str(e))
            traceback.print_exc()
            raise(Exception('Unexpected error  in  preliminary set up'))

        # make message/error logger for main code  with log and error output files
        self.msg_logger = MessageLogger('M:')
        msg_logger = self.msg_logger
        run_builder['output_files']['runLog_file'], run_builder['output_files']['run_error_file'] = \
            msg_logger.set_up_files(run_builder['output_files']['run_output_dir'], run_builder['output_files']['output_file_base'])


        # complete the setup with message logger
        try:
            run_builder, reader, case_builders_list = self.set_up(run_builder,msg_logger)

        except GracefulError as e:
            msg_logger.show_all_warnings_and_errors()
            msg_logger.write_error_log_file(e)
            msg_logger.msg(f' Graceful exit from main code', hint=' has parameters/setup has errors, see above', fatal_error=True)
            return  None, True
        except Exception as e:
            # unexpected errors
            msg_logger.write_error_log_file(e)
            msg_logger.show_all_warnings_and_errors(e)
            msg_logger.msg('unexpected error', hint='see trace back above, or .err file', fatal_error=True)
            return None, True


        # now run cases
        full_runInfoJSON_file_name, has_errors = self._run(run_builder, case_builders_list,reader)

        return full_runInfoJSON_file_name, has_errors

    def setup_output_folders_and_run_builder(self, params):
        #setus up params, opens log files/ error handling, required befor mesage loger can be used

        if type(params) is not dict:
            raise GracefulError('Parameter must be a dictionary or json/yaml file readable as a dictionary, given parameters are type=' + str(type(params)),
                                hint='check parameter file or parameter variable is in dictionary form')

        run_builder={'params_from_user': deepcopy(params),
                    'working_params': deepcopy(params),
                    'output_files': {}}


        working_params = run_builder['working_params']
        # basic share params checks, not logged to file
        if 'shared_params' not in working_params:
           raise GracefulError('Cannot find required top level parameter "shared_prams "',
                               hint = 'check parameter file or dictionary for  "shared_prams" key')

        shared_params = working_params['shared_params']

        # partial merger of share params to set up output dir for logging  class etc
        if 'root_output_dir' not in shared_params:
            shared_params['root_output_dir']='default_root_output_dir'

        if type(shared_params['root_output_dir']) is not str:
            raise GracefulError('Shared_params params root_output_dir must be a stringhas type=' + str(type(params['shared_params']['output_file_base'])),
                                hint='check parameter root_output_dir values type')

        # file base
        if 'output_file_base' not in shared_params:
            shared_params['output_file_base'] = 'default_output_file_base'

        if type(shared_params['output_file_base']) is not str:
            raise GracefulError('Shared_params params output_file_base must be a string, has type=' + str(type(shared_params['output_file_base'])),
                                hint='check parameter output_file_base values type')

        # get output files location
        root_output_dir = path.abspath(path.normpath(shared_params['root_output_dir']))
        run_output_dir = path.join(root_output_dir, shared_params['output_file_base'])

        if 'add_date_to_run_output_dir' not in shared_params:
            shared_params['add_date_to_run_output_dir'] = False

        # add date to run if requested
        if type(shared_params['add_date_to_run_output_dir']) is not bool:
            raise GracefulError('Shared_params params output_file_base must be a boolean, has type=' + str(type(shared_params['output_file_base'])),
                                hint='check parameter add_date_to_run_output_dir values type')

        if shared_params['add_date_to_run_output_dir']:
            run_output_dir += datetime.now().strftime("_%Y-%m-%d_%H-%M")
        else:
            shared_params['add_date_to_run_output_dir'] = False

        # kill existing folder
        if path.isdir(run_output_dir):  shutil.rmtree(run_output_dir)

        try:
            makedirs(run_output_dir)  # make  and clear out dir for output
        except OSError as e:
            # path may already exist, but if not through other error, exit
            raise IOError('Failed to make run output dir:' + run_output_dir + ', exiting')

        run_builder['output_files'] = {'root_output_dir': root_output_dir,
                        'run_output_dir' :  run_output_dir,
                        'output_file_base': shared_params['output_file_base'],
                        'runInfo_file'  : shared_params['output_file_base'] + '_runInfo.json',
                        'runLog_file':  shared_params['output_file_base']+ '_runScreen.log',
                        'run_error_file':  shared_params['output_file_base']+ '_run.err'}

        return run_builder

    #@profile
    def set_up(self,run_builder,ml):
        # merge al param with defaults and make full case_builders

        run_builder= self.setup_check_python_version(run_builder,ml)
        working_params = run_builder['working_params']

        # check top level params and ad empty list and dict
        working_params = self.setup_check_toplevel_param_structure(working_params, ml)

        # fully merged shared params with drfaults
        working_params['shared_params'] = merge_params_with_defaults(working_params['shared_params'], run_params_defaults_template['shared_params'], {},
                                                                     ml, crumbs='merging shared_params with defaults')
        ml.insert_screen_line()
        ml.exit_if_prior_errors('errors merging share params with defaults')

        ml.set_max_warnings(working_params['shared_params']['max_warnings'])

        ml.insert_screen_line()
        ml.write_progress_marker('Running ' + package_fancy_name + ' started ' + str(datetime.now()))
        ml.write_progress_marker('Starting: ' + working_params['shared_params']['output_file_base'])

        # get info to build a reader, and create a dummy reader instance
        run_builder['reader_build_info'], reader = self._setup_reader_builder(run_builder, ml)
        ml.write_progress_marker('Input directory: ' + reader.params['input_dir'])

        # make full list of cases to run with fully merged params
        case_builders  = self.setup_build_full_case_params(run_builder,ml)


        return run_builder, reader, case_builders

    def setup_check_python_version(self,run_builder,msg_logger):
        # set up log files for run

        msg_logger.insert_screen_line()
        msg_logger.msg('Starting ' + package_fancy_name + '  Version ' + code_version)
        msg_logger.msg('Python version: ' + version, tabs=1)

        vi = version_info
        install_hint = 'Install Python 3.10 or used environment.yml to build a Conda virtual environment named oceantracker'

        # todo check share mem version
        if False and run_builder['working_params']['shared_params']['shared_reader_memory']:
            # for shared reader python version must be >=3.8
            if not (vi.major == 3 and vi.major >= 8):
                msg_logger.msg('To use shared reader memory ' +
                             package_fancy_name + ' requires Python 3 , version >= 3.8, disabling "share_reader_memory" parameter',
                             hint=install_hint, warning=True, tabs=1)
                run_builder['working_params']['shared_params']['shared_reader_memory'] = False

        if (vi.major == 3 and vi.major >= 11):
            msg_logger.msg(package_fancy_name + ' is not yet compatible with Python 3.11, as not al imported packages have been updated, eg Numba ',
                         hint=install_hint, fatal_error=FatalError, tabs=1)
        if vi.major < 3:
            msg_logger.msg(package_fancy_name + ' requires Python version 3 ', hint=install_hint,  exception = True, tabs = 1)

        msg_logger.exit_if_prior_errors()

        return run_builder

    def setup_check_toplevel_param_structure(self, working_params,msg_logger):
        # check basic structure of params  has the required keys etc
        #---------------------------------------------------------
        # overall structure
        working_params = check_top_level_param_keys_and_structure(working_params, run_params_defaults_template, msg_logger,
                                                                    required_keys=['shared_params', 'reader'],crumbs='top level parameter check',
                                                                    required_alternatives=[['base_case_params', 'case_list']])
        # base case structure
        working_params['base_case_params'] = check_top_level_param_keys_and_structure(working_params['base_case_params'], default_case_param_template,
                                                           msg_logger,  crumbs='base_case_params top level parameter check')


        if len(working_params['case_list']) == 0: working_params['case_list'] = [{}]  # add a dummy case if None given

        # check given cases
        for n, c in enumerate(working_params['case_list']):
            c  = check_top_level_param_keys_and_structure(c, default_case_param_template, msg_logger=msg_logger,
                                                          crumbs='case level parameters check, case_list parameters, case[#' + str(n) + ']  ')
            if len(c['particle_release_groups']) == 0 and len(working_params['base_case_params']['particle_release_groups']) == 0:
                msg_logger.msg('Neither base_case_params nor case_list  have "particle_release_groups"  for case =' + str(n + 1), fatal_error=True)

        msg_logger.exit_if_prior_errors()

        return working_params


    def _run(self,run_builder, case_builders_list, reader):

        d0 = datetime.now()
        t0 = perf_counter()
        run_info = {'user_note': {}, 'screen_log': [],
                    'run_started': str(d0),
                    'run_ended': None,
                    'elasped_time': None,
                    'performance': {},
                    'output_files': {},
                    }


        output_files= run_builder['output_files']
        working_params = run_builder['working_params']

        ml = self.msg_logger

        ml.insert_screen_line()

        # run the cases, return list of case info json files which make up the run of all cases
        #----------------------------------------------------------------------------------------------
        output_files['case_info'], case_error = self._run_case_list(case_builders_list, reader)
        # ----------------------------------------------------------------------------------------------

        # tidy up run
        tnow= datetime.now()
        run_info.update({
            'user_note': working_params['shared_params']['user_note'],
            'run_ended':tnow ,
            'elasped_time': str(tnow-d0),
            'code_version_info': self._U2_code_version_info(),
            'computer': basic_util.get_computer_info(),
            'user_supplied_params':run_builder['params_from_user'],  # add params
            'performance' : self._U1_get_all_cases_performance_info(output_files['case_info'], case_error, working_params['shared_params'],
                                                                    output_files['run_output_dir'], t0),
            'output_files': output_files
                })
        # write runInfo JSON
        full_runInfoJSON_file_name = path.join(output_files['run_output_dir'], output_files['runInfo_file'])
        json_util.write_JSON(full_runInfoJSON_file_name, run_info)

        # the end
        ml.show_all_warnings_and_errors()
        ml.insert_screen_line()
        ml.write_progress_marker('Finished ' + '---  started: ' + str(t0) + '---  ended: ' + str(datetime.now()))
        ml.msg('Elapsed time =' + str(datetime.now() - d0), tabs=3)
        ml.msg('Output in ' + output_files['run_output_dir'], tabs=4)
        ml.insert_screen_line()
        ml.close()

        has_errors= any(case_error)
        return full_runInfoJSON_file_name, has_errors

    def setup_build_full_case_params(self, run_builder, msg_logger):
        # make set of case params merged with defaults and checked

        working_params= run_builder['working_params']
        base_case_params = working_params['base_case_params']
        # build full shared params
        base_case_params = check_top_level_param_keys_and_structure(base_case_params, default_case_param_template,msg_logger,
                                                                              required_keys=[], crumbs='Checking base case  params')

        # build each case params
        processor_number = 0
        case_list = working_params['case_list'] # will have a dummy one anned in strcture checks if empty
        runner_params=[]
        shared_params= working_params['shared_params']

        for n_case, case in enumerate(case_list):
            # add replicate copies if required
            for n_replicate in range(shared_params['replicates']):
                # parameter list to run same particle on multiple threads
                c  = deepcopy(case)  # a set of parameters for this case
                c  = check_top_level_param_keys_and_structure(c, default_case_param_template,msg_logger,
                                                                       required_keys=[], crumbs ='Checking case params')

                cout = {'run_params': {}, 'core_classes': {}, 'class_lists': {}}

                for key, item in c.items():
                    if item is None: continue
                    if key =='run_params':
                        cout['run_params'] = merge_params_with_defaults(c['run_params'],default_case_param_template['run_params'],
                                                                                   base_case_params['run_params'],msg_logger,
                                                                                   crumbs='case_run_params')
                        pass
                    elif type(item) == dict and key != 'reader':
                        # core classes
                        i = make_class_instance_from_params(item,msg_logger, class_type_name=key,crumbs ='class param ' + key +' >> ',
                                                                      base_case_params= base_case_params[key])
                        if i is not None:
                            cout['core_classes'][key]= i.params
                    elif type(item) == list:
                        if key not in cout['class_lists']: cout['class_lists'][key] =[]
                        for n, cli in enumerate( item + base_case_params[key]):
                            i = make_class_instance_from_params(cli,msg_logger,class_type_name=key,
                                                                    nseq=n,crumbs ='class list param ' + key +' >> ')

                            if i is not None:
                                cout['class_lists'][key].append(i.params)

                    else: pass # top level checks ensures items are dict or lists


                case_output_files= deepcopy(run_builder['output_files']) # need to make a copy
                case_output_files['output_file_base']  = copy(shared_params['output_file_base'])

                # form case output file base name
                if len(case_list) > 1 : case_output_files['output_file_base'] += '_C%03.0f' % (n_case+1)
                if shared_params['replicates'] > 1:  case_output_files['output_file_base'] +=  'R%02.0f' % (n_replicate+1)
                if cout['run_params']['case_output_file_tag'] is not None : case_output_files['output_file_base'] += '_' + cout['run_params']['case_output_file_tag']

                # now build full params  for a single run
                processor_number += 1  # is one base
                runner_params.append({ 'processor_number' : processor_number,
                                    'code_version_info' : self._U2_code_version_info(),
                                    'shared_params': shared_params,
                                    'reader_build_info' : run_builder['reader_build_info'],
                                    'case_params' : cout, # single case_params  merged with base_case_params
                                    'output_files' : case_output_files,
                                    #'package_info':package_info,
                                    })  # add case/ copy to list for the pool



        msg_logger.exit_if_prior_errors('Errors in merging case parameters')
        return runner_params


    def _setup_reader_builder(self,run_builder , msg_logger):
        # created a dict which can be used to build a reader
        working_params = run_builder['working_params']
        if 'class_name' not in working_params['reader']:
            msg_logger('Reader param must have class_name parameter', fatal_error=True, exit_now=True)

        if not path.isdir(working_params['reader']['input_dir']):
            msg_logger('Cannot find  input_dir (hindcast) directory = ' + working_params['reader']['input_dir'], fatal_error=True, exit_now=True)

        working_params['reader']['input_dir'] = path.abspath(path.normpath((working_params['reader']['input_dir'])))

        reader = make_class_instance_from_params(working_params['reader'],msg_logger, class_type_name='reader')  # temporary  reader to get defaults
        reader.shared_info.shared_params = working_params['shared_params'] # reader needs access to share parms for set up

        # construct reader_build_info to be used by case_runners to build their reader
        reader_build_info= {'shared_reader_memory': working_params['shared_params']['shared_reader_memory'],
                            'backtracking' : working_params['shared_params']['backtracking'],
                            'reader_params': reader.params}
        reader_build_info['file_info'] = reader.get_hindcast_files_info() # get file lists

        msg_logger.write_progress_marker('Finished sorting hyrdo model  files ', tabs=3)

        # read and set up reader grid now as  required for writing grid file
        # also if requested shared grid memory is set up
        # and shared memory info will be also added to reader_build_info for case runner to build reader
        grid = reader.grid
        grid_time_buffers = reader.grid_time_buffers
        nc = reader._open_grid_file(reader_build_info)

        grid = reader.make_non_time_varying_grid(nc, grid)
        grid_time_buffers = reader.make_grid_time_buffers(nc,grid,grid_time_buffers)

        # add information to build grid and grid_time_buffers to reader_build_info
        reader_build_info = reader.make_grid_builder(grid, grid_time_buffers, reader_build_info)

        # get information required to build reader fields
        reader_build_info= reader.maker_field_builder(nc, reader_build_info)

        # special case read water depth field, so it can be wrtten to grid file
        #add_a_reader_field(self, nc, name, field_variable_comps)

        nc.close()

        if reader_build_info['shared_reader_memory']:

            reader_build_info = reader.set_up_shared_grid_memory(reader_build_info)

            # add to class to shared info, alows fileds to be built
            si = reader.shared_info
            si.classes['reader'] = reader

            # set up reader fields
            reader.setup_reader_fields(reader_build_info)
            sm_fields = {}
            for name, sm in reader.shared_memory['fields'].items():
                sm_fields[name] = sm.get_shared_mem_map()

        # write grid and save file names
        output_files = run_builder['output_files']
        if working_params['shared_params']['write_output_files']:
            output_files['grid'], output_files['grid_outline'] = self._write_run_grid_netCDF(output_files, reader_build_info, reader)


        return  reader_build_info, reader



    def _write_run_grid_netCDF(self, output_files, reader_build_info, reader):
        # write a netcdf of the grid from first hindcast file
   
        grid= reader.grid

        # get depth from first hincast file
        hindcast = NetCDFhandler(reader_build_info['file_info']['names'][0], 'r')
        depth_var = reader.params['field_variables']['water_depth']
        if depth_var is not None and hindcast.is_var(depth_var):
            # world around to ensure depth read in right format
            field_params,var_info = reader.get_field_variable_info(hindcast,'water_depth',reader.params['field_variables']['water_depth'])
            water_depth = reader.read_file_field_variable_as4D(hindcast,var_info['component_list'][0],var_info['is_time_varying'], file_index=None)
            water_depth = reader.preprocess_field_variable(hindcast,'water_depth',water_depth)
            water_depth= water_depth[0, :, 0, 0] # guard against  water depth being time dependent, so only write first time step of the 4D depth field
            grid['water_depth'] = np.squeeze(water_depth)

        hindcast.close()

        # write grid file
        grid_file = output_files['output_file_base'] + '_grid.nc'
        nc = NetCDFhandler(path.join(output_files['run_output_dir'], grid_file), 'w')
        nc.write_global_attribute('Notes', ' all indices are zero based')
        nc.write_global_attribute('created', str(datetime.now().isoformat()))

        nc.write_a_new_variable('x', grid['x'], ('node_dim', 'vector2D'))
        nc.write_a_new_variable('triangles', grid['triangles'], ('triangle_dim', 'vertex'))
        nc.write_a_new_variable('triangle_area', grid['triangle_area'], ('triangle_dim',))
        nc.write_a_new_variable('adjacency', grid['adjacency'], ('triangle_dim', 'vertex'))
        nc.write_a_new_variable('node_type', grid['node_type'], ('node_dim',), attributesDict={'node_types': ' 0 = interior, 1 = island, 2=domain, 3=open boundary'})
        nc.write_a_new_variable('is_boundary_triangle', grid['is_boundary_triangle'].astype(np.int8), ('triangle_dim',))
        nc.write_a_new_variable('water_depth', grid['water_depth'], ('node_dim',))
        nc.close()

        grid_outline_file = output_files['output_file_base'] + '_grid_outline.json'
        json_util.write_JSON(path.join(output_files['run_output_dir'], grid_outline_file), grid['grid_outline'])

        return grid_file, grid_outline_file

    def _run_case_list(self, case_param_list, reader):
        # do run of all cases
        ml = self.msg_logger
        shared_params = case_param_list[0]['shared_params']
        case_results = []

        if shared_params['shared_reader_memory']:
            case_results = self.run_with_shared_reader(case_param_list, reader)

        elif shared_params['processors'] == 1:
            # serial or non-parallel mode,   run a single case non parallel to makes debuging easier and allows reruns of single case
            case_results = self.run_serial(case_param_list)
        else:
            # run parallel
            case_results = self.run_parallel(case_param_list)

        # unpack case output
        case_info_file_list, case_errors_list = [],[]
        n=0
        for case_file,case_error  in case_results:
            case_info_file_list.append(case_file)
            case_errors_list.append(case_error)
            if case_file is None and case_error is not None:
                ml.msg('CaseInfo files missing  for case ' + str(n)
                                   + ', or other error, case may have not completed, check for .err file!!!!!!, error type= ' + case_error.__class__.__name__, warning=True)
            n += 1

        return case_info_file_list,  case_errors_list

    def run_serial(self,case_param_list):
        # serial or non-parallel mode,   run a single case non parallel to makes debuging easier and allows reruns of single case
        case_results = []
        for c in case_param_list:
            a = self._run1_case(c)
            case_results.append(a)
        return case_results

    def run_parallel(self,case_param_list):
        ml = self.msg_logger
        msg_list = []
        shared_params = case_param_list[0]['shared_params']
        shared_params['processors'] = min(shared_params['processors'], len(case_param_list))
        ml.write_progress_marker('oceantracker:multiProcessing: processors:' + str(shared_params['processors']))

        with multiprocessing.Pool(processes=shared_params['processors']) as pool:
            case_results = pool.map(self._run1_case, case_param_list)

        ml.write_progress_marker('parallel pool complete')

        return case_results

    def run_with_shared_reader(self, case_param_list, reader):
        # complete reader build then run cases asynchronously with shared reader

        # shared grid is already to allow grid to be written  and case

        # shared reader control arrays
        time_steps_in_buffer = shared_memory.SharedMemArray(shape=(2,0),dtype=np.int2)
        c = {'time_steps_in_buffer':time_steps_in_buffer.get_shared_mem_map() }

        # add field shared memory build info to each case
        for case in case_param_list:
            case['reader_build_info']['shared_memory']['fields'] = sm_fields
            case['reader_build_info']['shared_memory']['control'] = c
        #todo make shared fields and grid arrays read only in children sm.data.setflags(write=False)
        pass

    @staticmethod
    def _run1_case(run_params):
        # run one process on a particle based on given family class parameters
        # by creating an independent instances of  model classes, with given parameters
        ot = OceanTrackerCaseRunner()
        caseInfo_file, case_error = ot.run(deepcopy(run_params))
        return caseInfo_file, case_error

    def _U1_get_all_cases_performance_info(self, case_info_files, case_error_list, sparams, run_output_dir, t0):
        # finally get run totals of steps and particles

        n_time_steps = 0.
        total_alive_particles = 0
        # load log files to get info on run from solver info
        for n, case_file, case_error in zip(range(len(case_info_files)), case_info_files,case_error_list) :
            if case_file is not None :
                c= json_util.read_JSON(path.join(run_output_dir, case_file))
                sinfo = c['class_info']['solver']
                n_time_steps += sinfo['time_steps_completed']
                total_alive_particles += sinfo['total_alive_particles']

        num_cases = len(case_info_files)

        # JSON parallel run info data
        d = {'processors': sparams['processors'],
             'num_cases': num_cases,
             'replicates': sparams['replicates'],
                'elapsed_time' :perf_counter() - t0,
            'average_active_particles': total_alive_particles / num_cases if num_cases > 0 else None,
             'average_number_of_time_steps': n_time_steps/num_cases  if num_cases > 0 else None,
             'particles_processed_per_second': total_alive_particles /(perf_counter() - t0)
             }

        # put parallel info in first file base
        return d

    def _U2_code_version_info(self):
        try:
            git_revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path.dirname(path.realpath(__file__))).decode().replace('\n','')
        except:
            git_revision = 'unknown'
        return { 'version': code_version, 'git_revision': git_revision, 'python_version':version}