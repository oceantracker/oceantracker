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

class OceanTrackerCaseRunner(ParameterBaseClass):
    # this class runs a single case
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required


    def run(self, working_params):
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
        si.processorID = working_params['processorID']

        # set up message logging
        output_files = working_params['output_files']
        si.msg_logger = MessageLogger('P%03.0f:' % si.processorID, si.settings['advanced_settings']['max_warnings'])
        output_files['case_log_file'], output_files['case_error_file'] = \
        si.msg_logger.set_up_files(output_files['run_output_dir'], output_files['output_file_base'] + '_caseLog')


        # other useful shared values
        si.backtracking = si.settings['backtracking']
        si.model_direction = -1 if si.backtracking else 1
        si.is_3D_run = working_params['hindcast_is3D'] and not si.settings['run_as_depth_averaged']

        si.write_output_files = si.settings['write_output_files']
        si.write_tracks = si.settings['write_tracks']
        si.retain_culled_part_locations = si.settings['retain_culled_part_locations']

        si.z0 = si.settings['z0']
        si.minimum_total_water_depth = si.settings['minimum_total_water_depth']
        si.computer_info = get_versions_computer_info.get_computer_info()

        # set processors for threading, ie numba/parallel prange loops
        #if si.settings['max_threads'] is None:
         #   si.settings['max_threads']= si.computer_info['CPUs_hardware'] - 2

        #set_num_threads(max(1, si.settings['max_threads']))

        # set up profiling
        profiling_util.set_profile_mode(si.settings['advanced_settings']['profiler'])

        case_info_file = None
        case_exception = None
        # case set up
        #try:
        self._set_up_run()
        self._make_core_class_instances()
        si.solver_info = si.classes['solver'].info  # todo is this needed?? allows shortcut access from other classes
        self._initialize_solver_core_classes_and_release_groups()


        self._make_and_initialize_user_classes()

        # below are not done in _initialize_solver_core_classes_and_release_groups as it may depend on user classes to work
        si.classes['dispersion'].initial_setup()
        if si.hydro_model_is3D:
            si.classes['resuspension'].initial_setup()



        # check particle properties have other particle properties, fields and other compatibles they require
        self._do_run_integrity_checks()

       # except GracefulError as e:
       #     si.msg_logger.msg('Case runner graceful exit >>  Parameters/setup has errors, see above', fatal_error= True)
       #     return None, True

      #  except Exception as e:
     #       si.msg_logger.msg('Unexpected error  in case set up',fatal_error=True)
       #     si.msg_logger.write_error_log_file(e)
       #     return None, True

        # try running case
        try:
            self._do_a_run()
            case_info = self._get_case_info(d0,t0)

            if si.settings['write_output_files']:
                # write grid if first case
                if si.processorID == 0:
                    si.classes['field_group_manager'].write_hydro_model_grids()

                case_info_file = si.output_file_base + '_caseInfo.json'
                json_util.write_JSON(path.join(si.run_output_dir, case_info_file), case_info)

        except GracefulError as e:
            si.msg_logger.show_all_warnings_and_errors()
            si.msg_logger.write_error_log_file(e)
            si.msg_logger.msg(f' Case Funner graceful exit from case number [{si.processorID:2}]', hint ='Parameters/setup has errors, see above', fatal_error= True)
            return None, len(si.msg_logger.errors_list), len(si.msg_logger.warnings_list)

        except Exception as e:
            si.msg_logger.show_all_warnings_and_errors()
            si.msg_logger.write_error_log_file(e)
            si.msg_logger.msg(f' Unexpected error in case number [{si.processorID:2}] ', fatal_error=True,hint='check above or .err file')

            return None, len(si.msg_logger.errors_list), len(si.msg_logger.warnings_list)

        # reshow warnings
        si.msg_logger.show_all_warnings_and_errors()
        self.close()  # close al classes

        si.msg_logger.insert_screen_line()
        si.msg_logger.progress_marker('Finished case number %3.0f, ' % si.processorID + ' '
                                      + si.output_files['output_file_base']
                                      + ' started: ' + str(d0)
                                      + ', ended: ' + str(datetime.now()))
        si.msg_logger.msg('Elapsed time =' + str(datetime.now() - d0), tabs=3)
        si.msg_logger.insert_screen_line()


        si.msg_logger.close()
        case_info_file = path.join(si.run_output_dir,case_info_file)
        return case_info_file, len(si.msg_logger.errors_list), len(si.msg_logger.warnings_list)

    def _set_up_run(self):
        # builds shared_info class variable with data and classes initialized  ready for run
        # from single run case_runner_params
        si =self.shared_info

        si.msg_logger.insert_screen_line()
        si.msg_logger.msg('Starting case number %3.0f, ' % si.processorID + ' '
                                      + si.output_files['output_file_base']
                                      + ' at ' + time_util.iso8601_str(datetime.now()))
        si.msg_logger.insert_screen_line()

        if si.settings['advanced_settings']['use_random_seed']:
            #todo this may not set numbas random seed!!
            np.random.seed(0)
            si.msg_logger.msg('Using numpy.random.seed(0), makes results reproducible (only use for testing developments give the same results!)',warning=True)

        # get short class names map
        # delay  start, which may avoid occasional lockup at start if many cases try to read same hindcast file at same time
        if si.settings['advanced_settings']['multiprocessing_case_start_delay'] is not None:
            delay = si.settings['advanced_settings']['multiprocessing_case_start_delay'] * (si.processorID % si.settings['processors'])
            si.msg_logger.progress_marker('Delaying start by  ' + str(delay) + ' sec')
            sleep(delay)
            si.msg_logger.progress_marker('Starting after delay  of ' + str(delay) + ' sec')

        # not sure if buffer is to small, but make bigger to 512 as default,  Numba default is  128, may slow code due to recompilations from too small buffer??
        environ['numba_function_cache_size'] = str(si.settings['advanced_settings']['numba_function_cache_size'])

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
        si.msg_logger.insert_screen_line()
        si.msg_logger.progress_marker('Starting ' + si.output_file_base + ',  duration: ' + time_util.seconds_to_pretty_duration_string(si.solver_info['model_duration']))

        #------------------------------------------
        solver.initialize_run()
        solver.solve()
        # ------------------------------------------




    def _do_run_integrity_checks(self):
        si=self.shared_info
        grid = si.classes['reader'].grid

        # check all have required, fields, part props and grid data
        for i in si.all_class_instance_pointers_iterator():
            i.check_requirements()

        # other checks and warnings
        if si.settings['open_boundary_type'] > 0:
            if not np.any(grid['node_type'] == 3):
                si.msg_logger.msg('Open boundary requested, but no open boundary node data available, boundaries will be closed,',
                                        hint='For Schism open boundaries requires hgrid file to named in reader params',warning=True)
        else:
            si.msg_logger.msg('No open boundaries requested, as run_params["open_boundary_type"] = 0',note=True,
                                      hint='Requires list of open boundary nodes not in hydro model, eg for Schism this can be read from hgrid file to named in reader params and run_params["open_boundary_type"] = 1')

        si.msg_logger.exit_if_prior_errors()

    def _make_core_class_instances(self):
        # params are full merged by oceantracker main and instance making tested, so m=no parm merge needed
        si = self.shared_info
        case_params= si.working_params

        # make core classes, eg. field group
        for name, params in case_params['core_classes'].items():
            i = si.add_core_class(name, params, crumbs= f'core class "{name}" ')

        si.particle_status_flags= si.classes['particle_group_manager'].status_flags



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
                si.msg_logger.msg('Release group= ' + str(n + 1) + ', name= ' + i.info['name'] + ',  no release times in range of hindcast and given release duration', warning=True)
                continue
            else:
                first_release_time.append(release_info['first_release_time'])
                last_time_alive.append(release_info['last_time_alive'])

        if len(si.classes['release_groups']) == 0:
            # guard against there being no release groups
            si.msg_logger.msg('No valid release groups, exiting' , fatal_error=True, exit_now=True)

        t_first = np.min(np.asarray(first_release_time))
        t_last  = np.max(np.asarray(last_time_alive))

        # time range in forwards order
        return t_first, t_last

    def _initialize_solver_core_classes_and_release_groups(self):
        # initialise all classes, order is important!
        # shortcuts

        si = self.shared_info
        reader= si.classes['reader']
        # start with setting up reader as it has info on whether 2D or 3D which  changes class options'
        # reader prams should be full and complete from oceanTrackerRunner, so dont initialize
        si.classes['field_group_manager'].initial_setup()  # needed here to add reader fields inside reader build
        reader.initial_setup()

        # now know if 3D hindcast
        si.hydro_model_is3D = si.classes['fields']['water_velocity'].is3D()

        if si.settings['time_step'] is None:
            time_step = reader.info['file_info']['hydro_model_time_step']
            si.msg_logger.msg("No time step given, using hydro-model's time step =" + str(time_step) + 'sec', note=True)
        else:
            time_step =  si.settings['time_step']
            if time_step > reader.info['file_info']['hydro_model_time_step']:
                time_step = reader.info['file_info']['hydro_model_time_step']
                si.msg_logger.msg("Time step is greater than hydro-model's, this capability not yet available, using hydro-model's time step = " + str(time_step) + ' sec', warning=True)

        si.solver_info['model_time_step'] = time_step
        si.model_time_step = time_step

        # set up start time and duration based on particle releases
        t0 = perf_counter()
        time_start, time_end = self._setup_particle_release_groups(si.working_params['class_dicts']['release_groups'])


        #clip times to maximum duration in shared and case params
        duration = abs(time_end - time_start)
        duration = min(duration, si.settings['max_run_duration'])
        time_end = time_start + duration* si.model_direction

        # note results
        si.solver_info['model_start_time'] = time_start
        si.solver_info['model_end_time'] = time_end
        si.solver_info['model_duration'] = max(abs(time_end - time_start), si.model_time_step) # at least one time step

        # estimate total particle released  to use as particle buffer size
        # first need to clip particle releases times to fit within run duration, which may be shorter than the hindcast
        estimated_total_particles = 0
        for name, rg in si.classes['release_groups'].items():
            ri = rg.info['release_info']
            sel = np.logical_and( time_start * si.model_direction <=  ri['release_times']  * si.model_direction,
                                    ri['release_times']  * si.model_direction<= time_end  * si.model_direction)
            ri['release_times'] = ri['release_times'][sel]
            ri['release_dates'] = time_util.seconds_to_datetime64(ri['release_times'])
            estimated_total_particles += rg.estimated_total_number_released() # get number from clipped r

        si.msg_logger.progress_marker('set up release_groups', start_time=t0)

        # useful info
        si.solver_info['model_start_date'] = time_util.seconds_to_datetime64(time_start)
        si.solver_info['model_end_date'] = time_util.seconds_to_datetime64(time_end)
        si.solver_info['model_timedelta'] =time_util.seconds_to_pretty_duration_string(si.model_time_step)
        si.solver_info['model_duration_timedelta'] = time_util.seconds_to_pretty_duration_string(si.solver_info['model_duration'] )

        # value time to forced timed events to happen first time accounting for backtracking, eg if doing particle stats, every 3 hours
        si.time_of_nominal_first_occurrence = si.model_direction * 1.0E36
        # todo get rid of time_of_nominal_first_occurrence

        if si.write_tracks:
            si.classes['tracks_writer'].initial_setup()

        # initialize the rest of the core classes
        #todo below apply to all core classes, reader
        t0 = perf_counter()
        for name in ['field_group_manager','particle_group_manager', 'interpolator', 'solver'] : # order may matter?
            si.classes[name].initial_setup()
        si.msg_logger.progress_marker('initial set up of core classes', start_time=t0)




        # do final setp which may depend on settingd from intitial st up
        t0= perf_counter()
        # order matters, must do interpolator after particle_group_manager, to get stucted arrays and solver last
        for name in ['field_group_manager','particle_group_manager', 'interpolator', 'solver'] :
            si.classes[name].final_setup()
        si.msg_logger.progress_marker('final set up of core classes',start_time=t0)

    def _make_and_initialize_user_classes(self):
        # complete build of particle by adding reade, custom properties and modifiers
        si= self.shared_info
        pgm = si.classes['particle_group_manager']

        # create prop particle properties derived from fields loaded from reader on the fly
        t0= perf_counter()
        for prop_type in ['from_reader_field','derived_from_reader_field','depth_averaged_from_reader_field']:
            for name, i in si.classes['fields'].items():
                if i.info['group'] == prop_type:
                    pgm.create_particle_property(name, 'from_fields', dict( vector_dim=i.get_number_components(), time_varying=True,
                                                                 write= True if i.params['write_interp_particle_prop_to_tracks_file'] else False))
        si.msg_logger.progress_marker('created particle properties derived from fields', start_time=t0)
        # initialize custom fields calculated from other fields which may depend on reader fields, eg friction velocity from velocity
        for n, params in enumerate(si.working_params['class_dicts']['fields']):
            i = si.create_class_dict_instance('fields', 'user', params, crumbs='Adding "fields" from user params')
            i.initial_setup()
            # now add custom prop based on  this field
            pgm.create_particle_property(i.info['name'], 'from_fields', dict(vector_dim=i.get_number_components(), time_varying=i.is_time_varying(),
                                                             write= True if i.params['write_interp_particle_prop_to_tracks_file'] else False))

            # if not time varying can update once at start from other non-time varying fields
            if not i.is_time_varying(): i.update()

        # any custom particle properties added by user
        for name, p in si.working_params['class_dicts']['particle_properties'].items():
            pgm.create_particle_property(name, 'user',p)

        # add default classes, eg tidal stranding
        #todo this may be better else where
        if 'dry_cell_index' in si.classes['reader'].grid and 'tidal_stranding' not in  si.working_params['class_dicts']['status_modifiers']:
            si.working_params['class_dicts']['status_modifiers']['tidal_stranding'] ={'class_name': 'oceantracker.status_modifiers.tidal_stranding.TidalStranding'}

        # build and initialise other user classes, which may depend on custom particle props above or reader field, not sure if order matters
        for user_type in ['velocity_modifiers','trajectory_modifiers','status_modifiers',
                             'particle_statistics', 'particle_concentrations', 'event_loggers']:
            for name, params in si.working_params['class_dicts'][user_type].items():
                i = si.create_class_dict_instance(name,user_type, 'user', params, crumbs=' making class type ' + user_type + ' ')
                i.initial_setup()  # some require instanceID from above add class to initialise

    # ____________________________
    # internal methods below
    # ____________________________
    def _get_case_info(self, d0, t0):
        si = self.shared_info
        pgm= si.classes['particle_group_manager']
        info = self.info
        info['date_of_time_zero'] = time_util.seconds_to_datetime64(np.asarray([0.]))
        r = si.classes['reader']

        info['time_zone'] = r.params['time_zone']
        info['backtracking'] = si.backtracking
        elapsed_time_sec = perf_counter() -t0
        info.update(dict(started=str(d0), ended=str(datetime.now()),
                         duration=str(datetime.now() - d0),
                         elapsed_time_sec=elapsed_time_sec,
                         number_particles_released= pgm.particles_released))

        # base class variable warnings is common with all descendents of parameter_base_class
        d = {'user_note': si.settings['user_note'],
             'output_files': si.output_files,
             'processorID' : si.processorID,
             'version_info': get_versions_computer_info.get_code_version(),
            'computer_info': get_versions_computer_info.get_computer_info(),
             'file_written': datetime.now().isoformat(),
             'run_info' : info,
             'solver_info' : si.solver_info,
             'hindcast_info': r.info,
             'full_case_params': si.working_params,
             'particle_status_flags': si.particle_status_flags,
             'particle_release_group_info' : [],
             'particle_release_group_user_maps': si.classes['particle_group_manager'].get_release_group_userIDmaps(),
             'errors': si.msg_logger.errors_list,
             'warnings': si.msg_logger.warnings_list,
             'notes': si.msg_logger.notes_list,
             'function_timers': {},

             'class_info': {}, }

        for key, i in si.classes.items():

            if type(i) == dict:
                d['class_info'][key] = {}
                d['output_files'][key] = {}
                # interate over dict
                for key2, i2 in i.items():
                    d['class_info'][key][key2]= i2.info
                    d['output_files'][key][key2]= i2.info['output_file'] if 'output_file' in i2.info else None

            else:
                d['class_info'][key] = i.info
                d['output_files'][key] = i.info['output_file'] if 'output_file' in i.info else None

        for key, item in si.classes['release_groups'].items():
            rginfo=item.params
            rginfo.update(item.info['release_info'])
            d['particle_release_group_info'].append(rginfo)

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
