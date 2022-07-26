# method to run ocean tracker from parmeters
# eg run(params)


# todo kernal/numba based RK4 step
# todo short name map requires unique class names in package, this is checked on startup,add checks of uniqueness of user classes added from outside package
# Dev notes
# line debug?? python3.6 -m pyinstrument --show-all plasticsTrackOnLine_Main.py
# python -m cProfile
# python -m vmprof  <program.py> <program parameters>
# python -m cProfile -s cumtime
import time
from copy import deepcopy
from datetime import datetime
import multiprocessing
from os import path, makedirs
import traceback
import shutil
from time import perf_counter
from copy import  copy
import numpy as np

from oceantracker.util.package_util import check_package
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util import basic_util
from oceantracker.util import json_util
from oceantracker.util.message_and_error_logging import MessageLogging, append_message, GracefulExitError,FatalError
from oceantracker.util import time_util
from oceantracker.util.parameter_checking import merge_params_with_defaults, check_top_level_param_keys_and_structure
from oceantracker.oceantracker_case_runner import OceanTrackerCaseRunner
from oceantracker.common_info_default_param_dict_templates import  default_case_param_template, run_params_defaults_template, default_class_names, package_fancy_name
from oceantracker.util.module_importing_util import import_module_from_string

import subprocess

code_version = '0.3.0022'

run_info = {'user_note': {}, 'screen_log': [],
            'run_started': datetime.now(),
            'run_ended': None,
            'elasped_time': None,
            'performance': {},
            'output_files': {},
            }

def run(user_params):
    OT= _RunOceanTrackerClass()
    full_runInfoJSON_file_name, has_errors = OT._run(deepcopy(user_params))
    return  full_runInfoJSON_file_name, has_errors

