from copy import deepcopy
from os import path, environ, remove
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_util import  make_class_instance_from_params
from oceantracker.util.profiling_util import function_profiler
from time import  perf_counter
from oceantracker.util.messgage_logger import MessageLogger, GracefulError
from oceantracker.util import profiling_util, get_versions_computer_info
import numpy as np
from oceantracker.util import time_util
from numba import set_num_threads
from oceantracker.util import json_util
from datetime import datetime
from time import sleep
import traceback
from oceantracker.util.parameter_checking import merge_params_with_defaults
from oceantracker import common_info_default_param_dict_templates as common_info
from oceantracker.util.numba_util import seed_numba_random

class OceanTrackerCaseRunner(ParameterBaseClass):
    # this class runs a single case
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required


    def run_case(self, working_params):
        si=self.shared_info
        si.reset()  # clear out classes from class instance of SharedInfo if running series of mains
        d0 = datetime.now()
        t0 = perf_counter()


        # basic param shortcuts
        si.working_params = working_params

        # merge shared and case setting ito one shared variable as distinction no longer important
        si.settings = si.working_params['shared_settings']
        si.settings.update(si.working_params['case_settings'])

        si.output_files = si.working_params['output_files']
        si.run_output_dir = si.output_files['run_output_dir']
        si.output_file_base = si.output_files['output_file_base']
        si.caseID = working_params['caseID']

        # set up message logging
        output_files = working_params['output_files']
        si.msg_logger = MessageLogger(f'C{si.caseID:03d}', si.settings['max_warnings'])
        output_files['case_log_file'], output_files['case_error_file'] = \
        si.msg_logger.set_up_files(output_files['run_output_dir'], output_files['output_file_base'] + '_caseLog')

        # other useful shared values
        si.backtracking = si.settings['backtracking']
        si.model_direction = -1 if si.backtracking else 1

        si.write_output_files = si.settings['write_output_files']
        si.write_tracks = si.settings['write_tracks']

        si.z0 = si.settings['z0']
        si.minimum_total_water_depth = si.settings['minimum_total_water_depth']
        si.computer_info = get_versions_computer_info.get_computer_info()



        #set_num_threads(max(1, si.settings['max_threads']))
        #set_num_threads(5)

        # set up profiling
        profiling_util.set_profile_mode(si.settings['profiler'])

        case_info_file = None
        case_exception = None
        return_msgs = {'errors': si.msg_logger.errors_list, 'warnings': si.msg_logger.warnings_list, 'notes': si.msg_logger.notes_list}
        # case set up
        try:
            self._set_up_run()
            self._do_pre_processing()
            self._make_core_classes_and_release_groups()
            self._make_and_initialize_user_classes()
            # below are not done in _initialize_solver_core_classes_and_release_groups as it may depend on user classes to work




        except GracefulError as e:
            si.msg_logger.show_all_warnings_and_errors()
            si.msg_logger.write_error_log_file(e)
            si.msg_logger.msg(f' Case Funner graceful exit from case number [{si.caseID:2}]', hint ='Parameters/setup has errors, see above', fatal_error= True)

            if si.settings['debug']:
                si.msg_logger.write_error_log_file(e)
                si.msg_logger.write_error_log_file(traceback.print_exc())

            si.msg_logger.close()
            return None, return_msgs

        except Exception as e:
            si.msg_logger.show_all_warnings_and_errors()
            si.msg_logger.write_error_log_file(e)
            si.msg_logger.write_error_log_file(traceback.print_exc())
            si.msg_logger.msg(f' Unexpected error in case number [{si.caseID:2}] ', fatal_error=True,hint='check above or .err file')
            si.msg_logger.close()
            return  None, return_msgs


        # check particle properties have other particle properties, fields and other compatibles they require
        self._do_run_integrity_checks()


        try:
            self._do_a_run()
            case_info = self._get_case_info(d0,t0)

            if si.settings['write_output_files']:
                # write grid if first case
                if si.caseID == 0:
                    si.classes['field_group_manager'].write_hydro_model_grids()

                case_info_file = si.output_file_base + '_caseInfo.json'
                json_util.write_JSON(path.join(si.run_output_dir, case_info_file), case_info)

        except GracefulError as e:
            si.msg_logger.show_all_warnings_and_errors()
            si.msg_logger.write_error_log_file(e)

            si.msg_logger.msg(f' Case Funner graceful exit from case number [{si.caseID:2}]', hint ='Parameters/setup has errors, see above', fatal_error= True)

            if si.settings['debug']:
                si.msg_logger.write_error_log_file(e)
                si.msg_logger.write_error_log_file(traceback.print_exc())
            si.msg_logger.close()
            return None, return_msgs

        except Exception as e:
            si.msg_logger.show_all_warnings_and_errors()
            si.msg_logger.write_error_log_file(e)
            si.msg_logger.write_error_log_file(traceback.print_exc())
            si.msg_logger.msg(f' Unexpected error in case number [{si.caseID:2}] ', fatal_error=True,hint='check above or .err file')
            si.msg_logger.close()
            return  None, return_msgs

        # reshow warnings
        si.msg_logger.show_all_warnings_and_errors()
        self.close()  # close al classes

        si.msg_logger.print_line()
        si.msg_logger.progress_marker('Finished case number %3.0f, ' % si.caseID + ' '
                                      + si.output_files['output_file_base']
                                      + ' started: ' + str(d0)
                                      + ', ended: ' + str(datetime.now()))
        si.msg_logger.msg('Elapsed time =' + str(datetime.now() - d0), tabs=3)
        si.msg_logger.print_line()

        si.msg_logger.close()
        case_info_file = path.join(si.run_output_dir,case_info_file)
        return case_info_file,  return_msgs

    def _set_up_run(self):
        # builds shared_info class variable with data and classes initialized  ready for run
        # from single run case_runner_params
        si =self.shared_info

        si.msg_logger.print_line()
        si.msg_logger.msg('Starting case number %3.0f, ' % si.caseID + ' '
                                      + si.output_files['output_file_base']
                                      + ' at ' + time_util.iso8601_str(datetime.now()))
        si.msg_logger.print_line()

        if si.settings['use_random_seed']:
            np.random.seed(0) # set numpy
            seed_numba_random(0)
            si.msg_logger.msg('Using numpy.random.seed(0), makes results reproducible (only use for testing developments give the same results!)',warning=True)

        # get short class names map
        # delay  start, which may avoid occasional lockup at start if many cases try to read same hindcast file at same time
        if si.settings['multiprocessing_case_start_delay'] is not None:
            delay = si.settings['multiprocessing_case_start_delay'] * (si.caseID % si.settings['processors'])
            si.msg_logger.progress_marker('Delaying start by  ' + str(delay) + ' sec')
            sleep(delay)
            si.msg_logger.progress_marker('Starting after delay  of ' + str(delay) + ' sec')

        # not sure if buffer is to small, but make bigger to 512 as default,  Numba default is  128, may slow code due to recompilations from too small buffer??
        environ['numba_function_cache_size'] = str(si.settings['numba_function_cache_size'])

        if si.settings['debug']:
            # makes it easier to debug, particularly  in pycharm
            environ['NUMBA_BOUNDSCHECK'] = '1'
            environ['NUMBA_FULL_TRACEBACKS'] = '1'
            si.msg_logger.msg('Running in debug mode',note=True)

    #@function_profiler(__name__)
    def _do_a_run(self):
        # build and run solver from parameter dictionary
        # run from a given dictionary to enable particle tracking on demand from JSON type parameter set
        # also used for parallel  version
        si = self.shared_info

        info= self.info
        info['model_run_started'] = datetime.now()

        solver = si.classes['solver']
        p, reader, f = si.classes['particle_group_manager'], si.classes['reader'], si.classes['field_group_manager']  # for later use

        # fill and process buffer until there is less than 2 steps
        si.msg_logger.print_line()
        si.msg_logger.progress_marker('Starting ' + si.output_file_base + ',  duration: ' + time_util.seconds_to_pretty_duration_string(si.run_info['model_duration']))

        t0 = perf_counter()
        si.msg_logger.progress_marker('Initialized Solver Class', start_time=t0)

        # ------------------------------------------
        solver.solve()
        # ------------------------------------------

    def _do_run_integrity_checks(self):
        si=self.shared_info
        grid = si.classes['reader'].grid

        # check all have required, fields, part props and grid data
        for i in si.all_class_instance_pointers_iterator():
            i.check_requirements()

        # other checks and warnings
        #todo move to set up fields
        if si.settings['open_boundary_type'] > 0:
            if not np.any(grid['node_type'] == 3):
                si.msg_logger.msg('Open boundary requested, but no open boundary node data available, boundaries will be closed,',
                                        hint='For Schism open boundaries requires hgrid file to named in reader params',warning=True)
        else:
            si.msg_logger.msg('No open boundaries requested, as run_params["open_boundary_type"] = 0',note=True,
                                      hint='Requires list of open boundary nodes not in hydro model, eg for Schism this can be read from hgrid file to named in reader params and run_params["open_boundary_type"] = 1')

        si.msg_logger.exit_if_prior_errors()



    def _do_pre_processing(self):
        # do pre-processing, eg read polygons from files
        si = self.shared_info

        case_params = si.working_params
        for name, params in case_params['role_dicts']['pre_processing'].items():
            i = si.create_class_dict_instance(name, 'pre_processing', 'user', params, crumbs='Adding "fields" from user params')
            i.initial_setup()

    def _setup_particle_release_groups(self, particle_release_groups_params_dict):
        # particle_release groups setup and instances,
        # find extremes of  particle existence to calculate model start time and duration
        #todo move to particle group manager and run in main at set up to get reader range etc , better for shared reader development
        si = self.shared_info

        # set up to start end times based on release_groups
        # find earliest and last release times+life_duration ( if going forwards)

        first_release_time = []
        last_time_alive = []

        for name, pg_params in particle_release_groups_params_dict.items():
            # make instance
            if 'class_name' not in pg_params: pg_params['class_name'] = 'oceantracker.release_groups.point_release.PointRelease'

            # make instance and initialise

            i = si.create_class_dict_instance(name, 'release_groups', 'user', pg_params, crumbs='Adding release groups')
            i.initial_setup()

            # set up release times so duration of run known
            i.set_up_release_times()
            release_info = i.info['release_info']

            if release_info['release_times'].size == 0:
                si.msg_logger.msg(f'Release group= {name} no release times in range of hindcast and given release duration', warning=True,crumbs='Setting up release groups')
                continue
            else:
                first_release_time.append(release_info['first_release_time'])
                last_time_alive.append(release_info['last_time_alive'])

        si.msg_logger.exit_if_prior_errors('Errors in release groups')

        if len(si.classes['release_groups']) == 0:
            # guard against there being no release groups
            si.msg_logger.msg('No valid release groups, exiting' , fatal_error=True, exit_now=True)

        # find first release, and last ime alive
        t_first = np.min(np.asarray(first_release_time)*si.model_direction)*si.model_direction
        t_last = np.max(np.asarray(last_time_alive) * si.model_direction) * si.model_direction

        # time range in forwards order
        return t_first,t_last

    def _make_core_class_instances(self):
        # params are full merged by oceantracker main and instance making tested, so m=no parm merge needed
        si = self.shared_info
        case_params= si.working_params

        # make core classes, eg. field group

        for name, params in case_params['core_roles'].items():
            if name in ['reader',  'resuspension']: continue
            i = si.add_core_class(name, params, crumbs= f'core class "{name}" ')

        si.particle_status_flags= si.classes['particle_group_manager'].status_flags

    def _make_core_classes_and_release_groups(self):
        # initialise all classes, order is important!
        # shortcuts
        t0 = perf_counter()
        si = self.shared_info
        si.particle_status_flags = common_info.particle_info['status_flags']

        si.run_info = {}


        # start with setting up field gropus, which set up readers
        # as it has info on whether 2D or 3D which  changes class options'
        # reader prams should be full and complete from oceanTrackerRunner, so dont initialize
        # chose fiel manager for normal or nested readers
        if len(si.working_params['role_dicts']['nested_readers']) > 0:
            # use devopment nested readers class
            si.working_params['core_roles']['field_group_manager'].update(dict(class_name='oceantracker.field_group_manager.dev_nested_fields.DevNestedFields'))

        # set up feilds
        fgm = si.add_core_class('field_group_manager', si.working_params['core_roles']['field_group_manager'], crumbs=f'adding core class "field_group_manager" ')
        fgm.initial_setup()  # needed here to add reader fields inside reader build

        dispersion_params = si.working_params['core_roles']['dispersion']
        if  si.is3D_run:
            if si.settings['use_A_Z_profile'] and fgm.info['has_A_Z_profile']:
               # use profile of AZ

               dispersion_params['class_name'] ='oceantracker.dispersion.random_walk_varyingAz.RandomWalkVaryingAZ'

            # resuspension only in 3D
            si.add_core_class('resuspension', si.working_params['core_roles']['resuspension'], initialise=True)

        # alawys add dispersion
        si.add_core_class('dispersion', dispersion_params, initialise=True)
       

        if si.write_tracks:
            si.add_core_class('tracks_writer',si.working_params['core_roles']['tracks_writer'], initialise=True)
        else:
            si.classes['tracks_writer'] = None

        pgm = si.add_core_class('particle_group_manager', si.working_params['core_roles']['particle_group_manager'], crumbs=f'adding core class "particle_group_manager" ')
        pgm.initial_setup()  # needed here to add reader fields inside reader build

        fgm.final_setup()  # set up particle properties associated with fields

        # make other core classes, eg.
        core_role_params=si.working_params['core_roles']
        for name in ['solver']:
            si.add_core_class(name, core_role_params[name], crumbs=f'core class "{name}" ')


        if si.is3D_run:
            si.add_core_class('resuspension', core_role_params['resuspension'], crumbs= 'core class "resuspension" ')


        if  si.settings['time_step'] > fgm.get_hydo_model_time_step():
            si.msg_logger.msg(f'Results may not be accurate as, time step param={si.settings["time_step"]:2.0f} sec,  > hydo model time step = {fgm.get_hydo_model_time_step():2.0f}',
                              warning=True)

        # set up start time and duration based on particle releases
        t0 = perf_counter()
        time_start, time_end = self._setup_particle_release_groups(si.working_params['role_dicts']['release_groups'])


        #clip times to maximum duration in shared and case params
        duration = abs(time_end - time_start)
        duration = min(duration, si.settings['max_run_duration'])
        time_end = time_start + duration* si.model_direction

        # note results
        si.run_info['model_start_time'] = time_start
        si.run_info['model_end_time'] = time_end
        si.run_info['model_duration'] = max(abs(time_end - time_start), si.settings['time_step']) # at least one time step

        si.msg_logger.progress_marker('set up release_groups', start_time=t0)

        # useful info
        si.run_info['model_start_date'] = time_util.seconds_to_datetime64(time_start)
        si.run_info['model_end_date'] = time_util.seconds_to_datetime64(time_end)
        si.run_info['model_timedelta'] =time_util.seconds_to_pretty_duration_string(si.settings['time_step'])
        si.run_info['model_duration_timedelta'] = time_util.seconds_to_pretty_duration_string(si.run_info['model_duration'] )

        # value time to forced timed events to happen first time accounting for backtracking, eg if doing particle stats, every 3 hours
        si.time_of_nominal_first_occurrence = -si.model_direction * 1.0E36
        # todo get rid of time_of_nominal_first_occurrence



        # initialize the rest of the core classes
        #todo below apply to all core classes, reader
        #todo alternative can they be intitlised on creation here?
        t0 = perf_counter()
        for name in ['interpolator', 'solver'] : # order may matter?
            si.classes[name].initial_setup()
        si.msg_logger.progress_marker('initial set up of core classes', start_time=t0)

        # do final setp which may depend on settingd from intitial st up
        t0= perf_counter()
        # order matters, must do interpolator after particle_group_manager, to get stucted arrays and solver last
        for name in ['particle_group_manager', 'interpolator', 'solver'] :
            si.classes[name].final_setup()
        si.msg_logger.progress_marker('final set up of core classes',start_time=t0)

    def _make_and_initialize_user_classes(self):
        # complete build of particle by adding reade, custom properties and modifiers
        si= self.shared_info

        pgm = si.classes['particle_group_manager']

        # create prop particle properties derived from any field  reader ot user custom
        t0= perf_counter()
        for name, i in si.classes['fields'].items():
            pgm.add_particle_property(name, 'from_fields', dict( vector_dim=i.get_number_components(), time_varying=True,
                                                    write= True if i.params['write_interp_particle_prop_to_tracks_file'] else False))


        si.msg_logger.progress_marker('created particle properties for custom fields and derived from fields ', start_time=t0)

        # any custom particle properties added by user
        for name, p in si.working_params['role_dicts']['particle_properties'].items():
            pgm.add_particle_property(name, 'user',p)

        # add default classes, eg tidal stranding
        #todo this may be better else where
        if 'dry_cell_index' in si.classes['reader'].grid and 'tidal_stranding' not in  si.working_params['role_dicts']['status_modifiers']:
            si.working_params['role_dicts']['status_modifiers']['tidal_stranding'] ={'class_name': 'oceantracker.status_modifiers.tidal_stranding.TidalStranding'}

        # build and initialise other user classes, which may depend on custom particle props above or reader field, not sure if order matters
        for user_type in ['velocity_modifiers','trajectory_modifiers','status_modifiers',
                             'particle_statistics', 'particle_concentrations', 'event_loggers']:
            for name, params in si.working_params['role_dicts'][user_type].items():
                i = si.create_class_dict_instance(name,user_type, 'user', params, crumbs=' making class type ' + user_type + ' ')
                i.initial_setup()  # some require instanceID from above add class to initialise
        pass

    # ____________________________
    # internal methods below
    # ____________________________
    def _get_case_info(self, d0, t0):
        si = self.shared_info
        pgm= si.classes['particle_group_manager']
        info = self.info
        info['date_of_time_zero'] = time_util.seconds_to_datetime64(np.asarray([0.]))
        r = si.classes['reader']

        info['backtracking'] = si.backtracking
        elapsed_time_sec = perf_counter() -t0
        info.update(dict(started=str(d0), ended=str(datetime.now()),
                         duration=str(datetime.now() - d0),
                         elapsed_time_sec=elapsed_time_sec,
                         number_particles_released= pgm.info['particles_released']))
        info.update(si.run_info)
        # base class variable warnings is common with all descendents of parameter_base_class
        d = {'user_note': si.settings['user_note'],
             'output_files': si.output_files,
             'caseID' : si.caseID,
             'block_timings': [],
             'version_info': get_versions_computer_info.get_code_version(),
            'computer_info': get_versions_computer_info.get_computer_info(),
            'file_written': datetime.now().isoformat(),
             'run_info' : info,
             'hindcast_info': r.info,
             'full_case_params': si.working_params,
             'particle_status_flags': si.particle_status_flags,
             'release_groups' : {},
             'particle_release_group_user_maps': si.classes['particle_group_manager'].get_release_group_userIDmaps(),
             'errors': si.msg_logger.errors_list,
             'warnings': si.msg_logger.warnings_list,
             'notes': si.msg_logger.notes_list,
             'function_timers': {},
             'class_roles_info': {}, }

        for key, i in si.classes.items():
            if i is None : continue

            if type(i) == dict:
                d['class_roles_info'][key] = {}
                d['output_files'][key] = {}
                # interate over dict
                for key2, i2 in i.items():
                    d['class_roles_info'][key][key2]= i2.info
                    d['output_files'][key][key2]= i2.info['output_file'] if 'output_file' in i2.info else None

            else:
                d['class_roles_info'][key] = i.info
                d['output_files'][key] = i.info['output_file'] if 'output_file' in i.info else None

        # add basic release group info
        for key, item in si.classes['release_groups'].items():
            rginfo={'points': item.params['points'],
                    'is_polygon': hasattr(item,'polygon')}
            d['release_groups'][key]= rginfo

        # sort function times into order
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
        return d

    def close(self):
        # close all instances, eg their files if not close etc
        si=self.shared_info
        ml = si.msg_logger

        for i in si.all_class_instance_pointers_iterator():
            try:
                i.close()

            except Exception as e:

                ml.msg(f'Unexpected error closing class ="{ i.info["name"]}"', fatal_error= True, exception=e)
