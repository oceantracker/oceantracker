from oceantracker.util.parameter_checking import ParamValueChecker as PVC
package_fancy_name= 'OceanTracker'
import numpy as np
from copy import deepcopy

code_version = '0.4.00.003 2023-04-27'

max_timedelta_in_seconds = 1000*365*24*3600
# template for oceanTracker params, with defaults to check against
shared_params = {'user_note': PVC('No user note', str),
                 'root_output_dir':     PVC('root_output_dir', str, doc_str='base dir for all output files'),
                 'add_date_to_run_output_dir':  PVC(False, bool),
                 'output_file_base':    PVC('output_file_base', str,doc_str= 'The start/base of all output files and name of sub-dir where output will be written'),
                 'time_step': PVC(None, float, min=0.01,doc_str='Time step in seconds for all cases'),
                'screen_output_time_interval': PVC(3600., float, doc_str='Time in seconds between writing progress to the screen/log file'),
                 'backtracking':        PVC(False, bool),
                  'run_as_depth_averaged': PVC(False, bool),  # turns 3D hindcast into a 2D one
                 'debug':               PVC(False, bool),
                  'minimum_total_water_depth': PVC(0.25, float, min=0.0, doc_str='Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering'),
                  'compact_mode':        PVC(False, bool,doc_str='Periodically discard dead particles from memory, eg. those too old to be be of interest, if used track output file also has a compact format'), # discard dead/inactive particles from memory
                 'write_output_files':     PVC(True,  bool, doc_str='Set to False if no output files are to be written, eg. for output sent to web'),
                 'write_grid':          PVC(True,  bool),
                 'max_duration':        PVC(max_timedelta_in_seconds, float,doc_str='Maximun duation in seconds to run all cases. Each case can have its own duration, this sets the maximum, useful in testing'),  # limit all cases to this duration
                 'processors':          PVC(1, int, min=1,doc_str='number of processors used, if > 1 then cases in the case_list run in parallel'),
                'shared_reader_memory' : PVC(False,  bool),
                'advanced_settings': { 'max_warnings':        PVC(50,    int, min=0),  # dont record more that this number of warnings, to keep caseInfo.json finite
                              'use_numpy_random_seed':  PVC(False,  bool,doc_str='Makes results reproducible, only use for testing developments give the same results!'),
                               'numba_function_cache_size' :  PVC(1024, int, min=128),
                                'multiprocessing_case_start_delay': PVC(None, float, min=0.),  # which lareg numbers of case, sometimes locks up at start al reading same file, so ad delay
                            },
                  # params needed for later scatch_tests work
                  # 'list_paths_of_user_modules': PVC(None,list, contains = str), # todo not implemented yet
                  # shared reader memory params for later scatch_tests.
                  # 'shared_reader_memory' :PVC(False,  bool),
                  # 'multiprocessing_start_method_spawn': PVC(True,  bool), # overide default of linux as fork
                  #'loops_over_hindcast':  PVC(0, int, min=0),  #, not implemented yet,  artifically extend run by rerun from hindcast from start, given number of times
                   }
case_params= {
            'case_output_file_tag':     PVC(None, str,doc_str='insert this tag into output files name fore each case'), #todo make this only settable in a case, caselist params?
            'write_tracks':             PVC(True, bool),
            'particle_buffer_size':     PVC(None, int, min=1),
            'z0':                       PVC(0.005, float, min=0.0001),  # default bottom roughness
            'retain_culled_part_locations': PVC(False, bool, doc_str='When particle marked dead/culled keep its position value, ie dont set position to nan so it does not appear in plots etc after death'),
            'duration':                 PVC(1.0 * 10 ** 300, float),
            'open_boundary_type' :  PVC(0, int, min=0, max=1,doc_str='new- open boundary behaviour, only current option=1 is disable particle, only works if open boundary nodes  can be read or inferred from hydro-model, current schism using hgrid file, and inferred ROMS '),
            'block_dry_cells' :   PVC(True, bool, doc_str='Block particles moving from wet to dry cells, ie. treat dry cells as if they are part of the lateral boundary'),
              }

run_params = deepcopy(shared_params)
run_params.update(case_params)

core_classes= { 'reader': {},
   'solver': {},
   'field_group_manager':{},
   'interpolator': {},
    'particle_group_manager': {},
    'tracks_writer': {},
    'dispersion': {},
     'resuspension': {}}

