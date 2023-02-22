# method to run ocean tracker from parameters
# eg run(params)
code_version = '0.3.03.004 2023-01-13'

# todo kernal/numba based RK4 step
# todo short name map requires unique class names in package, this is checked on startup,add checks of uniqueness of user classes added from outside package


# Dev notes
# line debug?? python3.6 -m pyinstrument --show-all plasticsTrackOnLine_Main.py
# python -m cProfile
# python -m vmprof  <program.py> <program parameters>
# python -m cProfile -s cumtime

# do first to ensure its right
import multiprocessing


import time
from copy import deepcopy
from datetime import datetime


from os import path, makedirs
from sys import version, version_info
import traceback
import shutil
from time import perf_counter
from copy import  copy
import numpy as np

from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util import basic_util
from oceantracker.util import json_util

from oceantracker.util.message_and_error_logging import MessageLogging, append_message, GracefulExitError,FatalError
from oceantracker.util import time_util
from oceantracker.util.parameter_checking import merge_params_with_defaults, check_top_level_param_keys_and_structure
from oceantracker.oceantracker_case_runner import OceanTrackerCaseRunner
from oceantracker.common_info_default_param_dict_templates import  default_case_param_template, run_params_defaults_template, default_class_names, package_fancy_name
from oceantracker.util.parameter_base_class import make_class_instance_from_params


import subprocess

def run(user_params):
    OT= _RunOceanTrackerClass(user_params)
    full_runInfoJSON_file_name, has_errors = OT._run(deepcopy(user_params))
    return  full_runInfoJSON_file_name, has_errors

