import os
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
from oceantracker import definitions as common_info


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
        si.working_params = run_builder['working_params']

        # setup shared info and message logger
        si._setup() # clear out classes from class instance of SharedInfo if running series of mains
        si.msg_logger.set_screen_tag(f'C{run_builder["caseID"]:03d}')
        si.msg_logger.settings(max_warnings=si.settings.max_warnings)
        ml = si.msg_logger # shortcut for logger


        # merge settings with defaults
        si.working_params['settings'] = setup_util.merge_settings(si.working_params['settings'], si.default_settings, si.settings.possible_values(),
                                                               ml, crumbs= crumbs +'> case settings', caller=self)
        ml.exit_if_prior_errors('Errors in settings??', caller=self)
        # transfer all settings to shared_info.settings to allow tab hints
        ri = si.run_info
        for key in si.settings.possible_values():
            setattr(si.settings, key, si.working_params['settings'][key])


        # set numba config environment variables, before any import of numba, eg by readers,
        # also done in main but also needed here for parallel runs
        config_numba_environment_and_random_seed(si.working_params['settings'], si.msg_logger, crumbs='Starting case_runner', caller=self)  # must be done before any numba imports

        # basic  shortcuts
        si.run_builder = run_builder
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
                    si.msg_logger.set_up_files(output_files['run_output_dir'], output_files['output_file_base'] + '_caseLog')

        si.msg_logger.print_line()
        si.msg_logger.msg('Starting case number %3.0f, ' % ri.caseID + ' '
                                      + ri.output_file_base
                                      + ' at ' + time_util.iso8601_str(datetime.now()))
        si.msg_logger.print_line()

        # delay  start, which may avoid occasional lockup at start if many cases try to read same hindcast file at same time
        if si.settings['multiprocessing_case_start_delay'] is not None:
            delay = si.settings['multiprocessing_case_start_delay'] * (si.run_info.caseID % si.settings['processors'])
            si.msg_logger.progress_marker('Delaying start by  ' + str(delay) + ' sec')
            sleep(delay)
            si.msg_logger.progress_marker('Starting after delay  of ' + str(delay) + ' sec')


        t0=perf_counter()
        si.msg_logger.progress_marker('Scanned OceanTracker to build short name map to the full class_names', start_time=t0)

        # set up profiling
        #profiling_util.set_profile_mode(si.settings['profiler'])

        case_info_file = None
        return_msgs = {'errors': si.msg_logger.errors_list, 'warnings': si.msg_logger.warnings_list, 'notes': si.msg_logger.notes_list}

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

            self._make_core_classes()

            # add any integrated model, to get params changes, but don't initialise
            # there can only be one model added

            #todo remerge/check settings changed by model here?

            # now  params commlet cabn set up

            # set up start time and duration based on particle releases
            self._setup_particle_release_groups_and_start_end_times(si.working_params['roles_dict']['release_groups'])

            self._make_and_initialize_user_classes()
            self._finalize_classes()  # any setup actions that mus be done after other actions, eg shedulers

            # model may depend on ther classes, so intilialise after all other claases are setup
            if si.core_roles.integrated_model is not None:
                im.initial_setup()
                im.final_setup()

        except GracefulError as e:
            si.msg_logger.show_all_warnings_and_errors()
            si.msg_logger.write_error_log_file(e)
            si.msg_logger.msg(f' Case Funner graceful exit from case number [{ri.caseID:2}]', hint ='Parameters/setup has errors, see above', fatal_error= True)

            if si.settings['debug']:
                si.msg_logger.write_error_log_file(e)
                si.msg_logger.write_error_log_file(traceback.print_exc())

            si.msg_logger.close()
            return None, return_msgs

        except Exception as e:
            si.msg_logger.show_all_warnings_and_errors()
            si.msg_logger.write_error_log_file(e)
            si.msg_logger.write_error_log_file(traceback.print_exc())
            si.msg_logger.msg(f' Unexpected error in case number [{ri.caseID:2}] ', fatal_error=True,hint='check above or .err file')
            si.msg_logger.close()
            return  None, return_msgs


        # check particle properties have other particle properties, fields and other compatibles they require
        self._do_run_integrity_checks()


        try:
            self._do_a_run()


            case_info = self._get_case_info(d0,t_start)


            # write grid if first case
            if ri.caseID == 0:
                si.core_roles.field_group_manager.write_hydro_model_grid()
            case_info_file = ri.output_file_base + '_caseInfo.json'
            json_util.write_JSON(path.join(ri.run_output_dir, case_info_file), case_info)

        except GracefulError as e:
            si.msg_logger.show_all_warnings_and_errors()
            si.msg_logger.write_error_log_file(e)

            si.msg_logger.msg(f' Case Funner graceful exit from case number [{ri.caseID:2}]', hint ='Parameters/setup has errors, see above', fatal_error= True)

            if si.settings['debug']:
                si.msg_logger.write_error_log_file(e)
                si.msg_logger.write_error_log_file(traceback.print_exc())
            si.msg_logger.close()
            return None, return_msgs

        except Exception as e:
            si.msg_logger.show_all_warnings_and_errors()
            si.msg_logger.write_error_log_file(e)
            si.msg_logger.write_error_log_file(traceback.print_exc())
            si.msg_logger.msg(f' Unexpected error in case number [{ri.caseID:2}] ', fatal_error=True,hint='check above or .err file')
            si.msg_logger.close()
            return  None, return_msgs

        # reshow warnings
        si.msg_logger.show_all_warnings_and_errors()

        si.msg_logger.print_line()
        si.msg_logger.progress_marker('Finished case number %3.0f, ' % ri.caseID + ' '
                                      + si.run_info.output_file_base
                                      + ' started: ' + str(d0)
                                      + ', ended: ' + str(datetime.now()))
        si.msg_logger.msg('Computational time =' + str(datetime.now() - d0), tabs=3)
        si.msg_logger.print_line()

        self.close()  # close al classes and msg logger
        si.msg_logger.close()
        case_info_file = path.join(ri.run_output_dir,case_info_file)
        return case_info_file,  return_msgs




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

    def dev_setup_dispersion_and_resuspension(self):
        # these depend on which variables are available inb the hydro file
        fgm = si.core_roles.field_group_manager
        fmap = reader.params['field_variable_map']
        info = self.info

        nc = reader.open_first_file()

        # set up dispersion using vertical profiles of A_Z if available
        self._setup_dispersion_params(nc)
        si.add_core_role('dispersion', si.working_params['core_roles']['dispersion'],
                         default_classID='dispersion_random_walk', initialise=True)

        # add resuspension based on friction velocity
        if info['is3D']:
            # add friction velocity from bottom stress or near seabed vel
            self._setup_resupension_params(nc)
            si.add_core_role('resuspension', si.working_params['core_roles']['resuspension'],
                             default_classID='resuspension_basic', initialise=True)

        nc.close()

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
        ri.end_time = ri.times[-1] # adjust end to nearest time step

        # setup scheduler for each release group, how start and model times known
        #   this will round start times and release interval to be integer number of model time steps after the start
        for name, rg in si.roles.release_groups.items():
            si.add_scheduler_to_class('release_scheduler', rg, start=rg.params['start'], end=rg.params['end'], duration=rg.params['duration'], interval=rg.params['release_interval'], caller=rg)

        if len(si.roles.release_groups) == 0:
            # guard against there being no release groups
            si.msg_logger.msg('No valid release groups' , fatal_error=True, exit_now=True, caller=self)

        # useful information
        ri.duration = abs(ri.times[-1] - ri.times[0])
        ri.start_date = time_util.seconds_to_isostr(ri.times[0])
        ri.end_date = time_util.seconds_to_isostr(ri.times[-1])
        ri.dates = time_util.seconds_to_isostr(ri.times)

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
            # use devopment nested readers class
            si.working_params['core_roles']['field_group_manager'].update(dict(class_name='oceantracker.field_group_manager.dev_nested_fields.DevNestedFields'))

        # set up feilds
        fgm = si.add_core_role('field_group_manager', si.working_params['core_roles']['field_group_manager'], crumbs=f'adding core class "field_group_manager" ')
        fgm.initial_setup()  # needed here to add reader fields inside reader build
        si.run_info.is3D_run = fgm.info['is3D']

        fgm.setup_dispersion_and_resuspension()  # setup files required for didpersion etc, depends on what variables are in the hydro-files
        fgm.final_setup()

        si.hindcast_info = fgm.get_hydro_model_info()
        si.msg_logger.progress_marker('Setup field group manager', start_time=t0)


    def _make_core_classes(self):
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
        core_role_params = si.working_params['core_roles']

        # make other core classes
        si.add_core_role('solver', core_role_params['solver'], crumbs='core class solver ')


        if  si.settings.time_step >  si.hindcast_info['time_step']:
            si.msg_logger.msg(f'Results may not be accurate as, time step param={si.settings.time_step:2.0f} sec,  > hydo model time step = {si.hindcast_info["time_step"]:2.0f}',
                              warning=True)

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
        d = {'user_note': si.settings['user_note'],
             'output_files': si.output_files,
             'version_info': get_versions_computer_info.get_code_version(),
             'computer_info': get_versions_computer_info.get_computer_info(),
             'hindcast_info': si.hindcast_info,
             'caseID' : si.run_info.caseID,
             'block_timings': [],
            'file_written': datetime.now().isoformat(),
             'settings' : si.settings.as_dict(),
             'run_info' : info,
             'particle_status_flags': si.particle_status_flags.as_dict(),
             'errors': si.msg_logger.errors_list,
             'warnings': si.msg_logger.warnings_list,
             'notes': si.msg_logger.notes_list,
             'function_timers': {},
             'class_roles_info': {}, }

        # sweep up any output files from al used classes
        for key, i in si.roles.as_dict().items():
            if i is None : continue

            d['class_roles_info'][key] = {}
            d['output_files'][key] = {}
            # interate over dict
            for key2, i2 in i.items():
                d['class_roles_info'][key][key2]= i2.info
                d['output_files'][key][key2]= i2.info['output_file'] if 'output_file' in i2.info else None
                if hasattr(i2,'scheduler_info'):
                    d['class_roles_info'][key][key2]['scheduler_info'] = i2.scheduler_info

        # core roles
        for key, i in si.core_roles.as_dict().items():
            if i is None: continue
            d['class_roles_info'][key] = i.info
            d['output_files'][key] = i.info['output_file'] if 'output_file' in i.info else None
            if hasattr(i, 'scheduler_info'):
                d['class_roles_info'][key]['scheduler_info'] = i.scheduler_info

        keys= []
        times=[]
        for key, f in profiling_util.func_timings.items():
            times.append(f['time'])
            keys.append(key)
            f['msec_per_call'] = 1000*f['time']/f['calls']
            f['% of total time'] = 100*f['time']/elapsed_time_sec

        # add in reverse timing order
        for n in np.argsort(np.asarray(times))[::-1]:
            d['function_timers'][keys[n]]= profiling_util.func_timings[keys[n]]

        # block timings in time order
        b = si.block_timers
        times = np.asarray( [item['time'] for key, item in b.items()])
        order = np.argsort(times)[::-1]
        for key in [list(b.keys())[i] for i in order]:
            l = f' {100*b[key]["time"]/elapsed_time_sec:5.1f}% {key} : calls {b[key]["calls"]:4d}, {time_util.seconds_to_pretty_duration_string(b[key]["time"])}'
            d['block_timings'].append(l)
        d['block_timings'].append(f'--- Total time {time_util.seconds_to_pretty_duration_string(elapsed_time_sec)}')


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
        # close all instances, eg their files if not close etc



        for i in si._all_class_instance_pointers_iterator():
            try:
                i.close()

            except Exception as e:
                si.msg_logger.msg(f'Unexpected error closing class ="{ i.info["name"]}"', fatal_error= True, exception=e)