default_class_names={
    'solver': 'oceantracker.solver.solver.Solver',
    'field_group_manager_class': 'oceantracker.field_group_manager.field_group_manager.FieldGroupManager',
    'interpolator': 'oceantracker.interpolator.interp_triangle_native_grid.InterpTriangularNativeGrid_Slayer_and_LSCgrid',
    'particle_group_manager':'oceantracker.particle_group_manager.particle_group_manager.ParticleGroupManager',
    'tracks_writer': 'oceantracker.tracks_writer.track_writer_retangular.RectangularTrackWriter',
    'dispersion': 'oceantracker.dispersion.random_walk.RandomWalk',
    'resuspension': 'oceantracker.resuspension.resuspension.BasicResuspension',
'particle_release_groups': 'oceantracker.particle_release_groups.point_release.PointRelease',
'fields' :  'oceantracker.fields._base_field.BaseField',
'reader': 'oceantracker.reader.generic_unstructured_reader.GenericUnstructuredReader'}


class_lists={ # class lists
    'particle_release_groups':  [],
    # above classes are required classes/family members/ parameters, below are user classes held in named lists
    # below are optional user classes held in named lists
    'fields': [],  # prop calculated from other fields  on reading
    'particle_properties': [],  # user added particle properties, eg DistanceTraveled
    'status_modifiers': [],  # change status of particles, eg tidal stranding
    'velocity_modifiers': [],  # user added velocity effects, eg TerminalVelocity
    'trajectory_modifiers': [],  # change particle paths, eg. re-suspension
    'particle_statistics': [],  # heat map inside polygon statistics calculated on the fly
    'event_loggers': [],  # writes events files ,eg PolygonEntryExit
    'particle_concentrations': [],  # writes concentration of particles and other properties calculated on the fly.   files ,eg PolygonEntryExit
    # below still to be developed
     # 'post_processing':      PDLdefaults({}), #todo after run post processing not implemented yet
    'time_varying_info' :[] # particle info, eg tide at at tide gauge, core example is particle time
     }

# full run params
default_param_template = deepcopy(run_params)
default_param_template.update(core_classes)
default_param_template.update(class_lists)
default_param_template['case_list_params'] = []

default_class_names={ 'solver': 'oceantracker.solver.solver.Solver',
             'field_group_manager':'oceantracker.field_group_manager.field_group_manager.FieldGroupManager' ,
             'interpolator': 'oceantracker.interpolator.interp_triangle_native_grid.InterpTriangularNativeGrid_Slayer_and_LSCgrid',
             'particle_group_manager': 'oceantracker.particle_group_manager.particle_group_manager.ParticleGroupManager',
              'tracks_writer':   'oceantracker.tracks_writer.track_writer_retangular.RectangularTrackWriter',
             'dispersion':      'oceantracker.dispersion.random_walk.RandomWalk',
             'resuspension':     'oceantracker.resuspension.resuspension.BasicResuspension',
             'particle_release_groups': 'oceantracker.particle_release_groups.point_release.PointRelease',
              'fields' :  'oceantracker.fields._base_field.BaseField',
        }

default_polygon_dict_params = {'user_polygonID': PVC(0, int, min=0), 'user_polygon_name': PVC(None, str),
                'points': PVC([], 'vector', list_contains_type=float, is_required=True,
                 doc_str='Points making up the polygon as, N by 2 or 3 list of locations where particles are released. eg for 2D ``[[25,10],[23,2],....]``, must be convertible into N by 2 or 3 numpy array')
                               }

particle_info = {'status_flags': {'unknown': -128, 'bad_cord': -20, 'cell_search_failed': -19, 'notReleased': -10,  'dead': -2,'outside_open_boundary': -1, 'frozen': 0,
                                  'stranded_by_tide': 3,  'on_bottom': 6,  'moving': 10},
                 'known_prop_types': ['manual_update', 'from_fields','user']
                 }
# default reader classes used by auto dection of file type

default_reader ={'schisim': 'oceantracker.reader.schism_reader.SCHSIMreaderNCDF',
                 'fvcom': 'oceantracker.reader.FVCOM_reader.unstructured_FVCOM',
                 'roms': 'oceantracker.reader.ROMS_reader.OMsNativeReader',}
