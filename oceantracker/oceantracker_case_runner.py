from copy import deepcopy
from os import path, environ, remove
from oceantracker.util.parameter_base_class import ParameterBaseClass, make_class_instance_from_params
from oceantracker.util.messgage_logger import MessageLogger, GracefulError

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
        t0 = datetime.now()
        # basic param shortcuts
        si.shared_params = runner_params['shared_params']
        si.run_params = runner_params['case_params']['run_params']
        si.case_params = runner_params['case_params']
        si.output_files = runner_params['output_files']
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

        si.z0 = si.run_params['z0']
        si.minimum_total_water_depth = si.case_runner_params['shared_params']['minimum_total_water_depth']
        si.processor_number = runner_params['processor_number']


        # set up message logging
        output_files=runner_params['output_files']
        si.msg_logger = MessageLogger('P%03.0f:' % si.processor_number)
        output_files['case_log_file'], output_files['case_error_file'] = \
        si.msg_logger.set_up_files(output_files['run_output_dir'],output_files['output_file_base'] + '_caseLog')

        si.msg_logger.set_max_warnings(si.shared_params['max_warnings'])


        case_info_file = None
        case_exception = None
        # case set up
        try:
            self._set_up_run(runner_params)
            self._make_core_class_instances(runner_params)
            si.solver_info = si.classes['solver'].info  # allows shortcut access from other classes
            self._initialize_solver_core_classes_and_release_groups()


            self._make_and_initialize_user_classes()
            si.classes['dispersion'].initialize()  # is not done in _initialize_solver_core_classes_and_release_groups as it may depend on user classes to work

            # todo set up memory for all defined particle properties
            # todo memory packing is being developed and evaluated for speed
            #si.classes['particle_group_manager'].create_particle_prop_memory_block()

            # check particle properties have other particle properties, fields and other compatibles they require
            self._do_run_integrity_checks()

        except GracefulError as e:
            si.msg_logger.msg(' Graceful exit >>  Parameters/setup has errors, see above', fatal_error= True)
            si.msg_logger.write_error_log_file(e)
            return None, True

        except Exception as e:
            si.msg_logger.msg('Unexpected error  in case set up',fatal_error=True)
            si.msg_logger.write_error_log_file(e)
            return None, True

        # try running case
        try:
            self._do_a_run()
            case_info = self._get_case_info(t0)

            if si.shared_params['write_output_files']:
                case_info_file = si.output_file_base + '_caseInfo.json'
                json_util.write_JSON(path.join(si.run_output_dir, case_info_file), case_info)

        except GracefulError as e:
            si.msg_logger.show_all_warnings_and_errors()
            si.msg_logger.write_error_log_file(e)
            si.msg_logger.msg(f' Graceful exit from case number [{si.processor_number:2}]', hint ='Parameters/setup has errors, see above', fatal_error= True)
            return None, True

        except Exception as e:
            si.msg_logger.show_all_warnings_and_errors(e)
            si.msg_logger.write_error_log_file(e)
            si.msg_logger.msg(f' Unexpected error in case number [{si.processor_number:2}] ', fatal_error=True,hint='check above or .err file')
            return None, True

        # reshow warnings
        si.msg_logger.show_all_warnings_and_errors()
        si.msg_logger.insert_screen_line()
        si.msg_logger.progress_marker('Finished case number %3.0f, ' % si.processor_number + ' '
                                      + si.output_files['output_file_base']
                                      + ' started: ' + str(t0)
                                      + ', ended: ' + str(datetime.now()))
        si.msg_logger.msg('Elapsed time =' + str(datetime.now() - t0), tabs=3)
        si.msg_logger.insert_screen_line()
        si.msg_logger.close()
        return case_info_file, False

    def _set_up_run(self,runner_params):
        # builds shared_info class variable with data and classes initialized  ready for run
        # from single run case_runner_params


        # put needed variables in shared info
        self.user_set_params = deepcopy(runner_params)  # used for log file
        si = self.shared_info

        si.msg_logger.insert_screen_line()
        si.msg_logger.progress_marker('Starting case number %3.0f, ' % si.processor_number + ' '
                                      + si.output_files['output_file_base']
                                      + ' at ' + time_util.iso8601_str(datetime.now()))
        si.msg_logger.insert_screen_line()

        if si.shared_params['use_numpy_random_seed']:
            np.random.seed(0)
            si.msg_logger.msg('Using numpy.random.seed(0), makes results reproducible (only use for testing developments give the same results!)',warning=True)

        # get short class names map
        # delay  start, which may avoid occasional lockup at start if many cases try to read same hindcast file at same time
        if si.shared_params['multiprocessing_case_start_delay'] > 0:
            delay = si.shared_params['multiprocessing_case_start_delay'] * (si.processor_number % si.shared_params['processors'])
            si.msg_logger.progress_marker('Delaying start by  ' + str(delay) + ' sec')
            sleep(delay)
            si.msg_logger.progress_marker('Starting after delay  of ' + str(delay) + ' sec')

        # not sure if buffer is to small, but make bigger to 512 as default,  Numba default is  128, may slow code due to recompilations from too small buffer??
        environ['numba_function_cache_size'] = str(si.shared_params['numba_function_cache_size'])

        if si.shared_params['debug']:
            # makes it easier to debug, particularly  in pycharm
            environ['NUMBA_BOUNDSCHECK'] = '1'
            environ['NUMBA_FULL_TRACEBACKS'] = '1'
            si.msg_logger.msg('Running in debug mode',note=True)


    def _do_a_run(self):
        # build and run solver from parameter dictionary
        # run from a given dictionary to enable particle tracking on demand from JSON type parameter set
        # also used for parallel  version
        self.code_timer.start('total_model_all')
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


        # close all instances
        for i in si.all_class_instance_pointers_iterator():
            i.close()


        self.code_timer.stop('total_model_all')



    def _do_run_integrity_checks(self):
        si=self.shared_info
        grid = si.classes['reader'].grid

        # check all have required, fields, part props and grid data
        for i in si.all_class_instance_pointers_iterator():
            i.check_requirements()

        # other checks and warnings
        if si.run_params['open_boundary_type'] > 0:
            if not np.any(grid['node_type'] == 3):
                si.msg_logger.msg('Open boundary requested, but no open boundary node data available, boundaries will be closed,',
                                        hint='For Schism open boundaries requires hgrid file to named in reader params',warning=True)
        else:
            si.msg_logger.msg('No open boundaries requested, as run_params["open_boundary_type"] = 0',note=True,
                                      hint='Requires list of open boundary nodes not in hydro model, eg for Schism this can be read from hgrid file to named in reader params and run_params["open_boundary_type"] = 1')

        si.msg_logger.exit_if_prior_errors()

    def _make_core_class_instances(self, run_params):
        # params are full merged by oceantracker main and instance making tested, so m=no parm merge needed
        si=self.shared_info
        case_params= run_params['case_params']

        # change writer for compact mode
        if si.shared_params['compact_mode']:
            case_params['core_classes']['tracks_writer']['class_name']='oceantracker.tracks_writer.track_writer_compact.FlatTrackWriter'

        # make core classes, eg. field group
        for key, params in case_params['core_classes'].items():
            # merge params
            i = make_class_instance_from_params(params,si.msg_logger, class_type_name=key, crumbs= key)
            si.add_core_class(key, i)


        si.particle_status_flags= si.classes['particle_group_manager'].status_flags

        i = make_class_instance_from_params( si.reader_build_info['reader_params'],si.msg_logger, class_type_name='reader', crumbs='reader')
        si.add_core_class('reader', i,check_if_core_class=False)  # use cor ecars as name

        # some core classes required the presence of others to initialize so do all here in given order, with solver last
        #for name in ['reader','field_group_manager','particle_group_manager','interpolator','tracks_writer','dispersion','solver']:
        #    si.classes[name].initialize()

    def _setup_particle_release_groups(self, particle_release_groups_params_list):
        # particle_release groups setup and instances,
        # find extremes of  particle existence to calculate model start time and duration
        #todo move to particle group manager and run in main at set up to get reader range etc , better for shared reader development
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
            i = make_class_instance_from_params(pg_params,si.msg_logger,crumbs='particle release group')
            si.add_class_instance_to_interator_lists('particle_release_groups', 'user', i, crumbs='Adding release groups')
            i.initialize()

            # set up release times so duration of run known
            i.set_up_release_times(n)
            release_info = i.info['release_info']

            if release_info['release_times'].size == 0:
                si.msg_logger.msg('Release group= ' + str(n + 1) + ', name= ' + i.params['name'] + ',  no release times in range of hindcast and given release duration', warning=True)
                continue
            else:
                estimated_total_particles += release_info['estimated_number_released'] # used to give buffer size if needed
                first_release_time.append(release_info['first_release_time'])
                last_time_alive.append(release_info['last_time_alive'])

        if len(si.classes['particle_release_groups']) == 0:
            # guard against there being no release groups
            si.msg_logger.msg('No valid release groups, exiting' , fatal_error=True, exit_now=True)

        t_first = np.min(np.asarray(first_release_time))
        t_last  = np.max(np.asarray(last_time_alive))

        # time range in forwards order
        si.msg_logger.progress_marker('set up particle release groups')

        return t_first, t_last, estimated_total_particles

    def _initialize_solver_core_classes_and_release_groups(self):
        # initialise all classes, order is important!
        # short cuts
        si = self.shared_info
        reader= si.classes['reader']
        # start with setting up reader as it has info on whether 2D or 3D which  changes class options'
        # reader prams should be full and complete from oceanTrackerRunner, so dont initialize
        si.classes['field_group_manager'].initialize() # needed here to add reader fields inside reader build
        reader.build_case_runner_reader(si.reader_build_info)

        # now know if 3D hindcast
        si.hydro_model_is3D = si.classes['fields']['water_velocity'].is3D()

        if si.shared_params['time_step'] is None:
            time_step = reader.info['hydro_model_time_step']
            si.msg_logger.msg("No time step given, using hydro-model's time step =" + str(time_step) + 'sec', note=True)
        else:
            time_step =  si.shared_params['time_step']
            if time_step > reader.info['hydro_model_time_step']:
                time_step = reader.info['hydro_model_time_step']
                si.msg_logger.msg("Time step is greater than hydro-model's, this capability not yet available, using hydro-model's time step =" + str(time_step) + 'sec', warning=True)

        si.solver_info['model_time_step'] = time_step
        si.model_time_step = time_step

        # set up start time and duration based on particle releases
        time_start, time_end, estimated_total_particles = self._setup_particle_release_groups(si.case_params['class_lists']['particle_release_groups'])
        si.msg_logger.progress_marker('set up particle_release_groups')

        #clip time to maximum duration in shared params
        if  time_end - time_start  > si.shared_params['max_duration']:
            time_end = time_start + si.shared_params['max_duration'] * si.model_direction

        si.solver_info['model_start_time'] = time_start
        si.solver_info['model_end_time'] = time_end
        si.solver_info['model_duration'] = abs( time_end - time_start)



        # useful info


        si.solver_info['model_start_date'] = time_util.seconds_to_datetime64(time_start)
        si.solver_info['model_end_date'] = time_util.seconds_to_datetime64(time_end)
        si.solver_info['model_timedelta'] =time_util.seconds_to_pretty_duration_string(si.shared_params['time_step'])
        si.solver_info['model_duration_timedelta'] = time_util.seconds_to_pretty_duration_string(si.solver_info['model_duration'] )


        # value time to forced timed events to happen first time accounting for backtracking, eg if doing particle stats, every 3 hours
        si.time_of_nominal_first_occurrence = si.model_direction * 1.0E36
        # todo get rid of time_of_nominal_first_occurrence

        # find particle buffer size required by several classes
        if si.run_params['particle_buffer_size'] is None:
            si.run_params['particle_buffer_size'] = max(100, estimated_total_particles)

        si.particle_buffer_size = si.run_params['particle_buffer_size']

        if si.write_tracks:
            si.classes['tracks_writer'].initialize()

        # initialize the rest of the core classes
        for name in ['particle_group_manager', 'interpolator', 'solver'] : # order may matter?
            si.classes[name].initialize()

        si.msg_logger.progress_marker('initialized all core classes')

    def _make_and_initialize_user_classes(self):
        # complete build of particle by adding reade, custom properties and modifiers
        si= self.shared_info
        pgm = si.classes['particle_group_manager']

        # create prop particle properties derived from fields loaded from reader on the fly
        for prop_type in ['from_reader_field','derived_from_reader_field','depth_averaged_from_reader_field']:
            for name, i in si.class_interators_using_name['fields'][prop_type].items():
                pgm.create_particle_property('from_fields', dict(name=name,  vector_dim=i.get_number_components(), time_varying=True,
                                                                 write= True if i.params['write_interp_particle_prop_to_tracks_file'] else False))

        # initialize custom fields calculated from other fields which may depend on reader fields, eg friction velocity from velocity
        for n, params in enumerate(si.case_params['class_lists']['fields']):
            i = make_class_instance_from_params(params, si.msg_logger, crumbs='user fields')
            si.add_class_instance_to_interator_lists('fields','user', i, crumbs='Adding "fields" from user params')
            i.initialize()
            # now add custom prop based on  this field
            pgm.create_particle_property('from_fields', dict(name=i.params['name'], vector_dim=i.get_number_components(),
                                                             time_varying=i.is_time_varying(),
                                                             write= True if i.params['write_interp_particle_prop_to_tracks_file'] else False))

            # if not time varying can update once at start from other non-time varying fields
            if not i.is_time_varying(): i.update()

        # any custom particle properties added by user
        for p in si.case_params['class_lists']['particle_properties']:
            pgm.create_particle_property('user',p)

        # add default classes, eg tidal stranding
        #todo this may be better else where
        if 'dry_cell_index' in si.classes['reader'].grid_time_buffers and 'tidal_stranding' not in  si.case_params['class_lists']['status_modifiers']:
            si.case_params['class_lists']['status_modifiers'].append({'name':'tidal_stranding','class_name': 'oceantracker.status_modifiers.tidal_stranding.TidalStranding'})

        # build and initialise other user classes, which may depend on custom particle props above or reader field, not sure if order matters
        for user_type in ['velocity_modifiers', 'trajectory_modifiers',
                     'particle_statistics',
                     'particle_concentrations', 'event_loggers','status_modifiers']:
            for n, params in enumerate(si.case_params['class_lists'][user_type]):
                i = make_class_instance_from_params(params, msg_logger=si.msg_logger, crumbs= 'user type ' + user_type)
                si.add_class_instance_to_interator_lists(user_type, 'user', i)
                i.initialize()  # some require instanceID from above add class to initialise
        pass
    # ____________________________
    # internal methods below
    # ____________________________
    def _get_case_info(self, t0):
        si = self.shared_info
        pgm= si.classes['particle_group_manager']
        info = self.info
        info['date_of_time_zero'] = time_util.seconds_to_datetime64(np.asarray([0.]))
        r = si.classes['reader']

        info['time_zone'] = r.params['time_zone']
        info['backtracking'] = si.backtracking


        info.update(dict(started= str(t0),ended= str(datetime.now()), elapsed_time = str(datetime.now() - t0)))

        # base class variable warnings is common with all descendents of parameter_base_class
        d = {'run_user_note': si.shared_params['user_note'],
             'case_user_note': si.run_params['user_note'],
             'processor_number' : si.processor_number,
             'file_written': datetime.now().isoformat(),
             'code_version_info': si.case_runner_params['code_version_info'],
             'run_info' : info,
             'solver_info' : si.solver_info,
             'hindcast_info': r.info,
             'particle_release_group_info' : [],
             'particle_release_group_user_maps': si.classes['particle_group_manager'].get_release_group_userIDmaps(),
             'warnings_errors': si.msg_logger.warnings_and_errors,
             'timers': self.code_timer.time_sorted_timings(),
             'time_updating': {},
             'output_files': si.output_files,
             'particles': { 'num_released': pgm.particles_released,
                            'particle_status_flags': si.particle_status_flags},
             'shared_params': si.shared_params,
             'case_params': si.case_runner_params['case_params'],
             'full_params': {},
             'class_info': {},

              }

        for key, i in si.core_class_interator.items():
            if i is None: continue
            d['full_params'][key] = i.params
            d['class_info'][key] = i.info
            if 'output_file' in i.info:
                d['output_files'][key] = i.info['output_file']
            else:
                d['output_files'][key] = None


        for key, item in si.class_interators_using_name.items():
            # a class list type
            d['full_params'][key]=[]
            d['class_info'][key] = []
            d['output_files'][key] =[]
            d['time_updating'][key] =[]

            for i in item['all'].values():
                d['full_params'][key].append(i.params)
                d['class_info'][key].append(i.info)
                if 'output_file' in i.info:
                    d['output_files'][key].append(i.info['output_file'])
                else:
                    d['output_files'][key].append(None)

        for key, item in si.classes['particle_release_groups'].items():
            rginfo=item.params
            rginfo.update(item.info['release_info'])
            d['particle_release_group_info'].append(rginfo)


          # adds maps

        return d