class _RunOceanTrackerClass(object):
    def __init__(self):
        self.run_log = MessageLogging('M:')

    def _run(self, user_params):

        # make sure output dir is there, so to at least write errors
        try:
            output_files = self._A1_set_up_folders_and_file_names(user_params)
        except ValueError as e:
            print(traceback.format_exc())
            print(package_fancy_name + ' shared parameter start up error : Errors in building output folder - ' + str(e))
            return None, True
        except IOError as e:
            print(traceback.format_exc())
            print(package_fancy_name + ' shared parameter start up error : Failed to make output dir or other IO error - ' + str(e))
            return None, True

        except Exception as e:
            print(traceback.format_exc())
            raise Exception(package_fancy_name + ' shared parameter start up error : Unnown error making output dir from shared params - ' + str(e))
            return None, True

        # open log file
        rl = self.run_log
        rl.set_up_log_file(output_files['run_output_dir'], output_files['output_file_base'], 'runLog')
        self.package_info, msg_list = check_package(__file__)
        rl.add_messages(msg_list, raiseerrors=True)

        try:
            full_runInfoJSON_file_name, has_errors = self._A2_do_run(user_params, output_files)

        except GracefulExitError as e:
            rl.write_msg(' Graceful exit >>  Parameters/setup has errors, see above', exception = GracefulExitError)
            return None, True

        except FatalError as e:
            rl.write_error_log_file(e)
            return None, True

        except Exception as e:
            # other error
            msg ='Unknown error, see .err file'
            rl.write_msg(msg)
            rl.write_msg(str(e))
            rl.write_error_log_file(e)
            raise  Exception(msg)

        return full_runInfoJSON_file_name, has_errors

    def _A1_set_up_folders_and_file_names(self, user_params):
        if type(user_params) is not dict:
            raise ValueError('Params must be a dictionary, exiting,  got type=' + str(type(user_params)))

        if 'shared_params' not in user_params:
            raise ValueError('Cannot find key "shared_params" in parameters, exiting' )

        if 'root_output_dir' not in user_params['shared_params']:
            raise ValueError('Cannot find key "root_output_dir" in parameters, at least required for error logging,  exiting' )

        if 'output_file_base' not in user_params['shared_params']:
            raise ValueError('Cannot find key "output_file_base" in parameters,  exiting')

        shared_params = user_params['shared_params']
        root_output_dir = path.abspath(path.normpath(shared_params['root_output_dir']))
        run_output_dir = path.join(root_output_dir, shared_params['output_file_base'])

        if 'add_date_to_run_output_dir' in shared_params and shared_params['add_date_to_run_output_dir']:
            run_output_dir += datetime.now().strftime("_%Y-%m-%d")
        else:
            shared_params['add_date_to_run_output_dir'] = False

        if path.isdir(run_output_dir):  shutil.rmtree(run_output_dir)
        try:
            makedirs(run_output_dir)# make  and clear out dir for output
        except OSError as e:
            # path may already exist, but if not through other error, exit
                raise IOError('Failed to make run output dir:' + run_output_dir + ', exiting')


        # log file output control
        output_files = {'root_output_dir': root_output_dir,
                        'run_output_dir' :  run_output_dir,
                        'output_file_base': shared_params['output_file_base'],
                        'runInfo_file'  : shared_params['output_file_base'] + '_runInfo.json',
                        'runLog_file':  shared_params['output_file_base']+ '_runScreen.log'
                        }

        return output_files

    def _A2_do_run(self, params, output_files):
        run_info[ 'screen_log'] = []
        rl= self.run_log
        t0 = time.perf_counter()

        rl.insert_screen_line()
        rl.write_msg('Starting ' + package_fancy_name+ '  Version ' + code_version )

        # clean up params
        working_params = deepcopy(params)

        working_params = self._B1_check_param_structure(working_params)

        # get defaults for shared params, to set up output locations etc, todo moved to dev above
        working_params['shared_params'], msg_list = merge_params_with_defaults(params['shared_params'], run_params_defaults_template['shared_params'], {}, msg_list=[], tag='shared_params')

        rl.set_max_warnings(working_params['shared_params']['max_warnings'])
        rl.insert_screen_line()
        rl.write_progress_marker('Running '+ package_fancy_name + ' started ' + str(datetime.now()))
        rl.write_progress_marker('Starting: ' + working_params['shared_params']['output_file_base'])
        rl.insert_screen_line()

        # get info to build a reader
        reader =self._C1_build_reader(params)
        reader_build_info = self._C2_get_hindcast_files_info(working_params['shared_params'],reader)

        # write grid and outline and record file names
        if working_params['shared_params']['write_output_files']:
            output_files['grid'], output_files['grid_outline'] = self._U3_write_run_grid_netCDF(output_files, reader_build_info, reader)

        runner_params_test, shared_params, msg_list = self._E1_get_full_case_params(working_params, output_files, reader_build_info)
        # self.run_log.write_messages(msg_list)
        # run the cases, return list of case info json files which make up the run of all cases
        #----------------------------------------------------------------------------------------------
        #output_files['case_info'], case_error = self._F1_run_case_list(runner_params_case_list)
        output_files['case_info'], case_error = self._F1_run_case_list(runner_params_test)
        # ----------------------------------------------------------------------------------------------

        # tidy up run
        run_info.update({
            'user_note': working_params['shared_params']['user_note'],
            'run_ended': datetime.now(),
            'elasped_time': time_util.duration_str_from_dates(run_info['run_started'], datetime.now()),
            'code_version_info': self._U2_code_version_info(),
            'computer': basic_util.get_computer_info(),
            'user_params': params,  # add params
            'performance' : self._U1_get_all_cases_performance_info(output_files['case_info'], case_error, working_params['shared_params'],
                                                                    output_files['run_output_dir'], t0),
            'output_files': output_files
                })
        # write runInfo JSON
        full_runInfoJSON_file_name = path.join(output_files['run_output_dir'], output_files['runInfo_file'])
        json_util.write_JSON(full_runInfoJSON_file_name, run_info)

        # the end
        rl.show_all_warnings_and_errors()
        rl.insert_screen_line()
        rl.write_progress_marker('Finished ' + package_fancy_name + ' at ' + time_util.iso8601_str(datetime.now()))
        rl.write_progress_marker('Output in ' + output_files['run_output_dir'])
        rl.write_progress_marker('Run time  =  ' + str(run_info['elasped_time']))
        rl.insert_screen_line()
        rl.close()

        has_errors= any(v is not None for v in case_error)
        return full_runInfoJSON_file_name, has_errors

    def _B1_check_param_structure(self, params):
        rl= self.run_log
        msg_list=[]
        params, msg_list = check_top_level_param_keys_and_structure(params, run_params_defaults_template,msg_list=msg_list,
                                                                  required_keys=['shared_params', 'reader'],
                                                                  required_alternatives=[['base_case_params', 'case_list']],
                                                                  tag='Top level parameter check')
        params['base_case_params'] , msg_list = check_top_level_param_keys_and_structure(params['base_case_params'], default_case_param_template, msg_list=msg_list,
                                                                  tag='base_case_params top level parameter check')

        rl.add_messages(msg_list)

        if len(params['case_list'])==0: params['case_list'] = [{}]     # add a dummy case

        # check given cases
        msg_list = []
        for n, c in enumerate(params['case_list']):
            c, msg_list = check_top_level_param_keys_and_structure(c, default_case_param_template, msg_list=msg_list,
                                                                   tag='case_list, case[#' + str(n) + ']  top level parameter check')
            if len(c['particle_release_groups']) == 0  and len(params['base_case_params']['particle_release_groups']) == 0:
                rl.write_msg('Neither base_case_params nor case_list  have "particle_release_groups"  for case =' + str(n+1), exception = GracefulExitError)

        rl.add_messages(msg_list)
        rl.check_messages_for_errors()
        return params

    def _E1_get_full_case_params(self, params, output_files, reader_build_info):
        # make set of case params merged with defaults and checked
        msg_list =[]
        # build full shared params
        shared_params, msg_list = merge_params_with_defaults(params['shared_params'], run_params_defaults_template['shared_params'], {},msg_list=msg_list, tag='shared_params')
        base_case_params = deepcopy(params['base_case_params'])

        # build each case params
        processor_number = 0
        case_list = params['case_list'] # will have a dummy one anned in strcture checks if empty
        runner_params=[]

        for n_case, case in enumerate(case_list):
            # add replicate copies if required
            for n_replicate in range(shared_params['replicates']):
                # parameter list to run same particle on multiple threads
                c  = deepcopy(case)  # a set of parameters for this case
                cout = {'run_params': {}, 'core_classes': {}, 'class_lists': {}}

                for key, item in c.items():
                    if item is None: continue
                    if key =='run_params':
                        cout['run_params'], msg_list = merge_params_with_defaults(c['run_params'],default_case_param_template['run_params'],
                                                                                   base_case_params['run_params'],   msg_list=msg_list, tag='case_run_params')
                    elif type(item) == dict and key != 'reader':
                        # core classes
                        # merge templae with base case first
                        base_case_params[key], msg_list = merge_params_with_defaults(base_case_params[key],default_case_param_template[key],{}, check_for_unknown_keys=False,
                                                                                     crumbs='merging core clasess base case with case template', msg_list=msg_list)
                        cout['core_classes'][key], i, msg_list=  self._make_instance_and_merge_params(key, item, base_case_params[key], msg_list=msg_list)

                    elif type(item) == list:
                        if key not in cout['class_lists']: cout['class_lists'][key] =[]
                        for n, cli in enumerate( item + base_case_params[key]):
                            clp, i, msg_list=  self._make_instance_and_merge_params(key, cli, {},
                                                                 msg_list=msg_list, nseq=n,crumbs ='class list param ' + key +' >> ')
                            cout['class_lists'][key].append(clp)

                    else: pass # top level checks ensures items are dict or lists

                case_output_files= deepcopy(output_files) # need to make a copy
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
                                    'reader_build_info' : reader_build_info,
                                    'case_params' : cout, # single case_params  merged with base_case_params
                                    'output_files' : case_output_files,
                                    })  # add case/ copy to list for the pool


        self.run_log.add_messages(msg_list)
        self.run_log.check_messages_for_errors()
        return runner_params, shared_params, msg_list

    def _make_instance_and_merge_params(self, name, class_params, base_class_params, msg_list=[], nseq=None, crumbs=''):
        # dynamically  get instance of class from string eg oceantracker.solver.Solver
        rl = self.run_log
        if 'class_name' not in class_params:  class_params['class_name'] = None

        if class_params['class_name'] is None:
            if 'class_name' in base_class_params and  base_class_params['class_name'] is not None:
                class_params['class_name'] = base_class_params['class_name']
            elif name in default_class_names:
                class_params['class_name'] = default_class_names[name]
            else:
                append_message(msg_list, 'params for ' + crumbs + ' must contain class_name ' + name, exception = GracefulExitError, nseq= nseq)
                return None, None, msg_list
        else:
            # try to convert to long name
            if class_params['class_name'] in self.package_info['short_class_name_map']:
                class_params['class_name'] = self.package_info['short_class_name_map'][class_params['class_name']]

        i, msg = import_module_from_string(class_params['class_name'])
        rl.add_msg(msg, raiseerrors=True)
        if msg is not None:
            msg_list += [msg]
        # use new  merge
        msg_list = i.merge_with_class_defaults(class_params, base_class_params, msg_list=msg_list, crumbs=name if nseq == None else name + '[#' + str(nseq) + ']')

        return i.params, i, msg_list


    def _C1_build_reader(self, params):
        rl= self.run_log
        if 'class_name' not in params['reader']:
            FatalError('Reader must have class_name parameter')

        if not path.isdir(params['reader']['input_dir']):
            raise FatalError('Cannot find  input_dir (hindcast) directory = ' + params['reader']['input_dir'])

        params['reader']['input_dir'] = path.abspath(params['reader']['input_dir'])

        reader, msg = import_module_from_string(params['reader']['class_name'])  # temporary  reader to get defaults
        rl.add_msg(msg, raiseerrors=True)

        msg_list = reader.merge_with_class_defaults(params['reader'], {}, crumbs='reader')
        rl.add_messages(msg_list, raiseerrors=True)

        return  reader

    def _C2_get_hindcast_files_info(self, shared_params, reader):
        # read though files to get start and finish times of each file
        # create a time sorted list of files given by file mask in file_info dictionary
        # sorts based on time from read time,  assumes a global time across all files
        # note this is only called once by OceantrackRunner to form file info list,
        # which is then passed to  OceanTrackerCaseRunner

        # build a dummy non-initialise reader to get some methods and full params
        # add defaults from template, ie get reader class_name default, no warnings, but get these below
        # check cals name
        rl = self.run_log
        reader.initialize()
        file_info =reader.get_list_of_files_and_hindcast_times(reader.params['input_dir'])
        # check some files found
        if len(file_info['names']) == 0:
            rl.write_msg('reader: cannot find any files matching mask "' + reader.params['file_mask']
                           + '"  in input_dir : "' + reader.params['input_dir'] + '"', exception = GracefulExitError)

        msg_list = reader._file_checks(file_info['names'][0], msg_list=[])
        self.run_log.add_messages(msg_list)

        keys = ['names','n_time_steps', 'time_start', 'time_end', 'time_step']
        for key in keys:
            file_info[key] = np.asarray(file_info[key])


        # sort files in time order
        file_order = np.argsort(file_info['time_start'], axis=0)
        for key in keys:
            file_info[key] = file_info[key][file_order]
        file_info['names'] = file_info['names'].tolist()

        file_info['nt_global'] = np.cumsum(file_info['n_time_steps'])
        file_info['nt_global'] = np.column_stack((file_info['nt_global'] - file_info['n_time_steps'], file_info['nt_global'] - 1))
        file_info['n_time_steps_in_hindcast'] = np.sum(file_info['n_time_steps'], axis=0)

        # set up global time, step , file offset and file number for every time step in set of hindcast files
        file_info.update({'nt': [], 'file_number': [], 'file_offset': []})

        for n, n_steps in enumerate(file_info['n_time_steps']):
            file_info['nt'] += list(file_info['nt_global'][n, 0] + np.arange(n_steps))
            file_info['file_number'] += n_steps * [n]
            file_info['file_offset'] += range(n_steps)

        # make above as numpy arrays
        for key in ['nt','file_number','file_offset'] :  file_info[key] = np.asarray(file_info[key])

        # hindcast time step
        dt = (file_info['time_end']-file_info['time_start']) / (file_info['n_time_steps'] - 1)

        #todo these time step checks need to be better
        if abs(np.max(dt) - np.min(dt)) > 1.10 * np.mean(file_info['time_step']):
            rl.write_warning('Range of hindcast time step size in files is more than 1.1 times of mean time step, time step in each file are ' + str(dt))

        file_info['time_step'] = np.mean(dt, axis=0)  # reader time step always positive

        if np.any(np.abs(dt - file_info['time_step'])) > 1200:
            rl.write_warning('Some time steps differ in files by more than 1200 sec')

        reader_build_info = {'reader_params': reader.params} # add full reader params to build from
        reader_build_info['sorted_file_info'] = file_info
        rl.check_messages_for_errors()
        return reader_build_info

    def _U3_write_run_grid_netCDF(self, output_files, reader_build_info, reader):
        # write a netcdf of the grid from first hindcast file
        msg_list=[]
        hindcast = NetCDFhandler(reader_build_info['sorted_file_info']['names'][0], 'r')
        grid = reader._setup_grid(hindcast, reader_build_info)
        hindcast.close()

        # write grid file
        grid_file = output_files['output_file_base'] + '_grid.nc'
        nc = NetCDFhandler(path.join(output_files['run_output_dir'], grid_file), 'w')
        nc.write_global_attribute('Notes', ' all indices are zero based')
        nc.write_global_attribute('created', str(datetime.now().isoformat()))

        nc.write_a_new_variable('x', grid['x'], ('nodes', 'vector2D'))
        nc.write_a_new_variable('triangles', grid['triangles'], ('faces', 'vertex'))
        nc.write_a_new_variable('adjacency', grid['adjacency'], ('faces', 'vertex'))
        nc.write_a_new_variable('node_type', grid['node_type'], ('nodes',), attributesDict={'node_types': ' 0 = interior, 1 = island, 2=domain, 3=open boundary'})
        nc.write_a_new_variable('boundary_triangles', grid['boundary_triangles'].astype(np.int8), ('faces',))

        # add depth to output grid if present, useful for plots
        fieldvar = reader.params['field_variables']
        if 'water_depth' in fieldvar and fieldvar['water_depth'] is not None:
            hindcast = NetCDFhandler(reader_build_info['sorted_file_info']['names'][0], 'r')
            grid['water_depth'] = hindcast.read_a_variable(fieldvar['water_depth'])
            hindcast.close()
            depth = grid['water_depth'] if grid['water_depth'].ndim < 2 else grid['water_depth'][0, :]  # if depth time dependent
            nc.write_a_new_variable('water_depth', depth, ('nodes',))

        nc.close()
        grid_outline_file = output_files['output_file_base'] + '_grid_outline.json'
        json_util.write_JSON(path.join(output_files['run_output_dir'], grid_outline_file), grid['grid_outline'])

        self.run_log.add_messages(msg_list)
        return grid_file, grid_outline_file

    def _F1_run_case_list(self, case_param_list):
        # do run of all cases
        rl= self.run_log
        msg_list=[]
        shared_params = case_param_list[0]['shared_params']
        case_results = []
        if shared_params['processors'] == 1:
            # serial or non-parallel mode,   run a single case non parallel to makes debuging easier and allows reruns of single case
            for c in case_param_list:
                a  = self._run1_case(c)
                case_results.append(a)
        else:
            # run parallel
            shared_params['processors'] = min(shared_params['processors'], len(case_param_list))
            rl.write_progress_marker('oceantracker:multiProcessing: processors:' + str(shared_params['processors']))

            try:
                with multiprocessing.Pool(processes=shared_params['processors']) as pool:
                    case_results = pool.map(self._run1_case, case_param_list)
                append_message(msg_list, 'parallel pool complete')

            except Exception as e:
                append_message(msg_list,'Error setting up parallel run')
                rl.write_error_log_file(e)

        # unpack case output
        case_info_file_list, case_errors_list = [],[]
        n=0
        for case_file,case_error  in case_results:
            case_info_file_list.append(case_file)
            case_errors_list.append(case_error)
            if case_file is None and case_error is not None:
                append_message(msg_list, 'CaseInfo files missing  for case ' + str(n)
                                   + ', or other error, case may have not completed, check for .err file!!!!!!, error type= ' + case_error.__class__.__name__, warning=True)
            n+=1

        rl.add_messages(msg_list)
        return case_info_file_list,  case_errors_list

    @staticmethod
    def _run1_case(run_params):
        # run one process on a particle based on given family class parameters
        # by creating an independent instances of  model classes, with given parameters
        ot = OceanTrackerCaseRunner()
        caseInfo_file, case_error = ot.run(deepcopy(run_params))
        return caseInfo_file, case_error

    def _U1_get_all_cases_performance_info(self, case_info_files, case_error_list, sparams, run_output_dir, t0):
        # finally get run totals of steps and particles

        n_part_steps = 0.
        nPart = 0
        # load log files to get info on run from solver info
        for n, case_file, case_error in zip(range(len(case_info_files)), case_info_files,case_error_list) :
            if case_file is not None :
                c= json_util.read_JSON(path.join(run_output_dir, case_file))
                sinfo = c['info']['solver']
                nPart += sinfo['total_num_particles_moving']/sinfo['n_time_steps_completed']
                n_part_steps += sinfo['n_time_steps_completed'] * sinfo['total_num_particles_moving'] /float(sinfo['n_time_steps_completed'])  # number of steps times number of particles

        n_part_steps = max(1, n_part_steps)
        num_cases = len(case_info_files)

        # JSON parallel run info data
        d = {'processors': sparams['processors'],
             'num_cases': num_cases,
             'replicates': sparams['replicates'],
             'average_active_particles': nPart / num_cases,
             'nSecPerTimeStep': 1.E9 * (perf_counter() - t0) / n_part_steps,
             'total_timeSteps': n_part_steps,
             }
        # put parallel info in first file base
        return d

    def _U2_code_version_info(self):
        try:
            git_revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path.dirname(path.realpath(__file__))).decode().replace('\n','')
        except:
            git_revision = 'unknown'
        return { 'version': code_version, 'git_revision': git_revision}