# TODO LIST
# todo for version 0.40.01
    #TODO BUGS
            # todo stray particle location in track plots
            # todo no file found graceful exit
            # todo active count when culling?
            # todo why BC walk oo long for large steps sizes?
            # todo cope wih empty relese goups, ie non released
            # todo int32/64 signature issue in linux, eg contat mixed types
            # todo amimations ignoring release group argument?
            # todo no releses in particle buffer to small?

    #TODO TUTORIALS
        #todo parameters tut, _class, _list etc
        # todo release groups
        # todo on fly statistiics
        # todo Reader param and adding fields
        # todo resupension
        # todo random walk
        # todo
    #TODO PARAMETERS
        # todo vector type to array type
        # todo allow numpy arrays in array type
        # todo allow isostr, datetime, np.dateime64 for dates
        # todo allow user to give class_instance instead of class_name
        # todo add units to Parameter check and show in user docs
        # todo max time steps per file option?
        # todo add CPC for check class parameters??
        # todo add default class instance checking
        # todo remove leading/trailling blanks from string values
        # todo full use of  'update_interval' for stats eves and some part prop
        # todo check time_step default is hindcast time step
    # TODO DOCUMENTATION
        # todo update docs and build docs for new flat param structure
        #todo  add doc string for improtant methods and classes
        #todo hyperlinks to online docs where useful
        # add units to doc
    # TODO STRUCTURE
        # todo use update_interval everywhere as parmateter fo periodic actions
        # todo revert to index zero for all IDs and data loading
    # TODO SIMPLIFY
        #todo compact model only with self expanding buffer??
        #todo remove depth range stats and make depth range part of stats
        # add part property from field wwhich checks if field exists
        # field type reader, derived from reader feild ,  or custom
        # simplfy run in depth average mode and depth averaing fields, swap to explict depth aver tags feild names??
    #TODO MODELS
        #todo design and make base class
        # todo make template



#TODO FASTER STARTUP
    #todo add timing of start up blocks to improve setup speed
    # todo make outline builer faster by using numpy based rather than list based


#TODO PERFORMANCE
    # todo Kernal RK steps
        # todo kernal forms of hori/vert walk
        # todo kernal form of water vel interpolator
        # todo kernal RK solver

# TODO STRUCTURE
    # todo use update_interval everywhere as parmateter fo periodic actions
    # todo revert to index zero for all IDs and data loading
    # todo show defauls on param eros?
    # todo move writing to first case and make it a fieldgroup method
    # todo move particle comparison methods to wrapper methods
    # todo always give all non core part prop two buffers?
    # todo full use of initial setup, final set up and update with timers
    # todo get rid of used nseq in favour of instanceID
    # todo add check for use of known class prop types, eg 'maunal_update'


# TODO IMPROVEMENTS
    # todo rotate particle relese polygns to reduce searches for points in side
    # todo extend inside polygon to have list of cells fully inside plogon for faster serach
    # todo integerise all periodic evets to model time steps
    # todo to enable mutliple readers,  do all particle tracking in lon-lat

# TODO FUTURE
    #todo shared reader
    #todo FIELD group to manage readers/interp in multi-reader future
        # todo  move reader opertions to feild group mangager to allow for future with multiple readers
        # todo attach reader/interp to each  feild instance to
    # todo support for lat long inout/output


# TODO OUTPUT/POSTPROCESSING
    #todo put relese info in seperate json?

# TODO TESTING
    # todo test case fall vel no dispersion
    # todo reprducable  test cases with random seed to test is working

# TODO ERROR HANDLING
    #todo improve crumb trail use in paramters and elsewhere
    #todo  check in no if main for parralel case, to avoid  error on windows if running in //
    #todo case info not found on graceful exit error

# TODO SIMPLIFY
    #todo compact model only with self expanding buffer??
    #todo remove depth range stats and make depth range part of stats
    # add part property from field wwhich checks if field exists
    # field type reader, derived from reader feild ,  or custom
    # simplfy run in depth average mode and depth averaing fields, swap to explict depth aver tags feild names??

#TODO ISSUES
    #  todo in making custom fields how do i know fiels have been added before i use i
    #  todo how doi know part prop which depend on others are up to date before use




