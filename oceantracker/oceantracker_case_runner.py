import os
import psutil
from copy import deepcopy
from os import path, environ, remove
from oceantracker.util.parameter_base_class import ParameterBaseClass

from time import  perf_counter
from oceantracker.util.messgage_logger import MessageLogger, GracefulError
from oceantracker.util import profiling_util, get_versions_computer_info
import numpy as np
from oceantracker.util import time_util, numba_util, output_util
from oceantracker.util import json_util, setup_util
from datetime import datetime
from time import sleep
import traceback
from oceantracker.util.setup_util import config_numba_environment_and_random_seed
from oceantracker import definitions

from oceantracker.shared_info import SharedInfo as si

# note do not import numba here as its environment  setting must ve done first, import done below
class OceanTrackerCaseRunner(ParameterBaseClass):
    # this class runs a single case
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required
        self.info['name'] = 'OceanTrackerCaseRunner'

    def run_case(self, run_builder):
        # one case

        d0 = datetime.now()
        t_start = perf_counter()
        crumbs = 'OceanTrackerCaseRunner setup'

        # give shared access to params

        #todo add memory monitor
        #python_process = psutil.Process(os.getpid())
        #si.mem_monitor = dict(python_procssID=python_process , updates=0,initial_men_used=python_process.memory_info().rss, total_mem_used=0) # use to monitot memory usage

        si.run_builder = run_builder
        si.working_params = run_builder['working_params']
        si.case_summary=dict(case_info_file=None)

        # setup shared info and message logger
        si._setup() # clear out classes from class instance of SharedInfo if running series of mains
        si.msg_logger.set_screen_tag(f'C{run_builder["caseID"]:03d}')
        si.msg_logger.settings(max_warnings=si.settings.max_warnings)
        ml = si.msg_logger # shortcut for logger

        # merge settings with defaults
        si.working_params['settings'] = setup_util.merge_settings(si.working_params['settings'], si.default_settings, si.settings.possible_values(),
                                                                  ml, crumbs=crumbs + '> case settings', caller=self)
        for key in si.settings.possible_values():
            setattr(si.settings, key, si.working_params['settings'][key])

        # set numba config environment variables, before any import of numba, eg by readers,
        # also done in main but also needed here for parallel runs
        config_numba_environment_and_random_seed(si.working_params['settings'], ml, crumbs='Starting case_runner', caller=self)  # must be done before any numba imports

        ml.exit_if_prior_errors('Errors in settings??', caller=self)
        # transfer all settings to shared_info.settings to allow tab hints



        # basic  shortcuts
        ri = si.run_info
        ri.caseID = run_builder['caseID']
        si.output_files = run_builder['output_files']

        # move stuff to run info as central repository
        ri.run_output_dir = si.output_files['run_output_dir']
        ri.output_file_base = si.output_files['output_file_base']
        # move settings to run Info
        ri.model_direction = -1 if si.settings.backtracking else 1
        ri.time_of_nominal_first_occurrence = -ri.model_direction * 1.0E36

        # set up message logging
        output_files = run_builder['output_files']
        output_files['case_log_file'], output_files['case_error_file'] = \
                    ml.set_up_files(output_files['run_output_dir'], output_files['output_file_base'] + '_caseLog')

        si.case_summary['case_info_file'] = path.join(ri.run_output_dir, ri.output_file_base) + '_caseInfo.json'

        ml.print_line()
        ml.msg('Starting case number %3.0f, ' % ri.caseID + ' '
                                      + ri.output_file_base
                                      + ' at ' + time_util.iso8601_str(datetime.now()))
        ml.print_line()

        # delay  start, which may avoid occasional lockup at start if many cases try to read same hindcast file at same time
        if si.settings['multiprocessing_case_start_delay'] is not None:
            delay = si.settings['multiprocessing_case_start_delay'] * (si.run_info.caseID % si.settings['processors'])
            ml.progress_marker('Delaying start by  ' + str(delay) + ' sec')
            sleep(delay)
            ml.progress_marker('Starting after delay  of ' + str(delay) + ' sec')


        t0=perf_counter()
        ml.progress_marker('Scanned OceanTracker to build short name map to the full class_names', start_time=t0)

        # set up profiling
        #profiling_util.set_profile_mode(si.settings['profiler'])



        # run info
        ri = si.run_info

        # case set up
        try:
            # setup fields to get hindcast info, ie starts and ends
            self._setup_fields()

            # add any para,s from intergrated moedl to the other  user supplied working params
            params = si.working_params['core_roles']['integrated_model']
            if len(params) > 0:
                im = si.add_core_role('integrated_model', params, crumbs='adding  "integrated_model" class',initialise=False)
                # any changes to params by model,
                # e.g. release groups from model which affect start and end times
                im.have_called_add_settings_and_class_params = False
                im.add_settings_and_class_params()
                im.have_called_add_settings_and_class_params = True # this is used to block use of im.add_class and im.settings


            # now  params commlet cabn set up

            # initialise all classes, order is important!
            # shortcuts
            t0 = perf_counter()
            fgm = si.core_roles.field_group_manager

            if si.settings.write_tracks:
                i = si.add_core_role('tracks_writer', si.working_params['core_roles']['tracks_writer'], initialise=True)
            else:
                si.core_roles.tracks_writer = None

            pgm = si.add_core_role('particle_group_manager', si.working_params['core_roles']['particle_group_manager'], crumbs=f'adding core class "particle_group_manager" ')
            pgm.initial_setup()  # needed here to add reader fields inside reader build

            # set up particle properties associated with fields etc
            fgm.add_part_prop_from_fields_plus_book_keeping()

            # make other core classes
            core_role_params = si.working_params['core_roles']
            si.add_core_role('solver', core_role_params['solver'], crumbs='adding core class solver ')
            si.add_core_role('dispersion', core_role_params['dispersion'],  default_classID='dispersion_random_walk', initialise=True)
            si.add_core_role('resuspension', core_role_params['resuspension'], default_classID='resuspension_basic', initialise=True)

            if si.settings.time_step > si.hindcast_info['time_step']:
                ml.msg(f'Results may not be accurate as, time step param={si.settings.time_step:2.0f} sec,  > hydo model time step = {si.hindcast_info["time_step"]:2.0f}',
                                  warning=True)
            # set up start time and duration based on particle releases
            self._setup_particle_release_groups_and_start_end_times(si.working_params['roles_dict']['release_groups'])

            self._make_and_initialize_user_classes()
            self._finalize_classes()  # any setup actions that mus be done after other actions, eg shedulers

            # model may depend on ther classes, so intilialise after all other claases are setup
            if si.core_roles.integrated_model is not None:
                im.initial_setup()
                im.final_setup()

            ml.exit_if_prior_errors('Errors in setup??', caller=self)

            self._do_a_run()


            # close all instances, eg their files if not close etc
            for i in si._all_class_instance_pointers_iterator():
                i.close()

            # write grid if first case
            if ri.caseID == 0:
                si.core_roles.field_group_manager.write_hydro_model_grid()

            case_info = self._get_case_info(d0, t_start)
            json_util.write_JSON(path.join(ri.run_output_dir,  si.case_summary['case_info_file'] ), case_info)

            # check for non-releases
            # flag if some release groups did not release
            for name, i in si.roles.release_groups.items():
                if i.info['number_released'] == 0:
                    ml.msg(f'No particles were release by group name= "{name}"', fatal_error=True,
                           caller= i, hint='Release point/polygon or grid may be outside domain and or in permanently dry cells)')

            ml.show_all_warnings_and_errors()

        except GracefulError as e:
            ml.show_all_warnings_and_errors()
            ml.msg(f' Case Runner graceful exit from case number [{ri.caseID:2}]', hint ='Parameters/setup has errors, see above', fatal_error= True)
            ml.write_error_log_file(e, traceback.format_exc())

        except Exception as e:
            ml.show_all_warnings_and_errors()
            ml.msg(f' Unexpected error in case number [{ri.caseID:2}] ', fatal_error=True,hint='check above or .err file')
            raise Exception()
            tb = traceback.format_exc()
            ml.write_error_log_file(e, tb)
            # printout out trace back
            ml.msg(str(e))
            ml.msg(tb)

        finally:
            # reshow warnings
            ml.print_line()
            ml.progress_marker('Finished case number %3.0f, ' % ri.caseID + ' '
                                          + si.run_info.output_file_base
                                          + ' started: ' + str(d0)
                                          + ', ended: ' + str(datetime.now()))
            ml.msg('Computational time =' + str(datetime.now() - d0), tabs=3)
            ml.print_line(f'End case {ri.caseID}')

        self.close()  # close al classes and msg logger

        ml.close()
        si.case_summary['run_info'] = si.run_info.as_dict()
        si.case_summary['msg_counts'] = {'errors': ml.error_count,
                                         'warnings': ml.warning_count,
                                         'notes': ml.note_count}






        return si.case_summary




    #@function_profiler(__name__)
    def _do_a_run(self):
        # build and run solver from parameter dictionary
        # run from a given dictionary to enable particle tracking on demand from JSON type parameter set
        # also used for parallel  version
        info= self.info
        info['model_run_started'] = datetime.now()

        solver = si.core_roles.solver

        # fill and process buffer until there is less than 2 steps
        si.msg_logger.print_line()
        si.msg_logger.progress_marker('Starting ' + si.run_info.output_file_base + ',  duration: ' + time_util.seconds_to_pretty_duration_string(si.run_info.duration))

        t0 = perf_counter()
        si.msg_logger.progress_marker('Initialized Solver Class', start_time=t0)

        # ------------------------------------------
        solver.solve()
        # ------------------------------------------

        si.output_files['release_group_info'] = output_util.write_release_group_netcdf()

        pass

    def _do_run_integrity_checks(self):
         # check all have required, fields, part props and grid data
        for i in si._all_class_instance_pointers_iterator():
            i.check_requirements()

        si.msg_logger.exit_if_prior_errors('errors found in _do_run_integrity_checks')


    def _setup_particle_release_groups_and_start_end_times(self, particle_release_groups_params_dict):
        # particle_release groups setup and instances,
        # find extremes of  particle existence to calculate model start time and duration
        t0 = perf_counter()
        pgm = si.core_roles.particle_group_manager
        ri = si.run_info
        # set up to start end times based on release_groups

        # set up release groups and find first release time to start model
        first_time = []
        last_time = []


        md = ri.model_direction

        for name, rg_params in particle_release_groups_params_dict.items():
            # make instance and initialise
            rg = pgm.add_release_group(name, rg_params)
            start, life_span = rg.get_start_time_and_life_span()

            first_time.append(start)
            last_time.append( start + md * life_span)

        # set model run start/end time allowing for back tracking
        ri.start_time = np.min(md * np.asarray(first_time)) * md
        ri.end_time   = np.max(md * np.asarray(last_time)) * md


        # clip end time to be within hincast
        if si.settings.backtracking:
            ri.end_time = max(ri.end_time, si.hindcast_info['start_time'])
        else:
            ri.end_time = min(ri.end_time, si.hindcast_info['end_time'])

        # make release times array
        duration =  abs(ri.end_time-ri.start_time)
        if si.settings.max_run_duration is not None:  duration = min(si.settings.max_run_duration,duration)

        ri.times    = ri.start_time  + md * np.arange(0., duration + si.settings.time_step, si.settings.time_step)
        ri.end_time = ri.times[-1] # adjust end to last time step

        # useful information
        ri.duration = abs(ri.times[-1] - ri.times[0])
        ri.start_date = time_util.seconds_to_isostr(ri.times[0])
        ri.end_date = time_util.seconds_to_isostr(ri.times[-1])
        ri.dates = time_util.seconds_to_isostr(ri.times)
        ri.duration_str = time_util.seconds_to_pretty_duration_string(ri.duration)

        # setup scheduler for each release group, how start and model times known
        #   this will round start times and release interval to be integer number of model time steps after the start
        for name, rg in si.roles.release_groups.items():
            si.add_scheduler_to_class('release_scheduler', rg, start=rg.params['start'], end=rg.params['end'], duration=rg.params['duration'], interval=rg.params['release_interval'], caller=rg)

        if len(si.roles.release_groups) == 0:
            # guard against there being no release groups
            si.msg_logger.msg('No valid release groups' , fatal_error=True, exit_now=True, caller=self)



        si.msg_logger.progress_marker('Set up run start and end times, plus release groups and their schedulers', start_time=t0)

    def _setup_fields(self):
        # initialise all classes, order is important!
        # shortcuts
        t0 = perf_counter()

        # start with setting up field gropus, which set up readers
        # as it has info on whether 2D or 3D which  changes class options'
        # reader prams should be full and complete from oceanTrackerRunner, so dont initialize
        # chose fiel manager for normal or nested readers
        if len(si.working_params['roles_dict']['nested_readers']) > 0:
            # use development nested readers class
            si.working_params['core_roles']['field_group_manager'].update(dict(class_name='oceantracker.field_group_manager.dev_nested_fields.DevNestedFields'))

        # set up feilds
        fgm = si.add_core_role('field_group_manager', si.working_params['core_roles']['field_group_manager'], crumbs=f'adding core class "field_group_manager" ')
        fgm.initial_setup()  # needed here to add reader fields inside reader build
        si.run_info.is3D_run = fgm.info['is3D']

        fgm.setup_dispersion_and_resuspension_fields()  # setup fields required for dispersion based on  what variables are in the hydro-files
        fgm.final_setup()

        si.hindcast_info = fgm.get_hindcast_info()
        si.msg_logger.progress_marker('Setup field group manager', start_time=t0)



    def _finalize_classes(self):
        # finalise the classeds
        #todo , more needed here to finalise othe classes?
        t0 = perf_counter()
        ri = si.run_info
        # do final setp which may depend on settings from intitial st up

        # order matters, must do interpolator after particle_group_manager, to get stucted arrays and solver last
        si.core_roles.particle_group_manager.final_setup()
        si.core_roles.solver.final_setup()
        if si.settings.write_tracks:
            si.core_roles.tracks_writer.final_setup()

        si.msg_logger.progress_marker('final set up of core classes', start_time=t0)

    def _make_and_initialize_user_classes(self):
        # complete build of particle by adding reade, custom properties and modifiers

        pgm = si.core_roles.particle_group_manager



        # any custom particle properties added by user
        for name, p in si.working_params['roles_dict']['particle_properties'].items():
            pgm.add_particle_property(name, 'user',p)


        # build and initialise other user classes, which may depend on custom particle props above or reader field, not sure if order matters
        for user_type in ['velocity_modifiers','trajectory_modifiers',
                             'particle_statistics', 'particle_concentrations', 'event_loggers']:
            for name, params in si.working_params['roles_dict'][user_type].items():
                i = si.add_user_class(user_type,name, params,class_type= 'user',   crumbs=' making class type ' + user_type + ' ')
                i.initial_setup()  # some require instanceID from above add class to initialise


        pass


    # ____________________________
    # internal methods below
    # ____________________________
    def _get_case_info(self, d0, t0):
        pgm= si.core_roles.particle_group_manager
        info = self.info
        elapsed_time_sec = perf_counter() -t0
        info.update(dict(started=str(d0), ended=str(datetime.now()),
                         duration=str(datetime.now() - d0),
                         elapsed_time_sec=elapsed_time_sec,
                         number_particles_released= pgm.info['particles_released']))
        info.update(si.run_info.as_dict())
        # base class variable warnings is common with all descendents of parameter_base_class
        d = {'caseID' : si.run_info.caseID,
             'user_note': si.settings['user_note'],
             'file_written': datetime.now().isoformat(),
             'output_files': si.output_files,
             'version_info':   si.run_builder['version'],
             'computer_info': get_versions_computer_info.get_computer_info(),
             'hindcast_info': si.hindcast_info,
             'timing':dict(block_timings=[], function_timers= {}),
             'update_timers': {},
             'settings' : si.settings.as_dict(),
             'run_info' : info,
             'particle_status_flags': si.particle_status_flags.as_dict(),
             'errors': si.msg_logger.errors_list,
             'warnings': si.msg_logger.warnings_list,
             'notes': si.msg_logger.notes_list,
             'release_group_info': {},
             'scheduler_info': {},
             'class_roles_info': {},
             }

        # sweep up any output files from al used classes
        class_info={}
        for key, i in si.roles.as_dict().items():
            if i is None : continue
            class_info[key] = {}
            d['scheduler_info'][key] = {}
            d['update_timers'][key] = {}
            d['output_files'][key] = {}
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

        d['release_group_info'] = class_info['release_groups']

        # core roles
        for key, i in si.core_roles.as_dict().items():
            if i is None: continue
            class_info[key] = {}
            class_info[key] = i.info
            d['output_files'][key] = i.info['output_file'] if 'output_file' in i.info else None
            d['update_timers'][key] = dict(time_spent_updating= i.info['time_spent_updating'],
                                                 update_calls= i.info['update_calls'],
                                                 time_first_update_call= i.info['time_first_update_call'] )
            if hasattr(i, 'scheduler_info'):
                d['scheduler_info'][key]= i.scheduler_info

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
            from numba.core import config
            d['numba_code_info'] = dict(signatures={},SMID_code = {},
                                        config={key:val for key, val in config.__dict__.items()
                                                    if not key.startswith('_') and type(val) in [None,int,str,float]
                                                }
                                        )
            for name, func in  numba_util.numba_func_info.items():
                if hasattr(func,'signatures') : # only code that has been compiled has a sig
                    sig = func.signatures
                    d['numba_code_info']['signatures'][name] = str(sig)
                    d['numba_code_info']['SMID_code'][name] = []
                    for nsig in range(len(sig)):
                        d['numba_code_info']['SMID_code'][name].append(numba_util.count_simd_intructions(func, sig=nsig))
                    pass
        return d

    def close(self):
        pass

