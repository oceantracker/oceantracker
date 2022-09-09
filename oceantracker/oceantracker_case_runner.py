from copy import deepcopy
from os import path, environ, remove
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.message_and_error_logging import MessageLogging, GracefulExitError, FatalError
import numpy as np
from oceantracker.util import time_util

from oceantracker.util import json_util
from datetime import datetime
from time import sleep
import traceback

class OceanTrackerCaseRunner(ParameterBaseClass):
    # this class runs a single case
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required

    def run(self, runner_params):
        si=self.shared_info
        si.reset()  # clear out classes from class instance of SharedInfo if running series of mains
        case_info_file = None
        case_exception = None


        msg_list=[]
        try:
            self._set_up_run(runner_params)
            self._make_core_class_instances(runner_params)

            self._initialize_solver_and_core_classes()

            self._make_and_initialize_user_classes()

            si.classes['dispersion'].initialize()  # is not done in _initialize_solver_and_core_classes as it may depend on user classes to work


            # check particle properties have other particle properties, fields and other compatibles they require
            self._do_run_integrity_checks()


        except GracefulExitError as e:
            si.case_log.write_msg('Input or parameter errors: GracefulExitError')
            case_exception = e
        else:
            # if no setup errors, try to run
            try:
                self._do_a_run()
                case_info = self._get_case_info()
                self.code_timer.stop('total_model_all')

                if si.shared_params['write_output_files']:
                    case_info_file = si.output_file_base + '_caseInfo.json'
                    json_util.write_JSON(path.join(si.run_output_dir, case_info_file), case_info)

                si.case_log.write_progress_marker('Ended ' + si.output_file_base + ',  elapsed time =' + self.info['model_run_duration'])

            except GracefulExitError as e:
                si.case_log.write_msg(' Graceful exit >>  Parameters/setup has errors, see above', exception = GracefulExitError)
                return None, True

            except FatalError as e:
                si.case_log.write_error_log_file(e)
                return None, True

            except Exception as e:
                # other error
                msg = 'Unknown error, see .err file'
                si.case_log.write_msg(msg)
                si.case_log.write_msg(str(e))
                si.case_log.write_error_log_file(e)
                raise Exception(msg)


        finally:
            # reshow warnings
            si.case_log.show_all_warnings_and_errors()
            si.case_log.insert_screen_line()
            si.case_log.write_progress_marker('Finished case number %3.0f, ' % si.processor_number + ' '
                                  + si.output_files['output_file_base']
                                  + ' at ' + time_util.iso8601_str(datetime.now()))
            si.case_log.close()

        return case_info_file, case_exception

    def _set_up_run(self,runner_params):
        # builds shared_info class variable with data and classes initialized  ready for run
        # from single run case_runner_params

        self.code_timer.start('total_model_all')
        # put needed variables in shared info
        self.user_set_params = deepcopy(runner_params)  # used for log file
        si = self.shared_info

        # basic param shortcuts
        si.shared_params = runner_params['shared_params']
        si.run_params    = runner_params['case_params']['run_params']
        si.case_params = runner_params['case_params']
        si.output_files = runner_params['output_files']
        si.processor_number = runner_params['processor_number']
        si.reader_build_info = runner_params['reader_build_info']
        si.case_runner_params = runner_params

        si.run_output_dir = si.output_files['run_output_dir']
        si.output_file_base = si.output_files['output_file_base']

        # other useful shared values
        si.backtracking = si.shared_params['backtracking']
        si.model_direction = -1 if si.backtracking else 1
        si.write_output_files = si.shared_params['write_output_files']
        si.write_tracks = si.run_params['write_tracks']
        si.retain_culled_part_locations = si.run_params['retain_culled_part_locations']
        si.compact_mode = si.shared_params['compact_mode']

        # useful info
        si.z0 = si.run_params['z0']
        si.minimum_total_water_depth = si.case_runner_params['reader_build_info']['reader_params']['minimum_total_water_depth']

        # set up message logging
        si.case_log = MessageLogging('P%03.0f:' % si.processor_number)
        si.case_log.set_max_warnings(si.shared_params['max_warnings'])
        si.case_log.set_up_log_file(si.run_output_dir, si.output_file_base, 'caseLog')

        si.case_log.insert_screen_line()
        si.case_log.write_progress_marker('Starting case number %3.0f, ' % si.processor_number + ' '
                              + si.output_files['output_file_base']
                              +' at ' + time_util.iso8601_str(datetime.now()))
        si.case_log.insert_screen_line()

        if si.shared_params['use_numpy_random_seed']:
            np.random.seed(0)
            si.case_log.write_warning('Using numpy.random.seed(0), makes results reproducible (only use for testing developments give the same results!)')

        # get short class names map
        # delay  start, which may avoid occasional lockup at start if many cases try to read same hindcast file at same time
        if si.shared_params['multiprocessing_case_start_delay'] > 0:
            delay = si.shared_params['multiprocessing_case_start_delay'] * (si.processor_number % si.shared_params['processors'])
            si.case_log.write_progress_marker('Delaying start by  ' + str(delay) + ' sec')
            sleep(delay)
            si.case_log.write_progress_marker('Starting after delay  of ' + str(delay) + ' sec')

        # not sure if buffer is to small, but make bigger to 512 as default,  Numba default is  128, may slow code due to recompilations from too small buffer??
        environ['numba_function_cache_size'] = str(si.shared_params['numba_function_cache_size'])

        if si.shared_params['debug']:
            # makes it easier to debug, particularly  in pycharm
            environ['NUMBA_BOUNDSCHECK'] = '1'
            environ['NUMBA_FULL_TRACEBACKS'] = '1'
            si.case_log.write_warning('Running in debug mode')

    def _do_a_run(self):
        # build and run solver from parameter dictionary
        # run from a given dictionary to enable particle tracking on demand from JSON type parameter set
        # also used for parallel  version
        si = self.shared_info
        info= self.info
        info['model_run_started'] = datetime.now()

        solver = si.classes['solver']
        p, reader, f = si.classes['particle_group_manager'], si.classes['reader'], si.classes['field_group_manager']  # for later use


        si.case_log.write_progress_marker('Starting ' + si.output_file_base + ',  duration: %4.1f days' % (si.model_duration / 24 / 3600))


        # get hindcast step range
        nt0 = reader.time_to_global_time_step(si.model_start_time)
        nt1 = reader.time_to_global_time_step(si.model_start_time +  int(si.model_direction)*si.model_duration)
        nt = nt0 + int(si.model_direction)*np.arange(0 , abs(nt1-nt0))

        # get fist block of nt's into buffer
        num_in_buffer = reader.fill_time_buffer(nt)
        # set up run now data in buffer
        solver.initialize_run(0)

        # fill and process buffer until there is less than 2 steps
        si.case_log.write_progress_marker('Starting ' + si.output_file_base + ',  duration: %4.1f days' % (si.model_duration / 24 / 3600))
        si.case_log.insert_screen_line()
        t = si.model_start_time

        while num_in_buffer > 1:

            time_steps_completed, t = solver.solve_for_data_in_buffer(0, num_in_buffer, nt0)

            if abs(t-si.model_start_time) > si.model_duration: break

            # set up for next block
            nt = nt[num_in_buffer-1:] # discard time steps done, but reload last step
            num_in_buffer = reader.fill_time_buffer(nt)

        # post run stuff
        info = self.info
        info['start_time'] = si.model_start_time
        info['end_time'] = t
        info['start_date'] = time_util.seconds_to_date(si.model_start_time)
        info['end_date'] = time_util.seconds_to_date(t)

        info['time_steps_completed'] = 1 if solver.info['n_time_steps_completed'] == 0 else solver.info['n_time_steps_completed']
        info['average_number_moving_particles'] = solver.info['total_num_particles_moving'] /info['time_steps_completed']

        # close all instances
        for i in si.all_class_instance_pointers_iterator():
            i.close()
        info['model_run_ended'] = datetime.now()
        info['model_run_duration'] = time_util.duration_str_from_dates(info['model_run_started'], datetime.now())

    def _do_run_integrity_checks(self):
        si=self.shared_info
        msg_list = []

        # check all have required, fields, part props and grid data
        for i in si.all_class_instance_pointers_iterator():
            msg_list += i.check_requirements()


        # other checks and warnings
        if si.run_params['open_boundary_type'] > 0:
            if not si.grid['has_open_boundary_data']:
                si.case_log.write_warning('Open boundary requested, but no open boundary node data available, boundaries will be closed,',
                                        hint='For Schism open boundaries requires hgrid file to named in reader params')
        else:
            si.case_log.write_note('No open boundaries requested, as run_params["open_boundary_type"] = 0',
                                      hint='For Schism open boundaries requires hgrid file to named in reader params and run_params["open_boundary_type"] = 1')

        if len(msg_list) > 0:
            si.case_log.add_messages(msg_list)
            si.case_log.check_messages_for_errors()

    def _make_core_class_instances(self, run_params):
        # parsm are full merged by oceantracker main and instance making tested, so m=no parm merge needed
        si=self.shared_info
        case_params= run_params['case_params']

        # chage writer for compact mode
        if si.shared_params['compact_mode']:
            case_params['core_classes']['tracks_writer']['class_name']='oceantracker.tracks_writer.track_writer_compact.FlatTrackWriter'

        # make core classes
        for key, params in case_params['core_classes'].items():
            params['name'] = key
            si.add_core_class(key, params) # use cor ecars as name

        si.particle_status_flags= si.classes['particle_group_manager'].status_flags
        self._make_reader_instance()

    def _make_reader_instance(self):
        # make reader, seperstly to allow for a prebuilt full hindcast in memory reader to be used
        si = self.shared_info
        si.add_core_class('reader', si.reader_build_info['reader_params'],make_core=True)  # use cor ecars as name



    def _setup_particle_release_groups(self, particle_release_groups_params_list):
        # particle_release groups setup and instances,
        # find extremes of  particle existence to calculate model start time and duration

        si = self.shared_info
        estimated_total_particles = 0

        # set up to start end times based on particle_release_groups
        # find earliest and last release times+life_duration ( if going forwards)

        first_release_time = []
        last_time_alive = []

        for n, pg_params in enumerate(particle_release_groups_params_list):
            # make instance
            if 'class_name' not in pg_params: pg_params['class_name'] = 'oceantracker.particle_release_groups.point_release.PointRelease'

            # make instance and initialise
            pg = si.add_class_instance_to_list_and_merge_params('particle_release_groups', 'user', pg_params, crumbs='Adding release groups')
            pg.initialize()


            # set up release times so duration of run known
            release_info = pg.set_up_release_times(n)

            if release_info['release_schedule_times'] is not None:
                si.add_class_instance_to_interators(pg.params['name'],'particle_release_groups', 'user', pg)

                estimated_total_particles += release_info['estimated_number_released'] # used to give buffer size if needed
                first_release_time.append(release_info['first_release_time'])
                last_time_alive.append(release_info['last_time_alive'])

            else:
                si.case_log.write_msg('Release group= ' + str(n + 1) + ',  no release times in range of hindcast and given release duration', warning=True)

        if len(si.classes['particle_release_groups']) == 0:
            # guard against there being no release groups
            raise FatalError('There are no valid release groups in range of hindcast')

        t_first = np.min(np.asarray(first_release_time)*si.model_direction)*si.model_direction
        t_last  = np.max(np.asarray(last_time_alive)*si.model_direction)*si.model_direction

        # time range in forwards order
        si.case_log.write_progress_marker('built case instances')

        return t_first, t_last, estimated_total_particles

    def _initialize_solver_and_core_classes(self):
        # initialise all classes, order is important!
        # short cuts
        si = self.shared_info
        msg_list= []
        # start with setting up reader as it has info on whether 2D or 3D which  changes class options'
        # reader prams should be full and complete from oceanTrackerRunner, so dont initialize
        si.classes['field_group_manager'].initialize() # needed here to add reader fields inside reader build
        si.classes['reader'].build_reader(si.reader_build_info)  # initialize here as need to find out if 3D for set up of other clsasses

        # now know if 3D hindcast
        si.hindcast_is3D = si.classes['fields']['water_velocity'].is3D()

        # Timings, sort out start and run duration
        n_substeps = float(max(1, si.classes['solver'].params['n_sub_steps']))

        si.hindcast_time_step = si.reader_build_info['sorted_file_info']['time_step']
        model_time_step = abs(si.hindcast_time_step / float(n_substeps))
          # always >0
        si.model_substep_timestep = model_time_step

        # set up start time and duration based on particle releases
        t_start, t_end, estimated_total_particles = self._setup_particle_release_groups(si.case_params['class_lists']['particle_release_groups'])
        si.case_log.write_progress_marker('set up particle_release_groups')

        duration = min(abs(t_end - t_start), si.run_params['duration'], si.shared_params['max_duration'])
        duration = max(duration, 2 * si.hindcast_time_step)  # do at least 2 time steps
        si.model_start_time = t_start
        si.model_duration = duration

        # value time to forced timed events to happen first time accounting for backtracking, eg if doing particle stats, every 3 hours
        si.time_of_nominal_first_occurrence = si.model_direction * np.inf

        # find particle buffer size required by several classes
        pb_estimate= estimated_total_particles + max(100,estimated_total_particles)

        if si.run_params['particle_buffer_size'] is None:
            si.run_params['particle_buffer_size'] =pb_estimate

        si.particle_buffer_size = si.run_params['particle_buffer_size']

        if si.write_tracks:
            si.classes['tracks_writer'].initialize()

        # initialize the rest of the core classes
        for name in ['particle_group_manager', 'interpolator', 'solver'] : # order may matters?
            si.classes[name].initialize()

        si.case_log.write_progress_marker('initialized all classes')

    def _make_and_initialize_user_classes(self):
        # complete build of particle by adding reade, custom properties and modifiers
        si= self.shared_info
        pgm = si.classes['particle_group_manager']
        fgm = si.classes['field_group_manager']

        # initialize custom fields calculated from other fields, eg friction velocity from velocity
        for n, params in enumerate(si.case_params['class_lists']['fields']):
            i = fgm.add_field('user', params, crumbs='Adding "fields" from user params')
            i.initialize()
            # now add custom prop based on  this field
            if i.params['create_particle_property_with_same_name']:
                pgm.create_particle_property('from_fields', dict(name=i.params['name'], vector_dim=i.get_number_components(), time_varying=i.is_time_varying()))

            # if not time varying can update once at start from other non-time varying fields
            if not i.is_time_varying(): i.update()

        # create prop particle properties derived from fields loaded from reader on the fly
        for prop_type in ['from_reader_field','derived_from_reader_field','depth_averaged_from_reader_field']:
            for name, fd in si.class_list_interators['fields'][prop_type].items():
                pgm.create_particle_property('from_fields', dict(name=name,  vector_dim=fd.get_number_components(), time_varying=True))

        # any custom particle properties added by user
        for p in si.case_params['class_lists']['particle_properties']:
            pgm.create_particle_property('user',p)

        # build and initialise other user classes, which may depend on custom particle props above or reader field, not sure if order matters
        for type in ['velocity_modifiers', 'trajectory_modifiers',
                     'particle_statistics',
                     'particle_concentrations', 'event_loggers']:
            for n, params in enumerate(si.case_params['class_lists'][type]):
                i= si.add_class_instance_to_list_and_merge_params(type,'user', params)
                si.add_class_instance_to_interators(i.params['name'], type,'user', i)
                i.initialize()

    # ____________________________
    # internal methods below
    # ____________________________
    def _get_case_info(self):
        si = self.shared_info
        info = self.info
        info['date_of_time_zero'] = time_util.ot_time_zero()
        r = si.classes['reader']
        info['time_zone'] = r.params['time_zone']
        info['model_timestep'] = si.model_substep_timestep
        info['model_start_date']  = time_util.seconds_to_iso8601str(si.model_start_time)
        info['model_duration_days'] = si.model_duration/24/3600.
        info['backtracking'] = si.backtracking
        # base class variable warnings is common with all descendents of parameter_base_class
        d = {'run_user_note': si.shared_params['user_note'],
             'case_user_note': si.run_params['user_note'],
             'processor_number' : si.processor_number,
             'file_written': datetime.now().isoformat(),
             'code_version_info': si.case_runner_params['code_version_info'],
             'run_info' : info,
             'hindcast_info': r.get_hindcast_info(),
             'particle_release_group_info' : [],
             'warnings': si.case_log.get_all_warnings_and_errors(),
             'timers': self.code_timer.time_sorted_timings(),
             'time_updating': {},
             'output_files': si.output_files,
             'particles': { 'num_released': si.classes['particle_group_manager'].particles_released,
                            'particle_status_flags': si.particle_status_flags},
             'shared_params': si.shared_params,
             'case_params': si.case_runner_params['case_params'],
             'full_params': {},
             'info': {},

              }

        for key, i in si.core_class_interator.items():
            if i is None: continue
            d['full_params'][key] = i.params
            d['info'][key] = i.info
            if 'output_file' in i.info:
                d['output_files'][key] = i.info['output_file']
            else:
                d['output_files'][key] = None
            d['time_updating'][key] = {'time': i.info['time_spent_updating'], 'calls': i.info['calls']}

        for key, item in si.class_list_interators.items():
            # a class list type
            d['full_params'][key]=[]
            d['info'][key] = []
            d['output_files'][key] =[]
            d['time_updating'][key] =[]

            for i in item['all'].values():
                d['full_params'][key].append(i.params)
                d['info'][key].append(i.info)
                if 'output_file' in i.info:
                    d['output_files'][key].append(i.info['output_file'])
                else:
                    d['output_files'][key].append(None)
                d['time_updating'][key].append({'time': i.info['time_spent_updating'], 'calls': i.info['calls']})


        for key, item in si.classes['particle_release_groups'].items():
            d['particle_release_group_info'].append(item.info['release_info'])


        d['info'].update(si.classes['particle_group_manager'].get_release_group_userIDmaps())  # adds maps

        return d
