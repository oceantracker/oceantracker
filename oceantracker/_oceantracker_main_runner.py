# do first to ensure its right
import multiprocessing

from copy import deepcopy
from datetime import datetime, timedelta

from os import path, makedirs, walk, unlink
import shutil
from time import perf_counter
from copy import  copy, deepcopy
import numpy as np
from glob import glob
import xarray as xr
from oceantracker.util import setup_util, class_importer_util, time_util
from oceantracker import definitions

from oceantracker.util import json_util ,yaml_util, get_versions_computer_info
from oceantracker.util.message_logger import GracefulError, MessageLogger
from oceantracker.reader.util import get_hydro_model_info
from oceantracker.reader._oceantracker_dataset import OceanTrackerDataSet

import traceback

from  oceantracker.shared_info import shared_info as si

msg_logger= MessageLogger()

class _OceanTrackerRunner(object):
    def __init__(self):
        pass

    def run(self, user_given_params):
        ml = msg_logger
        ml.reset()
        ml.set_screen_tag('Main')
        setup_util.check_python_version(ml)
        self.start_t0 = perf_counter()
        self.start_date = datetime.now()

        ml.print_line()
        ml.msg(f'{definitions.package_fancy_name} starting main:')
        # add classiport and short name package tree to shared info
        self.class_importer = class_importer_util.ClassImporter(ml)

        # start forming the run builder
        crumbs = 'Forming run builder'
        working_params, working_case_list_params = self._build_working_params(deepcopy(user_given_params), crumbs=crumbs)

        # base case run builder
        run_builder = dict( working_params = working_params,
                            version = definitions.version,
                            computer_info = get_versions_computer_info.get_computer_info())

        #  merge defaults of bee case settings which have to be the same for all cases
        working_params['settings'] = setup_util.merge_settings(working_params['settings'], si.default_settings,
                                                               ml, crumbs=crumbs, caller=self)
        si.add_settings(working_params['settings'])

        ml.exit_if_prior_errors('Errors in merge_critical_settings_with_defaults' ,caller=self, crumbs=crumbs)

        # setup output dir and msg files
        t0 = perf_counter()
        o = self.setup_output_dir(working_params['settings'], ml, crumbs= crumbs + '> Setting up output dir')

        o['run_log'], o['run_error_file'] = ml.set_up_files(o['run_output_dir'], o['output_file_base' ] +'_run') # message logger output file setup
        run_builder['output_files'] = o

        ml.msg(f'Output is in dir "{o["run_output_dir"]}"', hint='see for copies of screen output and user supplied parameters, plus all other output')


        # write raw params to a file
        setup_util.write_raw_user_params(run_builder['output_files'], user_given_params, ml)

        # set numba config environment variables, before any import of numba, eg by readers,
        setup_util.config_numba_environment_and_random_seed(working_params['settings'], ml, crumbs='main setup', caller=self)  # must be done before any numba imports

        ml.print_line()
        ml.msg(f' {definitions.package_fancy_name} version {definitions.version["str"]} - preliminary setup')

        ml.exit_if_prior_errors('parameters have errors')

        run_builder['reader_builder'], run_builder['nested_reader_builders'] = self._create_reader_builders(run_builder)

        if len(working_case_list_params) == 0 :
            # no case list
            case_info_file = self._run_single(run_builder)
        else:
            # run // case list with params as base case defaults for each run
            case_info_file = self._run_parallel(run_builder, working_case_list_params, )

        ml.close()
        return case_info_file
    def _build_working_params(self, params, crumbs=''):
        ml = msg_logger
        if type(params) != dict:
            ml.msg('Parameters must be of type dict, ', hint=f'Got type {str(type(params))} ', fatal_error=True, exit_now=True)

        # check for reder classes
        if 'reader' not in params or len(params['reader']) < 2:
            ml.msg('Parameter "reader" is required, or missing required parameters',
                   hint='Add a "reader" top level key to parameters with a dictionary containing  at least "input_dir" and "file_mask" keys and values',
                   fatal_error=True, crumbs='case_run_set_up', caller=self)

        # split apart params and case list

        if 'case_list' in params:
            case_list = params['case_list']
            if type(case_list) != list:
                ml.msg('Parameter "case_list"  must be of type list, ', hint=f'Got type {str(type(case_list))} ', fatal_error=True, exit_now=True)

            params.pop( 'case_list')
        else:
            case_list =[]

        working_params = setup_util.decompose_params(si, params, msg_logger=ml, crumbs=crumbs + ' Forming working params ', caller=self)

        # decomopse ech cae
        working_case_list_params = []
        for n, c in enumerate(case_list):
            p = setup_util.decompose_params(si, c, msg_logger=ml, crumbs=crumbs + f' Forming working params from case list #{n}', caller=self)
            working_case_list_params.append(p)

        return working_params, working_case_list_params

    def _run_single(self, run_builder):

        ml = msg_logger
        # build hincast catlog  list of files etc in time order
        run_builder['caseID'] = 0  # tag case

        # try catch is needed in notebooks to ensure mesage loger file is close,
        # which allows rerunning in notebook without  permission file errors
        try:
            # keep oceantracker_case_runner out of main namespace
            from oceantracker._oceantracker_case_runner import OceanTrackerCaseRunner
            # make instance of case runer and run it with decomposed working params
            ot_case_runner = OceanTrackerCaseRunner()
            case_summary = ot_case_runner.run_case(run_builder)

        except Exception as e:
            # ensure message loggers are closed

            print(str(e))
            traceback.print_exc()
            return None

        case_info_files = self._main_run_end(case_summary, run_builder)

        # check is case ran
        if case_summary['case_info_file'] is None:
            ml.msg('case_info_file is None, run may not have completed', fatal_error=True)

        return case_info_files

    def _main_run_end(self, case_summary, run_builder):
        # final info output

        ml = msg_logger
        ml.set_screen_tag('End')
        ml.print_line('Summary')
        ml.msg('Run summary with case file names in "*_runInfo.json"', tabs=2, note=True)
        ml.show_all_warnings_and_errors()
        ml.print_line()

        # count total messages
        num_case_errors, num_case_warnings, num_case_notes = 0, 0, 0
        failed_count = 0
        for c in case_summary if type(case_summary) == list else [case_summary]:
            m = c['msg_counts']
            num_case_errors += m['errors']
            num_case_warnings += m['warnings']
            num_case_notes += m['notes']
            failed_count += c['has_errors']

        case_info_files = self._write_run_info_json(case_summary, run_builder)

        ml.print_line()
        ml.msg(f'OceanTracker summary:  elapsed time =' + str(datetime.now() - self.start_date), )
        ml.msg(f'Cases - {num_case_errors:3d} errors, {num_case_warnings:3d} warnings, {num_case_notes:3d} notes, check above', tabs=3)
        ml.msg(f'Main  - {ml.error_count:3d} errors, {ml.warning_count:3d} warnings, {ml.note_count:3d} notes, check above', tabs=3)
        ml.msg(f'Output in {si.run_info.run_output_dir}', tabs=1)
        ml.print_line()
        total_errors = num_case_errors + len(ml.errors_list)
        if total_errors > 0:
            ml.print_line('Found errors, so some cases may not have completed')
            ml.print_line(' ** see above or  *_caseLog.txt and *_caseLog.err files')
            ml.print_line()
        ml.close()
        return case_info_files if failed_count == 0 else None

    def _run_parallel(self, run_builder, working_case_list_params):
        # run list of case params
        ml = msg_logger
        base_working_params = run_builder['working_params']

        case_run_builder_list = []

        for n_case, case_params in enumerate(working_case_list_params):
            case_working_params = setup_util.merge_base_and_case_working_params(base_working_params, n_case, case_params, si.base_case_only_params, ml,
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
        n_proc = base_working_params['settings']['processors']
        if n_proc is None:
            n_proc = max(run_builder['computer_info']['CPUs_hardware'] - 2, 1)

        n_proc = min(n_proc, len(working_case_list_params))  # limit to number of cases

        ml.progress_marker('oceantracker:multiProcessing: processors:' + str(n_proc))
        if base_working_params['settings']['multi_processing_method'] is not None:
            multiprocessing.set_start_method(base_working_params['settings']['multi_processing_method'])

        # run // cases
        with multiprocessing.Pool(processes=n_proc) as pool:
            case_summaries = pool.map(self._run1_case, case_run_builder_list)

        ml.progress_marker('parallel pool complete')

        case_info_files = self._main_run_end(case_summaries, run_builder)
        return case_info_files

    @staticmethod
    def _run1_case(working_params):
        # run one process on a particle based on given family class parameters
        # by creating an independent instances of  model classes, with given parameters

        # keep oceantracker_case_runner out of main namespace
        from oceantracker._oceantracker_case_runner import OceanTrackerCaseRunner

        ot = OceanTrackerCaseRunner()
        case_summary = ot.run_case(deepcopy(working_params))
        return case_summary

    def _create_reader_builders(self, run_builder):
        # created a dict which can be used to build a reader
        t0 = perf_counter()
        ml = msg_logger
        crumbs = '_get_hindcast_file_info> '
        working_params = run_builder['working_params']

        # primary reader
        reader_builder= self._make_a_reader_builder(run_builder,working_params['core_roles']['reader'], crumbs)
        json_util.write_JSON(path.join(run_builder['output_files']['run_output_dir'], 'hindcast_variable_catalog.json'), reader_builder['catalog'])

        # work out in 3D run from water velocity
        run_builder['is3D_run'] = self._detect_3D_velocity(reader_builder)

        # remove any fields that cant be used in 2D
        if not run_builder['is3D_run']:
            fi = reader_builder['reader_field_info']
            for name in fi.keys():
                if fi[name]['params']['is3D']: fi.pop(name)
            # disable resuspension
            run_builder['working_params']['settings']['use_resuspension'] = False

        # get file info for nested readers
        nested_reader_builders = []
        if 'nested_readers' not in working_params['roles']: working_params['roles']['nested_readers'] = []

        for n, nested_reader_params in enumerate(working_params['roles']['nested_readers']):
            t0 = perf_counter()
            nested_reader_builder = self._make_a_reader_builder(run_builder, nested_reader_params, crumbs = crumbs+f'> nested reader#{n}')
            json_util.write_JSON(path.join(run_builder['output_files']['run_output_dir'], f'hindcast_variable_catalog_ested_reader{n:03d}.json'),
                                                        nested_reader_builder['catalog'])
            nested_reader_builders.append(nested_reader_builder)
            ml.progress_marker(f'sorted nested hyrdo-model #{n} files in time order ', start_time=t0)

        ml.progress_marker('sorted hyrdo-model files in time order', start_time=t0)

        return reader_builder, nested_reader_builders
    def _make_a_reader_builder(self,run_builder, reader_params, crumbs):
        crumbs = crumbs +'>_make_a_reader_builder '

        reader_builder = dict(params=reader_params)

        file_list = self._check_input_dir(reader_builder['params'], crumbs=crumbs)

        # detect reader format and add clas_name to params
        reader_builder['params'], reader = self._detect_hydro_file_format(reader_builder['params'], file_list, crumbs=crumbs)

        reader_builder['catalog'] = self._get_hydro_file_catalog(reader_builder['params'],crumbs=crumbs)

        # add info to reader bulider on if 3D hindcast and mapped fields
        reader_builder = self._map_and_catagorise_field_variables(run_builder, reader_builder, reader)

        # add custom fields
        reader_builder['custom_field_params'] = dict()
        for n, params in enumerate( run_builder['working_params']['roles']['fields']):
            if 'name' not in params:
                msg_logger.msg(f'Custom field #{n} must have both a "name" and "class_name" parameters',
                               hint=f'given parameters are {str(params)}', fatal_error=True, caller=self)
                continue

            params.update(time_buffer_size=reader_builder['params']['time_buffer_size'],
                          nodes=reader_builder['hindcast_info']['num_nodes'],
                          zlevels=reader_builder['hindcast_info']['num_z_levels'])
            reader_builder['custom_field_params'][params['name']] = params

        # add field params for those required by other classes
        reader_builder = self._add_field_params_added_by_classes_code( run_builder['working_params'], reader_builder)

        return reader_builder

    def _detect_3D_velocity(self, reader_builder):
        # check if water velocity variables are there, if not swap to depth averaged versions if present
        is3D_run = True
        fi =  reader_builder['reader_field_info']

        if 'water_velocity' not in fi:
            if  'water_velocity_depth_averaged' not in fi:
                # use depth average if vailable
                msg_logger.msg('Cannot find water_velocity or depth averaged water velocity in hindcast',
                        hint=f'Found variables mapped to {str(fi.keys())} \n File variables are {str(reader_builder["catalog"]["variables"].keys())}',
                        fatal_error=True, exit_now=True)

            fi['water_velocity'] = fi['water_velocity_depth_averaged']
            fi.pop('water_velocity_depth_averaged')
            msg_logger.msg('No 3D velocity variables in hindcast, using depth averaged water velocity instead in 2D mode', note=True)
            is3D_run = False

        return is3D_run

    def setup_output_dir(self, params, msg_logger, crumbs='', caller=None):

        # setus up params, opens log files/ error handling, required befor mesage loger can be used
        crumbs += '> setup_output_dir'

        # check outpu_file_base is not dir, just a test
        if len(path.dirname(params['output_file_base'])) > 0:
            msg_logger.msg(f'The setting "output_file_base" cannot include a directory only a text label, given output_file_base ="{params["output_file_base"]}"', fatal_error=True,
                           hint='Use setting "root_output_dir" to designate which dir. to place output files in',
                           crumbs=crumbs, caller=caller,
                           exit_now=True)

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
            msg_logger.msg(f'Failed to make run output dir:{run_output_dir}', fatal_error=True,
                           crumbs=crumbs, caller=caller,
                           exception=e, traceback_str=traceback.print_exc(), exit_now=True)

        # write a copy of user given parameters, to help with debugging and code support
        fb = 'users_params_' + params['output_file_base']
        output_files = {'root_output_dir': root_output_dir,
                        'run_output_dir': run_output_dir,
                        'output_file_base': params['output_file_base'],
                        'raw_output_file_base': copy(params['output_file_base']),
                        # this is need for grid file so it does not get a case number in // runs
                        'runInfo_file': params['output_file_base'] + '_runInfo.json',
                        'runLog_file': params['output_file_base'] + '_runScreen.log',
                        'run_error_file': params['output_file_base'] + '_run.err',
                        'users_params_json': fb + '.json',
                        }
        return output_files
    def _write_run_info_json(self, case_summary, run_builder):
        # read first case info for shared info
        ml = msg_logger
        o = run_builder['output_files']
        ci = deepcopy(case_summary)  # dont alter input
        if type(ci) is not list: ci = [ci]

        # finally get run totals of steps and particles across al cases and write
        n_time_steps = 0.
        total_alive_particles = 0
        case_info_list = []
        # load log files to get info on run from solver info
        for n, c in enumerate(ci):
            n_time_steps += c['run_info']['current_model_time_step']
            total_alive_particles += c['run_info']['total_alive_particles']
            if c['case_info_file'] is not None:
                case_info_list.append(path.join(path.basename(c['case_info_file'])))
            else:
                case_info_list.append(None)
                ml.msg(f'Case #{n:d} has no case info file, likely has crashed', warning=True)

        num_cases = len(ci)

        # JSON parallel run info data
        t0 = self.start_t0
        t1 = perf_counter()
        d0 = self.start_date
        d1 = d0 + timedelta(seconds=t1 - t0)
        d = {'output_files': {},
             'version_info': definitions.version,
             'computer_info': run_builder['computer_info'],
             'hindcast_info': run_builder['reader_builder']['catalog']['info'],
             'num_cases': num_cases,
             'elapsed_time': t1 - t0,
             'run_start': d0.isoformat(),
             'run_end': d1.isoformat(),
             'run_duration': time_util.seconds_to_pretty_duration_string(t1 - t0),
             'average_active_particles': total_alive_particles / num_cases if num_cases > 0 else None,
             'average_number_of_time_steps': n_time_steps / num_cases if num_cases > 0 else None,
             'particles_processed_per_second': total_alive_particles / (perf_counter() - t0),
             'case_summary': case_summary,
             }

        # get output file names

        d['output_files'] = {'root_output_dir': o['root_output_dir'],
                             'run_output_dir': o['run_output_dir'],
                             'output_file_base': o['output_file_base'],
                             'raw_output_file_base': o['raw_output_file_base'],  # this is need for grid file so it does not get a case number in // runs
                             'runInfo_file': o['runInfo_file'],
                             'runLog_file': o['runLog_file'],
                             'run_error_file': o['run_error_file'],
                             'users_params_json': o['raw_user_params'],
                             'caseInfo_files': case_info_list
                             }
        json_util.write_JSON(path.join(o['run_output_dir'], o['runInfo_file']), d)

        case_files = [path.join(run_builder['output_files']['run_output_dir'], f) for f in case_info_list]
        return case_files if len(case_files) > 1 else case_files[0]

    def _check_input_dir(self, reader_params,crumbs=''):
        ml = msg_logger
        crumbs = crumbs + 'get_hydro_file_catalog> '
        # check params and folders exists
        if 'input_dir' not in reader_params or 'file_mask' not in reader_params:
            ml.msg('Reader class requires settings, "input_dir" and "file_mask" to read the hindcast',
                   fatal_error=True, exit_now=True, crumbs=crumbs)
        # check input dir exists
        if path.isdir(reader_params['input_dir']):
            ml.progress_marker(f'Found input dir "{reader_params["input_dir"]}"')
        else:
            ml.msg(f'Could not find input dir "{reader_params["input_dir"]}"',
                   hint='Check reader parameter "input_dir"', fatal_error=True, exit_now=True)

        # file mask is optional
        if 'file_mask' not in reader_params: reader_params['file_mask'] = None

        # get the file_list
        # check files are there
        mask = path.join(reader_params['input_dir'], '**', reader_params['file_mask'])  # add subdir search
        file_list = glob(mask, recursive=True)
        if len(file_list) == 0:
            msg_logger.msg(f'No files found in input_dir, or its sub-dirs matching mask "{mask}"',
                           hint=f'searching with "gob" mask "{mask}"', fatal_error=True, exit_now=True)
        return file_list
    def _get_hydro_file_catalog(self, reader_params,  crumbs=''):
        t0 = perf_counter()
        ml = msg_logger
        # open hindcast dataset and get the catalog
        ds = OceanTrackerDataSet()
        cat = ds.build_catalog(reader_params['input_dir'], reader_params['grid_variable_map']['time'],
                               msg_logger=ml, crumbs=crumbs,
                               file_mask=reader_params['file_mask'])
        ml.progress_marker('Cataloged hydro-model files/variables in time order', start_time=t0)

        return cat

    def _detect_hydro_file_format(self, reader_params, file_list, crumbs=''):
        # detect hindcast format and add reader class_name to params if missing
        # return reader class_name if given
        ml = msg_logger

        if 'class_name' in reader_params:
            reader = self.class_importer.make_class_instance_from_params('reader',
                        reader_params, check_for_unknown_keys=True,caller=self,  # dont flag unknown keys
                        crumbs=crumbs + f'> loading given reader with class_name "{reader_params["class_name"]}"')
            return reader.params, reader

        # search all known readers for variable signature match
        # first build full set of instances of known readers
        # and their variable signatures
        known_readers={}
        for name, r in definitions.known_readers.items():
            params = deepcopy(reader_params)
            params['class_name'] = r
            reader = self.class_importer.make_class_instance_from_params('reader',
                    params, check_for_unknown_keys=False, # dont flag unknown keys
                    crumbs=crumbs + f'> loading reader "{name}"  class "{r}"', caller=self)
            known_readers[name] = dict(instance=reader,
                                variable_sig = reader.params['variable_signature'],
                                )

        # look through files to see which reader's signature matches
        # must check all files as varables may be split between files

        found_reader = None
        all_variables= set()
        for fn in file_list:
            ds= xr.open_dataset(fn)
            all_variables.union(set(ds.variables.keys()))
            for name, r in known_readers.items():
                # check if each variable in the signature
                found_var = [v in ds.variables for v in r['variable_sig']]
                # break if all variables are found for this reader
                if all(found_var):
                    found_reader = name
            if found_reader is not None: break

        if found_reader is None:
            ml.msg(f'Could not set up reader, no files in dir = "{reader_params["input_dir"]} found matching mask = "{reader_params["file_mask"]}"  (or "out2d*.nc" if schism v5), or files do no match known format',
                   hint='Check given input_dir and  file_mask params, check if any non-hydro netcdf files in the dir, otherwise may not be known format',
                   fatal_error=True, exit_now=True, crumbs=crumbs, caller=self)
        # match found
        ml.progress_marker(f'found hydro-model files of type  "{found_reader.upper()}"')
        # return merged params
        params = known_readers[found_reader]['instance'].params
        reader = known_readers[found_reader]['instance']
        return params, reader

    def _add_field_params_added_by_classes_code(self,working_params,reader_builder ):
        # get pasm for any fields added by classes in there add_any_required_fields() method using self.add_field
        # must be done first to allow the reader to build all required fields
        crumbs = 'Adding code required fields'

        settings = working_params['settings']

        # look at core classes which might require addition fields if they are used
        for used, role in zip([settings['use_resuspension'], settings['use_dispersion'], True],
                              ['resuspension', 'dispersion', 'tidal_stranding']):
            # make an instance to run is add_any_required_fields(catalog)
            if not used: continue
            params = working_params['core_roles'][role] if working_params['core_roles'][role] is not None else {}
            self._add_fields_from_one_class(role, params, settings, reader_builder, crumbs='')

        if working_params['core_roles']['integrated_model'] is not None:
            self._add_fields_from_one_class('integrated_model', working_params['core_roles']['integrated_model'],
                                            settings, reader_builder, crumbs='')

        # add fields required by other classes
        for role, param_list  in working_params['roles'].items():
            if role == 'nested_readers': continue # a reader wont add custom fields
            for params in param_list:
                self._add_fields_from_one_class(role, params, settings, reader_builder, crumbs=f' add classes for role {role}')

        return reader_builder

    def _add_fields_from_one_class(self, role, params, settings, reader_builder, crumbs=''):
        # and fields given by one class
        known_fields = list(reader_builder['reader_field_info'].keys()) \
                   + list(reader_builder['custom_field_params'].keys())

        i = self.class_importer.make_class_instance_from_params(role, params,
                                                                check_for_unknown_keys=False, crumbs=crumbs + f'> loading  {role}', caller=self)
        # get any fields it requires
        i.add_any_required_fields(settings,known_fields, msg_logger)

        for name in i.required_fields_info['reader']:
            if name not in reader_builder['reader_field_info']:
                msg_logger.msg(f'No reader field variable map for variable "{name}"',
                               hint=f'field added by class')
            reader_builder['params']['load_fields'] = list(set([name]+reader_builder['params']['load_fields']))

        # add required custom field params
        for name, params in i.required_fields_info['custom'].items():
            params.update(  time_buffer_size=reader_builder['params']['time_buffer_size'],
                            nodes= reader_builder['hindcast_info']['num_nodes'],
                            zlevels = reader_builder['hindcast_info']['num_z_levels'])
            reader_builder['custom_field_params'][name] = params
        pass

    def _map_and_catagorise_field_variables(self, run_builder,reader_builder, reader):
        # add to catalog if 3D hindcast and mapped internal fields to file variables
        # also builds field_info,  pamareters and info  required to set up reader fields
        ml = msg_logger
        catalog = reader_builder['catalog']

        reader_builder['hindcast_info'] = catalog['info']

        # additional info on vert grid etc, node dim etc
        hi = reader.get_hindcast_info(catalog)

        if hi['vert_grid_type'] is not None and hi['vert_grid_type'] not in si.vertical_grid_types.possible_values():
            ml.msg(f'Coding error, dont recognise vert_grid_type grid type, got {hi["vert_grid_type"]}, must be one of [None , "Slayer_or_LSC","Zlayer","Sigma"]',
                           hint=f'check reesder codes  get_hindcast_info() ', fatal_error=True)

        reader_builder['hindcast_info'].update(hi)

        # categorise field variables
        file_vars = catalog['variables']
        reader_field_vars_map = {}

        # loop over mapped variables and loaded variables
        mapped_fields= reader.params['field_variable_map']
        for name in list(set(reader.params['load_fields'] + list(mapped_fields.keys()))):
            # if named var not in map, try to use is name as a map,
            # ie load named field is a file varaiable name
            if name not in mapped_fields:
                    mapped_fields[name] = name
                    if name not in catalog['variables']:
                        ml.msg(f' No  field_variable_map to load variable named "{name}" and no variable in file matching this name, so can not load this field',
                               hint=f'Add a map for this variable readers "field_variable_map"  param or check spelling loaded variable name matches a file variable, current map is {str(mapped_fields)}',
                               fatal_error=True, exit_now=True)

            # decompose variabele lis
            var_list = mapped_fields[name]
            if type(var_list) != list: var_list = [var_list]  # ensure it is a list

            # use first variable to get basic info
            v1 = var_list[0]
            if v1 not in file_vars: continue

            field_params = dict(time_varying=file_vars[v1]['has_time'],
                                is3D = any(x in hi['all_z_dims'] for x in file_vars[v1]['dims']),
                                    )
            field_params['zlevels'] = reader_builder['hindcast_info']['num_z_levels'] if  field_params['is3D'] else  1

            # work out if variable is a vector field
            file_vars_info = {}

            dm = reader.params['dimension_map']
            for n_var, v in enumerate(var_list):
                if v not in file_vars: continue  # listed var not in file, eg vecotion variable has npo vertical velocity

                if dm['vector2D'] is not None and dm['vector2D'] in file_vars[v]['dims']:
                    n_comp = 2
                elif dm['vector3D'] is not None and dm['vector2D'] in file_vars[v]['dims']:
                    n_comp = 3
                else:
                    n_comp = 1

                s4D = [reader.params['time_buffer_size'] if field_params['time_varying'] else 1,
                       hi['num_nodes'],
                       hi['num_z_levels'] if field_params['is3D'] else 1,
                       n_comp ]

                file_vars_info[v] =dict(vector_components_per_file_var=n_comp,
                                        shape4D=np.asarray(s4D,dtype=np.int32))

            field_params['is_vector'] = sum(x['vector_components_per_file_var']for x in file_vars_info.values()) > 1
            reader_field_vars_map[name] = dict(file_vars_info=file_vars_info,
                                                params=field_params)
            if len(file_vars_info) < len(var_list):
                ml.msg(f'not all vector components found for field {name}',
                       hint=f'missing file variables {[x for x in var_list if x not in file_vars_info]}', warning=True)
        # record field map
        reader_builder['reader_field_info'] = reader_field_vars_map
        catalog['reader_field_info'] = reader_field_vars_map
        # add grid variable info
        reader_builder['grid_info'] = dict(variable_map=reader.params['grid_variable_map'])

        ml.exit_if_prior_errors('Errors matching field variables with those in the file, see above')

        return reader_builder

    def close(self):
        msg_logger.close()
