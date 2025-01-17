import sys


from copy import deepcopy, copy
from os import path, makedirs, walk, unlink
import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass

from time import  perf_counter
from oceantracker.util.message_logger import MessageLogger, GracefulError
from oceantracker.util import profiling_util, get_versions_computer_info

from oceantracker.field_group_manager import set_up_reader

#os.environ['NUMBA_NUM_THREADS'] = '2'

from oceantracker.util import time_util, output_util

from oceantracker.util import json_util, setup_util, class_importer_util
from datetime import datetime
from time import sleep
import traceback
from oceantracker.util.setup_util import config_numba_environment_and_random_seed
from oceantracker import definitions
from oceantracker.shared_info import shared_info as si

# note do not import numba here as its environment  setting must ve done first, import done below
class OceanTrackerParamsRunner(ParameterBaseClass):
    # this class runs a single case
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required

    def run(self, user_given_params):
        d0 = datetime.now()
        t_start = perf_counter()

        self._do_setup(user_given_params)
        ml = si.msg_logger

        # _________ do run ____________________________
        ml.hori_line()
        ml.msg('Starting run' + si.run_info.output_file_base   + ' at ' + time_util.iso8601_str(datetime.now()))
        ml.hori_line()

        self._run_case()
        # _____________________________________________

        # write a sumary of errors etc
        num_errors = len(ml.errors_list)
        ml.hori_line()
        ml.msg(
            f'Error counts - {num_errors:3d} errors, {len(ml.warnings_list):3d} warnings, {len(ml.notes_list):3d} notes, check above',
            tabs=3)
        ml.msg('')

        if num_errors > 0:
            ml.hori_line('Found errors, so some cases may not have completed')
            ml.hori_line(' ** see above or  *_caseLog.txt and *_caseLog.err files')
            ml.hori_line()

        ml.progress_marker('Finished' + si.run_info.output_file_base
                           + ' started: ' + str(d0) + ', ended: ' + str(datetime.now()))
        ml.msg('Computational time =' + str(datetime.now() - d0), tabs=3)
        ml.msg(f'Output in {si.run_info.run_output_dir}', tabs=1)
        ml.msg('')
        ml.hori_line(f'Finished Oceantracker run')
        ml.msg('')

        ml.close()

        case_info_file = self._get_case_run_info(d0, t_start)

        return case_info_file

    def _do_setup(self, user_given_params):
        # setup shared info and message logger
        si._setup()  # clear out classes from class instance of SharedInfo if running series of mains

        ml = si.msg_logger
        ml.reset()
        ml.set_screen_tag('prelim')
        setup_util.check_python_version(ml)

        ml.hori_line()
        ml.msg(f'{definitions.package_fancy_name} starting main:')

        # split params in to settings, core and class role params
        si.working_params = setup_util._build_working_params(deepcopy(user_given_params), si.msg_logger,
                                                             crumbs='Buling working params')
        ml.exit_if_prior_errors('Errors in merge_critical_settings_with_defaults', caller=self)

        si.add_settings(si.working_params['settings'])  # add full settings to shared info

        # setup output dir and msg files
        si.output_files = setup_util.setup_output_dir(si.working_params['settings'], crumbs='Setting up output dir')

        si.output_files['run_log'], si.output_files['run_error_file'] = ml.set_up_files(
            si.output_files['run_output_dir'],
            si.output_files[
                'output_file_base'] + '_runLog')  # message logger output file setup
        si.msg_logger.settings(max_warnings=si.settings.max_warnings)
        ml.msg(f'Output is in dir "{si.output_files["run_output_dir"]}"',
               hint='see for copies of screen output and user supplied parameters, plus all other output')

        # write raw params to a file
        setup_util.write_raw_user_params(si.output_files, user_given_params, ml)

        # setup numba before first import as its environment variable settings  have to be set before first import on Numba
        # set numba config environment variables, before any import of numba, eg by readers,
        setup_util.config_numba_environment_and_random_seed(si.working_params['settings'], ml, crumbs='main setup',
                                                            caller=self)  # must be done before any numba imports

        # add class importer, import all package parameter classes and build short name package tree to shared info
        # must be after numba setup as it imports al classes
        si.class_importer = class_importer_util.ClassImporter(si.msg_logger)

        si.run_info.version = definitions.version
        si.run_info.computer_info = get_versions_computer_info.get_computer_info()

        ml.set_screen_tag('setup')
        ml.hori_line()
        ml.msg(f' {definitions.package_fancy_name} version {definitions.version["str"]} ')

        ml.exit_if_prior_errors('parameters have errors')

        # cpty basic  shortcuts to run info
        ri = si.run_info

        # move stuff to run info as central repository
        ri.run_output_dir = si.output_files['run_output_dir']
        ri.output_file_base = si.output_files['output_file_base']
        ri.model_direction = -1 if si.settings.backtracking else 1  # move key  settings to run Info
        ri.time_of_nominal_first_occurrence = -ri.model_direction * 1.0E36

    def _run_case(self):
        ml = si.msg_logger # shortcut for logger

        si.add_settings(si.working_params['settings']) # push settings into shared info

        ml.exit_if_prior_errors('Errors in settings??', caller=self)
        # transfer all settings to shared_info.settings to allow tab hints

        try:
            # - -------- start set up---------------------------------------------------------------------

            # must make fields first, so other claseses can add own required fields
            self._build_field_group_manager(si.working_params)

            self._make_all_class_instances_from_params(si.working_params)

            self._add_release_groups_to_get_run_start_end(si.working_params)

            self._initial_setup_all_classes(si.working_params)

            self._final_setup_all_classes()

            self._do_run_integrity_checks()

            ml.exit_if_prior_errors('Errors in setup??', caller=self)

            # -----------run-------------------------------
            self.info['model_run_started'] = datetime.now()
            si.msg_logger.hori_line()
            si.msg_logger.progress_marker('Starting ' + si.run_info.output_file_base + ',  duration: ' + time_util.seconds_to_pretty_duration_string(si.run_info.duration))

            si.core_class_roles.solver.solve() # do time stepping


            # ----------ended--------------------------------

        except GracefulError as e:
            ml.show_all_warnings_and_errors()
            ml.msg(f' Case Runner graceful exit ', hint ='Parameters/setup has errors, see above', error= True)
            ml.write_error_log_file(e, traceback.format_exc())

        except Exception as e:
            ml.show_all_warnings_and_errors()
            ml.msg(f' Unexpected error  ', error=True,hint='check above or .err file')
            tb = traceback.format_exc()

            ml.write_error_log_file(e, tb)
            # printout out trace back
            ml.msg(str(e))
            ml.msg(tb)

        finally:
            # ----- wrap up ---------------------------------
            ml.set_screen_tag('end')
            ml.hori_line()

            si.output_files['release_groups'] = output_util.write_release_group_netcdf()      # write release groups
            for i in si._all_class_instance_pointers_iterator(): i.close()     # close all instances, eg their files if not close etc

            # check for non-releases
            # flag if some release groups did not release
            for name, i in si.class_roles.release_groups.items():
                if i.info['number_released'] == 0:
                    ml.msg(f'No particles were released by release_group named= "{name}"', error=True,
                           caller= i, hint='Release point/polygon or grid may be outside domain and or in permanently dry cells)')

            ml.show_all_warnings_and_errors() # reshow warnings

            self.close()  # close all classes and msg logger

    def _make_all_class_instances_from_params(self, working_params):

        fgm = si.core_class_roles['field_group_manager']
        ccr = working_params['core_class_roles']
        for role, params in ccr.items():
            if role in ['particle_group_manager', 'solver', 'tidal_stranding']:
                i= si.add_class(role,params=params)
            pass

        if si.settings['use_dispersion']:
            i = si.add_class('dispersion', params= ccr['dispersion'])

        if fgm.info['is3D']:
            i = si.add_class('resuspension', params=ccr['resuspension'])

        if si.settings.write_tracks:
            si.add_class('tracks_writer', params= ccr['tracks_writer'], crumbs='making tracks writer class instance',
                         caller=self)

        # do class role lists
        for role, param_list in working_params['class_roles'].items():
            if role in ['nested_readers']: continue

            for params in param_list:
                i = si.add_class(role, params=params)

        if ccr['integrated_model'] is not None:
            si.add_class('integrated_model', ccr['integrated_model'])
        pass

    def _do_run_integrity_checks(self):
         # check all have required, fields, part props and grid data
        for i in si._all_class_instance_pointers_iterator():
            i.check_requirements()

        si.msg_logger.exit_if_prior_errors('errors found in _do_run_integrity_checks')

    def _initial_setup_all_classes(self,working_params):
        # initialise all classes, order is important!
        crumbs='initial_setup_all_classes>'
        t0 = perf_counter()

        fgm = si.core_class_roles.field_group_manager
        fgm.final_setup()


        fgm.add_part_prop_from_fields_plus_book_keeping()  # todo move back to make instances

        # particle group manager for particle handing infra-structure
        pgm = si.core_class_roles.particle_group_manager
        pgm.initial_setup()

        # schedule all release groups
        pgm.info['max_age_for_each_release_group'] = np.zeros((0,),dtype=np.int32)
        for name, i in si.class_roles.release_groups.items():
            p = i.params
            i.initial_setup() # delayed set up
            i.add_scheduler('release',start=p['start'], end=p['end'], duration=p['duration'],
                            interval =p['release_interval'], crumbs=f'Adding release groups scheduler {name} >')
            # max_ages needed for culling operations
            max_age = si.info.large_float if i.params['max_age'] is None else i.params['max_age']
            pgm.info['max_age_for_each_release_group'] = np.append(pgm.info['max_age_for_each_release_group'], max_age)

        # make other core classes
        ccr = si.core_class_roles
        ccr.solver.initial_setup()

        if si.settings['use_dispersion']:
            ccr.dispersion.initial_setup()

        if si.run_info.is3D_run and si.settings['use_resuspension']:
            ccr.resuspension.initial_setup()


        # initialise other user classes, which may depend on custom particle props above or reader field, not sure if order matters
        for role in ['particle_properties','time_varying_info','velocity_modifiers', 'trajectory_modifiers', 'particle_statistics', 'particle_concentrations', 'event_loggers']:
            for name, i in si.class_roles[role].items():
                i.initial_setup()

        if si.settings.write_tracks:
            si.core_class_roles.tracks_writer.initial_setup()

        # do integrated models last, which may add release groups
        if si.core_class_roles.integrated_model is not None:
            si.core_class_roles.integrated_model.initial_setup()


        si.msg_logger.progress_marker('Done initial setup of all classes', start_time=t0)

    def _final_setup_all_classes(self):
        # finlaise alll partimes after all inatilaised

        for role, i in si.core_class_roles.as_dict().items():
            if i is not None:
                i.final_setup()

        for role, item in si.class_roles.as_dict().items():
            for name, i in item.items():
                if i is not None:
                    i.final_setup()  # some require instanceID from above add class to initialise

    def _add_release_groups_to_get_run_start_end(self, working_params):
        # particle_release groups setup and instances,
        # find extremes of  particle existence to calculate model start time and duration
        t0 = perf_counter()
        ri = si.run_info
        md = ri.model_direction
        fgm= si.core_class_roles.field_group_manager
        hi_start,hi_end = fgm.info['start_time'],fgm.info['end_time']

        crumbs = 'adding release groups'
   
        if len(si.class_roles['release_groups']) == 0:
            si.msg_logger.msg('No particle "release_groups" parameters found', error=True, caller=self)
        si.msg_logger.exit_if_prior_errors('Errors adding release groups??')

        # set up to start end times based on release_groups
        # set up release groups and find first release time to start model
        first_time = []
        last_time = []
        default_start = hi_end   if si.settings.backtracking else hi_start
        default_end   = hi_start if si.settings.backtracking else hi_end

        for name, rg in si.class_roles['release_groups'].items():
            rg_params = rg.params
            rg.initial_setup()
            start =  default_start if rg_params['start'] is None else  rg_params['start']
            end = default_end if rg_params['end'] is None else rg_params['end']
            duration = si.info.large_float if rg_params['duration'] is None else rg_params['duration']

            # end time takes presence over given duration
            if rg_params['end'] is not None:
                duration = abs(end-start)

            life_span = duration if rg_params['max_age'] is None else duration + rg_params['max_age']

            first_time.append(start)
            last_time.append( start + md * life_span)

        # set model run start/end time allowing for back tracking
        start_time = np.min(md * np.asarray(first_time)) * md
        end_time   = np.max(md * np.asarray(last_time)) * md

        # clip end time to be within hincast
        if si.settings.backtracking:
            end_time = max(end_time, hi_start)
        else:
            end_time = min(end_time, hi_end)

        # get duration clipped by max duration
        duration =  abs(end_time-start_time)
        if si.settings.max_run_duration is not None:  duration = min(si.settings.max_run_duration,duration)

        end_time = start_time + md * duration

        # record info in run
        ri.start_time = start_time
        ri.end_time = end_time
        ri.duration = duration
        ri.times    = ri.start_time  + md * np.arange(0., ri.duration + si.settings.time_step, si.settings.time_step)
        ri.end_time = ri.times[-1] # adjust end to last time step

        # useful information
        ri.duration = abs(ri.times[-1] - ri.times[0])
        ri.start_date = time_util.seconds_to_isostr(ri.times[0])
        ri.end_date = time_util.seconds_to_isostr(ri.times[-1])
        ri.dates = time_util.seconds_to_isostr(ri.times)
        ri.duration_str = time_util.seconds_to_pretty_duration_string(ri.duration)
        ri.backtracking = si.settings.backtracking

        si.msg_logger.progress_marker('Added release groups and found run start and end times', start_time=t0)


    def _build_field_group_manager(self, working_params):
        # initialise all classes, order is important!
        # shortcuts
        info = self.info
        si.msg_logger.progress_marker('Start  field group manager and readers setup')
        t0 = perf_counter()

        # start with setting up field groups, which set up readers
        # as it has info on whether 2D or 3D which  changes class options'
        # reader prams should be full and complete from oceanTrackerRunner, so dont initialize
        # chose file manager for normal or nested readers
        if len(working_params['class_roles']['nested_readers']) > 0:
            # use development nested readers class field group manager
            if working_params['core_class_roles']['field_group_manager'] is None: working_params['core_class_roles']['field_group_manager'] ={}
            if 'class_name' not in working_params['core_class_roles']['field_group_manager']:
                working_params['core_class_roles']['field_group_manager']['class_name'] = definitions.default_classes_dict['field_group_manager_nested']

        # set up fields
        fgm = si.add_class('field_group_manager',working_params['core_class_roles']['field_group_manager'])
        fgm.initial_setup(caller=self)

        # tweak settings based on available fields etc
        si.settings.use_geographic_coords = fgm.info['geographic_coords'] or si.settings.use_geographic_coords
        si.settings.use_A_Z_profile = fgm.info['has_A_Z_profile'] and si.settings.use_A_Z_profile
        si.settings.use_bottom_stress = fgm.info['has_bottom_stress'] and si.settings.use_bottom_stress

        si.run_info.is3D_run = fgm.info['is3D']
        if not si.run_info.is3D_run:
            si.settings.use_resuspension = False

        # now setup reader knowing if geographic, if A_Z_profile or bottom stress available,  and in use
        fgm.build_reader_grid_fields()

        si.run_info.vector_components = 3 if si.run_info.is3D_run else 2
        fgm.final_setup()

        si.run_info.hindcast_start_time = fgm.info['start_time']
        si.run_info.hindcast_end_time = fgm.info['end_time']

        si.msg_logger.progress_marker('Finished field group manager and readers setup', start_time=t0)

    # ____________________________
    # internal methods below
    # ____________________________
    def _get_case_run_info(self, d0, t0):
        pgm= si.core_class_roles.particle_group_manager
        info = self.info
        ml = si.msg_logger
        elapsed_time_sec = perf_counter() -t0
        info.update(dict(started=str(d0), ended=str(datetime.now()),
                         duration=str(datetime.now() - d0),
                         elapsed_time_sec=elapsed_time_sec,
                         number_particles_released= pgm.info['particles_released'] if pgm  is not None else None ))
        info.update(si.run_info.as_dict())
        # base class variable warnings is common with all descendants of parameter_base_class
        d = {'user_note': si.settings['user_note'],
             'file_written': datetime.now().isoformat(),
             'output_files': deepcopy(si.output_files),
             'version_info':   si.run_info.version,
             'computer_info':  si.run_info.computer_info,

             'working_params': dict(settings = si.settings.as_dict() ,core_class_roles={}, class_roles={}),
             'timing':dict(block_timings=[], function_timers= {}),
             'update_timers': {},
             'settings' : si.settings.as_dict(),
             'run_info' : info,
             'particle_status_flags': si.particle_status_flags.asdict(),
             'errors': si.msg_logger.errors_list,
             'warnings': si.msg_logger.warnings_list,
             'notes': si.msg_logger.notes_list,
             'release_group_info': {},
             'scheduler_info': {},
             'class_roles_info': {},
             }

        # sweep up any output files from al used classes
        class_info={}
        for key, i in si.class_roles.as_dict().items():
            if i is None : continue
            class_info[key] = {}
            d['scheduler_info'][key] = {}
            d['update_timers'][key] = {}
            d['output_files'][key] = {}
            d['working_params']['class_roles'][key] = {}
            # interate over dict
            for key2, i2 in i.items():
                class_info[key][key2]= i2.info
                d['update_timers'][key][key2] =dict( time_spent_updating= i2.info[ 'time_spent_updating'],
                                                     update_calls= i2.info[ 'update_calls'],
                                                     time_first_update_call=i2.info['time_first_update_call'],
                                                     )
                d['output_files'][key][key2]= i2.info['output_file'] if 'output_file' in i2.info else None
                if hasattr(i2,'scheduler_info'):
                    d['scheduler_info'][key][key2] = i2.scheduler_info

                # full parameters
                p = deepcopy(i2.params)
                if key == 'release_groups':  # don't put release point locations which may make json too big
                    p['points'] = 'points may be too large for json, read release_groups netCDF file, '
                d['working_params']['class_roles'][key][key2] = p

        # rewrite release groups in net cdf
        d['output_files']['release_groups'] = si.output_files['release_groups']

        d['release_group_info'] = class_info['release_groups']

        # core roles
        for key, i in si.core_class_roles.as_dict().items():
            if i is None: continue
            class_info[key] = {}
            class_info[key] = i.info
            #todo move all output files to si.output_files, not info
            d['output_files'][key] = i.info['output_file'] if 'output_file' in i.info else None
            d['update_timers'][key] = dict(time_spent_updating= i.info['time_spent_updating'],
                                                 update_calls= i.info['update_calls'],
                                                 time_first_update_call= i.info['time_first_update_call'] )
            if hasattr(i, 'scheduler_info'):
                d['scheduler_info'][key]= i.scheduler_info

            d['working_params']['core_class_roles'][key] = i.params

        keys= []
        times=[]
        for key, f in profiling_util.func_timings.items():
            times.append(f['time'])
            keys.append(key)
            f['msec_per_call'] = 1000*f['time']/f['calls']
            f['% of total time'] = 100*f['time']/elapsed_time_sec

        # add in reverse timing order
        for n in np.argsort(np.asarray(times))[::-1]:
            d['timing']['function_timers'][keys[n]]= profiling_util.func_timings[keys[n]]

        # block timings in time order
        b = si.block_timers
        times = np.asarray( [item['time'] for key, item in b.items()])
        order = np.argsort(times)[::-1]
        for key in [list(b.keys())[i] for i in order]:
            l = f' {100*b[key]["time"]/elapsed_time_sec:5.1f}% {key} : calls {b[key]["calls"]:4d}, {time_util.seconds_to_pretty_duration_string(b[key]["time"])}'
            d['timing']['block_timings'].append(l)
        d['timing']['block_timings'].append(f'--- Total time {time_util.seconds_to_pretty_duration_string(elapsed_time_sec)}')

        d['class_roles_info'] = class_info

        # check numba code for SIMD
        if True:
            from oceantracker.util import numba_util
            d['numba_code_info'] = numba_util.get_numba_func_info()

        case_info_file = path.join(si.output_files[ 'run_output_dir'],si.output_files['caseInfo_file'])
        json_util.write_JSON(case_info_file, d)
        return case_info_file
