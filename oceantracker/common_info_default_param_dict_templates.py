from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from os import path
package_fancy_name= 'OceanTracker'



# template for oceanTracker params, with defaults to check against
run_params_defaults_template = {'shared_params': {'user_note': PVC('No user note', str),
                                                 'root_output_dir':     PVC('default_root_output_dir', str, doc_str='base dir for all output files'),
                                                 'add_date_to_run_output_dir':  PVC(False, bool),
                                                 'output_file_base':    PVC('default_output_file_base', str),
                                                 'backtracking':        PVC(False, bool),
                                                 'debug':               PVC(False, bool),
                                                 'compact_mode':        PVC(False, bool,doc_str='Periodically discard dead particles from memory, eg. those too old to be be of interest, if used track output file also has a compact format'), # discard dead/inactive particles from memory
                                                 'write_output_files':     PVC(True,  bool),
                                                 'write_grid':          PVC(True,  bool),
                                                 'max_warnings':        PVC(50,    int, min=0),  # dont record more that this number of warnings, to keep caseInfo.json finite
                                                 'max_duration':        PVC(1.0e20, float),  # limit all cases to this duration
                                                 'processors':          PVC(1, int, min=1,doc_str='number of processors used, if > 1 then cases in the case_list run in parallel'),
                                                 'replicates':          PVC(1, int, min=1,doc_str='number of replicates of each case to run, allows running larger particle numbers for each case in less time if running in parallel'),
                                                'numba_function_cache_size' :  PVC(1024, int, min=128),
                                                'multiprocessing_case_start_delay': PVC(0., float, min=0.), # which lareg numbers of case, sometimes locks up at start al reading same file, so ad delay
                                                'use_numpy_random_seed':  PVC(False,  bool,doc_str='Makes results reproducible, only use for testing developments give the same results!')
                                                  # params needed for later dev work
                                                  # 'list_paths_of_user_modules': PVC(None,list, contains = str), # todo not implemented yet
                                                  # shared reader memory params for later dev.
                                                  # 'shared_reader_memory' :PVC(False,  bool),
                                                  # 'multiprocessing_start_method_spawn': PVC(True,  bool), # overide default of linux as fork
                                                  #'loops_over_hindcast':  PVC(0, int, min=0),  #, not implemented yet,  artifically extend run by rerun from hindcast from start, given number of times
                                                   },
                                 'reader': {'class_name': PVC(None, str, is_required=True)},
                                 'base_case_params': {},
                                 'case_list': [],
                                 }

default_case_param_template={
            'run_params' : {'user_note': PVC('No user note', str),
                                    'case_output_file_tag':          PVC(None, str),
                                    'write_tracks':             PVC(True, bool),
                                    'particle_buffer_size':     PVC(None, int, min=1),
                                    'z0':                       PVC(0.005, float, min=0.0001),  # default bottom roughness
                                    'retain_culled_part_locations': PVC(False, bool, doc_str='When particle marked dead/culled keep its position value, ie dont set position to nan so it does not appear in plots etc after death'),
                                    'duration':                 PVC(1.0 * 10 ** 300, float),
                                    'open_boundary_type' :  PVC(0, int, min=0, max=1),
                                    'block_dry_cells' :   PVC(True, bool, doc_str='Block particles moving from wet to dry cells, ie. treat dry cells as if they are part of the lateral boundary'),
              },
             'solver': {},
             'field_group_manager':{} ,
             'interpolator': {} ,
             'particle_group_manager': {},
             'tracks_writer':   {},
             'dispersion':      {},
     # class lists
             'particle_release_groups':  [],  #bbbbbbbbbbbbbbbbbbbbbbbbb

    # above classes are required classes/family members/ parameters, below are user classes held in named lists
    # below are optional user classes held in named lists
    'fields': [],  # prop calculated from other fields  on reading
    'particle_properties': [],  # user added particle properties, eg DistanceTraveled
    'status_modifiers': [],  # chnage status of particles, eg tidal stranding
    'velocity_modifiers': [],  # user added velocity effects, eg TerminalVelocity
    'trajectory_modifiers': [],  # change particle paths, eg. re-suspension
    'particle_statistics': [],  # heat map inside polygon statitics calculated on the fly
    'event_loggers': [],  # writes events files ,eg PolygonEntryExit
    'particle_concentrations': [],  # writes conctration of particles and other properties calculated on the fly.   files ,eg PolygonEntryExit

    # below stil to be develoedv
            # 'post_processing':      PDLdefaults({}), #todo after run post processing not implemented yet
            'time_varying_info' :[] # particle info, eg tide at at tide gauge, core example is particle time
    }

default_class_names={ 'solver': 'oceantracker.solver.solver.Solver',
             'field_group_manager':'oceantracker.field_group_manager.field_group_manager.FieldGroupManager' ,
             'interpolator': 'oceantracker.interpolator.interp_triangle_native_grid.InterpTriangularNativeGrid_Slayer_and_LSCgrid',
             'particle_group_manager': 'oceantracker.particle_group_manager.particle_group_manager.ParticleGroupManager',
              'tracks_writer':   'oceantracker.tracks_writer.track_writer_retangular.RectangularTrackWriter',
             'dispersion':      'oceantracker.dispersion.random_walk.RandomWalk',
             'particle_release_groups': 'oceantracker.particle_release_groups.point_release.PointRelease',
              'fields' :  'oceantracker.fields._base_field.BaseField',
              'reader': 'oceantracker.reader.generic_unstructured_reader.GenericUnstructuredReader'}

default_polygon_dict_params = {'user_polygonID': PVC(0, int, min=0), 'user_polygon_name': PVC(None, str),
                        'points': PVC([], 'vector', list_contains_type=float, is_required=True),
                               }

particle_info = {'status_flags': {'unknown': -127, 'bad_cord': -20, 'cell_search_failed': -19, 'notReleased': -10,  'dead': -2,'outside_open_boundary': -1, 'frozen': 0,
                                  'stranded_by_tide': 3,  'on_bottom': 6,  'moving': 10},
                 'known_prop_types': ['manual_update', 'from_fields','user']
                 }