class _RunOceanTrackerClass(object):
    def __init__(self, params):
        self.run_log = MessageLogging('M:')
        rl = self.run_log
        rl.insert_screen_line()
        rl.write_msg('Starting ' + package_fancy_name + '  Version ' + code_version)
        rl.write_msg('Python version: ' + version, tabs=1)

        if type(params) is not dict:
            rl.write_msg('Parameter must be a dictionary or json/yaml file readable as a dictionary,given parameters are type=' + str(type(params)),
                hint='check parameter file or parameter variable is in dictionary form', exception=GracefulExitError)

            raise ValueError('Params must be a dictionary or json/yaml file readable as a dictioary,  got type=' + str(type(params)))

        if 'shared_params' not in params:
            rl.write_msg('Cannot find required top level parameter "shared_prams"',
                         hint='check parameter file or dictionary for  "shared_prams" key', exception=GracefulExitError)

        vi = version_info
        install_hint = 'Install Python 3.10 or used environment.yml to build a Conda virtual environment named oceantracker',
        if 'share_reader_memory' in params['shared_params'] and params['shared_params']['share_reader_memory']:
            # for shared reader python version must be >=3.8
            if not (vi.major == 3 and vi.major >= 8):
                rl.write_msg('To use shared reader memory ' +
                             package_fancy_name + ' requires Python 3 , version >= 3.8, disabling "share_reader_memory" parameter',
                             hint=install_hint, warning=True, tabs=1)
                params['shared_params']['share_reader_memory'] = False

        if (vi.major == 3 and vi.major >= 11):
            rl.write_msg(package_fancy_name + ' is not yet compatible with Python 3.11, as not al imported packages have been updated, eg Numba ',
                         hint=install_hint, exception=FatalError, tabs=1)
        if vi.major < 3:
            rl.write_msg(package_fancy_name + ' requires Python version 3 ', hint=install_hint,  exception = FatalError, tabs = 1)

        # todo check param structure here??
        pass

    def _run(self, user_params):

        # get shared params defaults
        # todo check param struntured
        msg_list=[]
        user_params['shared_params'], msg_list = merge_params_with_defaults(user_params['shared_params'],
                                        run_params_defaults_template['shared_params'], {},msg_list=msg_list, tag='shared_params')

        # make sure output dir is there, so to at least write errors
        #todo convert error catching to use message logging
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
        #package_info, msg_list = check_package(__file__)
        rl.add_messages(msg_list)

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
        run_info = {'user_note': {}, 'screen_log': [],
                    'run_started': datetime.now(),
                    'run_ended': None,
                    'elasped_time': None,
                    'performance': {},
                    'output_files': {},
                    }
        rl= self.run_log
        t0 = time.perf_counter()


        # clean up params
        working_params = deepcopy(params)

        working_params = self._B1_check_param_structure(working_params)

        # get defaults for shared params, to set up output locations etc, todo moved to dev above
        working_params['shared_params'], msg_list = merge_params_with_defaults(params['shared_params'], run_params_defaults_template['shared_params'], {}, msg_list=[], tag='shared_params')

        rl.set_max_warnings(working_params['shared_params']['max_warnings'])
        rl.insert_screen_line()
        rl.write_progress_marker('Running '+ package_fancy_name + ' started ' + str(datetime.now()))
        rl.write_progress_marker('Starting: ' + working_params['shared_params']['output_file_base'])

        # get info to build a reader
        reader_build_info, reader =self._C1_build_reader(params)

        rl.write_progress_marker('Input directory: ' + reader.params['input_dir'])
        rl.insert_screen_line()
        # write grid and outline and record file names
        if working_params['shared_params']['write_output_files']:
            output_files['grid'], output_files['grid_outline'] = self._U3_write_run_grid_netCDF(output_files, reader_build_info, reader)

        runner_params_test, shared_params, msg_list = self._E1_get_full_case_params(working_params, output_files, reader_build_info)
        # self.run_log.write_messages(msg_list)
        # run the cases, return list of case info json files which make up the run of all cases
        #----------------------------------------------------------------------------------------------
        output_files['case_info'], case_error = self._F1_run_case_list(runner_params_test, reader)
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
        rl.write_progress_marker('Finished ' + package_fancy_name + ' at ' + time_util.iso8601_str(datetime.now()))
        rl.write_progress_marker('Output in ' + output_files['run_output_dir'])
        rl.write_progress_marker('Run time  =  ' + str(run_info['elasped_time']))
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
        base_case_params = deepcopy(params['base_case_params'])
        base_case_params, msg_list = check_top_level_param_keys_and_structure(base_case_params, default_case_param_template,
                                                                              required_keys=[],
                                                                              tag='Checking base case  params', msg_list=msg_list)

        # build each case params
        processor_number = 0
        case_list = params['case_list'] # will have a dummy one anned in strcture checks if empty
        runner_params=[]
        shared_params= params['shared_params']

        for n_case, case in enumerate(case_list):
            # add replicate copies if required
            for n_replicate in range(shared_params['replicates']):
                # parameter list to run same particle on multiple threads
                c  = deepcopy(case)  # a set of parameters for this case
                c, msg_list = check_top_level_param_keys_and_structure(c, default_case_param_template,
                                                                       required_keys=[],
                                                                       tag='Checking case params', msg_list=msg_list)

                cout = {'run_params': {}, 'core_classes': {}, 'class_lists': {}}

                for key, item in c.items():
                    if item is None: continue
                    if key =='run_params':
                        cout['run_params'], msg_list = merge_params_with_defaults(c['run_params'],default_case_param_template['run_params'],
                                                                                   base_case_params['run_params'],
                                                                                 msg_list=msg_list, tag='case_run_params')
                        pass
                    elif type(item) == dict and key != 'reader':
                        # core classes
                        i, msg_list = make_class_instance_from_params(item,class_type_name=key,crumbs ='class param ' + key +' >> ',
                                                                      base_case_params= base_case_params[key], msg_list=msg_list)
                        if i is not None:
                            cout['core_classes'][key]= i.params
                    elif type(item) == list:
                        if key not in cout['class_lists']: cout['class_lists'][key] =[]
                        for n, cli in enumerate( item + base_case_params[key]):
                            i, msg_list = make_class_instance_from_params(cli,class_type_name=key, msg_list=msg_list,
                                                                    nseq=n,crumbs ='class list param ' + key +' >> ')

                            if i is not None:
                                cout['class_lists'][key].append(i.params)

                    else: pass # top level checks ensures items are dict or lists

                self.run_log.add_messages(msg_list)

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
                                    #'package_info':package_info,
                                    })  # add case/ copy to list for the pool



        self.run_log.check_messages_for_errors()
        return runner_params, shared_params, msg_list




    def _C1_build_reader(self, params):

        rl= self.run_log


        if 'class_name' not in params['reader']:
            FatalError('Reader must have class_name parameter')

        if not path.isdir(params['reader']['input_dir']):
            raise FatalError('Cannot find  input_dir (hindcast) directory = ' + params['reader']['input_dir'])

        params['reader']['input_dir'] = path.abspath(params['reader']['input_dir'])

        reader, msg_list = make_class_instance_from_params(params['reader'],class_type_name= 'reader')  # temporary  reader to get defaults
        reader.info['share_reader_memory'] = params['shared_params']['share_reader_memory']

        reader.shared_info.case_log = self.run_log #todo make shared info messages more consistent???, ie this is not a case
        rl.add_messages(msg_list)

        # construct reader_build_info to be used by case_runners to build their reader
        reader_build_info = {'reader_params': reader.params,
                             'use_shared_memory': params['shared_params']['share_reader_memory']}
        rl.write_progress_marker('Sorting hyrdo model files in time order')
        reader_build_info = self._C2_get_hindcast_files_info(reader_build_info, reader) # get file lists
        rl.write_progress_marker('Finished sorting hyrdo model  files ', tabs=2)
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

        if reader_build_info['use_shared_memory']:

            reader_build_info = reader.set_up_shared_grid_memory(reader_build_info)

            # add to class to shared info, alows fileds to be built
            si = reader.shared_info
            si.classes['reader'] = reader

            # set up reader fields
            reader.setup_reader_fields(reader_build_info)
            sm_fields = {}
            for name, sm in reader.shared_memory['fields'].items():
                sm_fields[name] = sm.get_shared_mem_map()

        return  reader_build_info, reader

    def _C2_get_hindcast_files_info(self, reader_build_info, reader):
        # read through files to get start and finish times of each file
        # create a time sorted list of files given by file mask in file_info dictionary
        # sorts based on time from read time,  assumes a global time across all files
        # note this is only called once by OceantrackRunner to form file info list,
        # which is then passed to  OceanTrackerCaseRunner

        # build a dummy non-initialise reader to get some methods and full params
        # add defaults from template, ie get reader class_name default, no warnings, but get these below
        # check cals name
        rl = self.run_log
        file_info =reader.get_list_of_files_and_hindcast_times(reader.params['input_dir'])

        # check some files found
        if len(file_info['names']) == 0:
            rl.write_msg('reader: cannot find any files matching mask "' + reader.params['file_mask']
                           + '"  in input_dir : "' + reader.params['input_dir'] + '"', exception = GracefulExitError)
        
        # checks on hindcast using first hindcast file 
        nc = NetCDFhandler(file_info['names'][0], 'r')
        msg_list = reader._basic_file_checks(nc, msg_list=[])
        rl.add_messages(msg_list)
        msg_list = reader.additional_setup_and_hindcast_file_checks(nc, msg_list=msg_list)
        rl.add_messages(msg_list)
        nc.close()
        self.run_log.add_messages(msg_list)

        # convert file info to numpy arrays for sorting
        keys = ['names','n_time_steps', 'time_start', 'time_end']
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

        # checks on hindcast
        if  file_info['n_time_steps_in_hindcast']< 2:
            rl.write_msg('Hindcast must have at least two time steps, found ' + str(file_info['n_time_steps_in_hindcast']),exception=FatalError)

        # check for large time gaps between files
        file_info['hydro_model_time_step'] = (file_info['time_end'][-1]-file_info['time_start'][0])/(file_info['n_time_steps_in_hindcast']-1)

        # check if time diff between starts of file and end of last are larger than average time step
        if len(file_info['time_start']) > 1:
            dt_gaps = file_info['time_start'][1:] -file_info['time_end'][:-1]
            sel = np.abs(dt_gaps) > 1.8 * file_info['hydro_model_time_step']
            if np.any(sel):
                rl.write_msg('Some time gaps between hindcast files is are > 1.8 times average time step, check hindcast files are all present??', hint='check hindcast files are all present and times in files consistent', warning=True)
                for n in np.flatnonzero(sel):
                    rl.write_msg('file gaps between ' + file_info['names'][n] + ' and ' + file_info['names'][n+1],tabs=1)

        reader_build_info['sorted_file_info'] = file_info
        rl.check_messages_for_errors()
        return reader_build_info

    def _U3_write_run_grid_netCDF(self, output_files, reader_build_info, reader):
        # write a netcdf of the grid from first hindcast file
        msg_list=[]

        grid= reader.grid

        # get depth from first hincast file
        hindcast = NetCDFhandler(reader_build_info['sorted_file_info']['names'][0], 'r')
        depth_var = reader.params['field_variables']['water_depth']
        if depth_var is not None and hindcast.is_var(depth_var):
            # world around to ensure depth read in right format
            field_params,var_info = reader.get_field_variable_info(hindcast,'water_depth',reader.params['field_variables']['water_depth'])
            water_depth = reader.read_file_field_variable_as4D(hindcast,var_info['component_list'][0],var_info['is_time_varying'], file_index=None)
            water_depth = reader.preprocess_field_variable(hindcast,'water_depth',water_depth)
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

        self.run_log.add_messages(msg_list)
        return grid_file, grid_outline_file

    def _F1_run_case_list(self, case_param_list, reader):
        # do run of all cases
        shared_params = case_param_list[0]['shared_params']
        case_results = []

        if reader.info['share_reader_memory']:
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
        msg_list =[]
        for case_file,case_error  in case_results:
            case_info_file_list.append(case_file)
            case_errors_list.append(case_error)
            if case_file is None and case_error is not None:
                append_message(msg_list, 'CaseInfo files missing  for case ' + str(n)
                                   + ', or other error, case may have not completed, check for .err file!!!!!!, error type= ' + case_error.__class__.__name__, warning=True)
            n+=1

        self.run_log.add_messages(msg_list)
        return case_info_file_list,  case_errors_list

    def run_serial(self,case_param_list):
        # serial or non-parallel mode,   run a single case non parallel to makes debuging easier and allows reruns of single case
        case_results = []
        for c in case_param_list:
            a = self._run1_case(c)
            case_results.append(a)
        return case_results

    def run_parallel(self,case_param_list):
        rl = self.run_log
        msg_list = []
        shared_params = case_param_list[0]['shared_params']
        shared_params['processors'] = min(shared_params['processors'], len(case_param_list))
        rl.write_progress_marker('oceantracker:multiProcessing: processors:' + str(shared_params['processors']))

        case_results= None

        try:
            with multiprocessing.Pool(processes=shared_params['processors']) as pool:
                case_results = pool.map(self._run1_case, case_param_list)
            append_message(msg_list, 'parallel pool complete')

        except Exception as e:
            append_message(msg_list, 'Error setting up parallel run')
            rl.write_error_log_file(e)
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
                n_time_steps += sinfo['n_time_steps_completed']
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