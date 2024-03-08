from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.util.profiling_util import available_profile_types
package_fancy_name= 'OceanTracker'
import numpy as np
from copy import deepcopy

code_version = '0.5.0.000 2024-03-07'

max_timedelta_in_seconds = 1000*365*24*3600

docs_base_url= 'https://oceantracker.github.io/oceantracker/_build/html/'

# shared settings allpy to all parallel cases
shared_settings_defaults ={
                'root_output_dir':     PVC('root_output_dir', str, doc_str='base dir for all output files'),
                'add_date_to_run_output_dir':  PVC(False, bool, doc_str='Append the date to the output dir. name to help in keeping output from different runs separate'),
                'output_file_base':    PVC('output_file_base', str,doc_str= 'The start/base of all output files and name of sub-dir of "root_output_dir" where output will be written'),
                'time_step': PVC(3600., float, min=0.01, units='sec',doc_str='Time step in seconds for all cases'),
                'screen_output_time_interval': PVC(3600., float, doc_str='Time in seconds between writing progress to the screen/log file'),
                'backtracking':        PVC(False, bool, doc_str='Run model backwards in time'),
               'regrid_z_to_uniform_sigma_levels': PVC(True, bool, doc_str='much faster 3D runs by re-griding hydo-model fields in the z to uniform sigma levels on read, based on sigma most curve z_level profile. Some hydo-model are already uniform sigma, so this param is ignored, eg ROMS'),
               # 'debug_level':               PVC(0, int,min=0, max=10, doc_str='Gives  diferent levels of debug, in development'),
                'display_grid_at_start' : PVC(False, bool, doc_str='Pause during strat up to plot the grid for checking using matplotlib, clicking om image will print a coord'),
                'dev_debug_plots': PVC(False, bool, doc_str='show any debug plot generated at give dbug_level, not for general use'),
                'debug': PVC(False, bool, doc_str= 'more info on errors'),
                'dev_debug_opt': PVC(0, int,doc_str= 'does extra checks given by integer, not for general use'),
                'minimum_total_water_depth': PVC(0.25, float, min=0.0, units='m', doc_str='Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering'),
                'write_output_files':     PVC(True,  bool, doc_str='Set to False if no output files are to be written, eg. for output sent to web'),
                'write_dry_cell_flag': PVC(True, bool,
                                doc_str='Write dry cell flag to all cells when writing particle tracks, which can be used to show dry cells on plots, currently cannot be used with nested grids '),
                'max_run_duration':    PVC(max_timedelta_in_seconds, float,units='sec',doc_str='Maximum duration in seconds of model run, this sets a maximum, useful in testing'),  # limit all cases to this duration
                'max_particles': PVC(10**9, int, min=1,  doc_str='Maximum number of particles to release, useful in testing'),  # limit all cases to this number
                'processors':          PVC(None, int, min=1,doc_str='number of processors used, if > 1 then cases in the case_list run in parallel'),
                'max_warnings':        PVC(50,    int, min=0,doc_str='Number of warnings stored and written to output, useful in reducing file size when there are warnings at many time steps'),  # dont record more that this number of warnings, to keep caseInfo.json finite
                'use_random_seed':  PVC(False,  bool,doc_str='Makes results reproducible, only use for testing developments give the same results!'),
                'numba_function_cache_size' :  PVC(4048, int, min=128, doc_str='Size of memory cache for compiled numba functions in kB'),
                'numba_cache_code': PVC(False, bool,  doc_str='Speeds start-up by caching complied Numba code on disk in root output dir. Can ignore warning/bug from numba "UserWarning: Inspection disabled for cached code..."'),
                'multiprocessing_case_start_delay': PVC(None, float, min=0., doc_str='Delay start of each case run parallel, to reduce congestion reading first hydo-model file'),  # which large numbers of case, sometimes locks up at start al reading same file, so ad delay
                'profiler': PVC('oceantracker', str, possible_values=available_profile_types,
                                                       doc_str='in development- Default oceantracker profiler, writes timings of decorated methods/functions to run/case_info file use of other profilers in development and requires additional installed modules '),
                'EPSG_code_metres_grid': PVC(None, int,
                                 doc_str='If hydro-model has lon_lat coords, then grid is converted to this meters system. For codes see https://epsg.io/. eg EPSG for NZ Transverse Mercator use 2193. Default grid is UTM'),

                }



#  these setting can be different for each case
case_settings_defaults ={
            'user_note': PVC('No user note', str,doc_str='Any run note to store in case info file'),
            'case_output_file_tag':     PVC(None, str,doc_str='insert this tag into output files name for each case, for parallel runs this is set to C000, C001...'), #todo make this only settable in a case, caselist params?
            'write_tracks':             PVC(True, bool, doc_str='Flag if "True" will write particle tracks to disk. For large runs and statistics done on the fly, is normally set to False to reduce output volumes'),
            'z0':                       PVC(0.005, float, units='m', doc_str='Bottom roughness in meters, used for tolerance and log layer calcs. ', min=0.0001),  # default bottom roughness
            'water_density':  PVC(1025., float, units='kg/m^3', doc_str='Water density , default is seawater, an example of use is in calculating friction velocity from bottom stress, ', min=900.),
            'open_boundary_type' :  PVC(0, int, min=0, max=1,doc_str='new- open boundary behaviour, only current option=1 is disable particle, only works if open boundary nodes  can be read or inferred from hydro-model, current schism using hgrid file, and inferred ROMS '),
            'block_dry_cells' :   PVC(True, bool, doc_str='Block particles moving from wet to dry cells, ie. treat dry cells as if they are part of the lateral boundary'),
            'use_A_Z_profile': PVC(True, bool, doc_str='Use the hydro-model vertical turbulent diffusivity profiles for vertical random walk (more realistic) instead of constant value (faster), if profiles are in the file'),
            'include_dispersion': PVC(True, bool, doc_str='Include random walk, allows it to be turned off if needed for applications like Lagrangian coherent structures '),

    #  #'loops_over_hindcast':  PVC(0, int, min=0),  #, not implemented yet,  artifically extend run by rerun from hindcast from start, given number of times

            }
core_class_list=['reader',
                'solver',
                'field_group_manager',
               'interpolator',
                'particle_group_manager',
                'tracks_writer',
                'dispersion',
                 'tidal_stranding',
                'resuspension',
                 'integrated_model' # this is here as ther can be only one at a time
                 ]

default_classes_dict = dict( solver= 'oceantracker.solver.solver.Solver',
                        particle_properties='oceantracker.particle_properties._base_particle_properties.ParticleProperty',
                        time_varying_info='oceantracker.time_varying_info._base_time_varying_info.TimeVaryingInfo',
                        field_group_manager='oceantracker.field_group_manager.field_group_manager.FieldGroupManager',
                        particle_group_manager= 'oceantracker.particle_group_manager.particle_group_manager.ParticleGroupManager',
                        tracks_writer = 'oceantracker.tracks_writer.track_writer_compact.CompactTracksWriter',
                        interpolator = 'oceantracker.interpolator.interp_triangle_native_grid.InterpTriangularNativeGrid_Slayer_and_LSCgrid',
                        dispersion_random_walk = 'oceantracker.dispersion.random_walk.RandomWalk',
                        dispersion_random_walk_varyingAz ='oceantracker.dispersion.random_walk_varyingAz.RandomWalkVaryingAZ',
                        resuspension_basic = 'oceantracker.resuspension.resuspension.BasicResuspension',
                        tidal_stranding = 'oceantracker.tidal_stranding.tidal_stranding.TidalStranding',
                        release_groups = 'oceantracker.release_groups.point_release.PointRelease',
                        field_reader='oceantracker.fields._base_field.ReaderField',
                        field_custom='oceantracker.fields._base_field.CustomField',
                        field_friction_velocity_from_bottom_stress='oceantracker.fields.friction_velocity.FrictionVelocityFromBottomStress',
                        field_friction_velocity_from_near_sea_bed_velocity='oceantracker.fields.friction_velocity.FrictionVelocityFromNearSeaBedVelocity',
                        field_A_Z_profile_vertical_gradient='oceantracker.fields.field_vertical_gradient.VerticalGradient',

                        )

class_dicts_list=[ # class dicts which replace lists
            #'pre_processing',
            'release_groups' ,
            'fields',  # user fields calculated from other fields  on reading
            'particle_properties',  # user added particle properties, eg DistanceTraveled
            'velocity_modifiers',  # user added velocity effects, eg TerminalVelocity
            'trajectory_modifiers',  # change particle paths, eg. re-suspension
            'particle_statistics',  # heat map inside polygon statistics calculated on the fly
            'particle_concentrations',  # writes concentration of particles and other properties calculated on the fly.   files ,eg PolygonEntryExit
            'nested_readers',
            'event_loggers',  # writes events files ,eg PolygonEntryExit
            # below still to be developed
            # 'post_processing':      PDLdefaults({}), #todo after run post processing not implemented yet
            'time_varying_info', # particle info,eg. time,or  tide at at tide gauge, core example is particle time

            ]


default_polygon_dict_params = {'user_polygonID': PVC(0, int, min=0),
                'name': PVC(None, str),
                'points': PCC( None,is_required=True, doc_str='Points making up the polygon as, N by 2 or 3 list of locations where particles are released. eg for 2D ``[[25,10],[23,2],....]``, must be convertible into N by 2 or 3 numpy array')
                               }

particle_info = {'status_flags': {'unknown': -128, 'bad_cord': -20, 'cell_search_failed': -19,
                                  'notReleased': -10,
                                  'dead': -2,
                                  'outside_open_boundary': -1,
                                  'stationary': 0,
                                  'stranded_by_tide': 3,  'on_bottom': 6,  'moving': 10},
                 'known_prop_types': ['manual_update', 'from_fields','user']

                 }
particle_info['status_keys_list']= list(particle_info['status_flags'].keys()) # possible values for checking user input
# interp cell find flags

cell_search_status_flags = dict(ok =0, outside_domain=1 ,blocked_domain=-5, blocked_dry_cell=-4, bad_cord=-20, failed=-30)

# default reader classes used by auto-detection of file type
known_readers ={'schisim': 'oceantracker.reader.schism_reader.SCHISMreaderNCDF',
                'schisim_v5':    'oceantracker.reader.schism_reader_v5.SCHISMreaderNCDFv5',
                 'fvcom': 'oceantracker.reader.FVCOM_reader.unstructured_FVCOM',
                 'roms': 'oceantracker.reader.ROMS_reader.ROMsNativeReader',
                 'delft3d_fm': 'oceantracker.reader.dev_delft_fm.DELFTFM',
                 'generic': 'oceantracker.reader.generic_ncdf_reader.GenericNCDFreader',
                }


large_float=1.0E32

# node types for hydro model
node_types= dict(interior = 0,island_boundary = 1, domain_boundary= 2, open_boundary=3, land = 4)

# TODO LIST
# todo for version 0.41
    #TODO BUGS
        #todo error handling and log file permission errors when reunning cells in note books

    #TODO PARAMETERS

    # TODO DOCUMENTATION

    # TODO STRUCTURE
        # todo remove writing to file or mp4, and show how to save it by example???
        #todo plots to return figure handle to allow adding plots, on no show
        # work only with triangle face values, better for vel bc etc , group feils in array of strutures for faseter acess. No read cost if async reader

    # TODO SIMPLIFY

    # TODO input checking
        #todo check class being added is child of given role
        # todo make it so user can add own Az profile class!! setup default classes dict for different type beyond standard

    #TODO Nice to haves
        # todo get rid of info[points], just alter params points
        # todo field type reader, derived from reader field ,  or custom
        # todo simplfy run in depth average mode and depth averaing fields, swap to explict depth aver tags field names??
        # todo check time_step default is hindcast time step
        # todo read write polygons from geo-jsons, release groups poly stats
        # todo add units to Parameter check and show in user docs
        # todo add message logging to post processing
        # todo add read case info file with not found errors
        # todo  add doc string for improtant methods and classes
        # todo aviod netcdf chunk size erors max time steps per file option?
        # todo remove blanks from class papam keys

#TODO checks
    #todo setup of using AZ profiles from hindcast
    # todo note if using hindcast tiem step

#TODO FASTER STARTUP
    # todo line profile reader buffer fill to improve speed of copys, eg np.copyto()

# TODO MODELS
    # todo design and make base class
    # todo make template
    # todo add get time and date as methods, plus other useful basics, get particles in the bufferS

# TODO TUTORIALS
    # todo Reader param and adding fields
    # todo dispersion resupension

#TODO PERFORMANCE
        # todo kernal forms of hori/vert walk
        # todo kernal form of water vel interpolator
        # todo kernal RK solver
        # todo fraction to read use ::10 form to only read load a fraction of track/timestats time steps? can this work in compact filesode?
        # todo indepth look at circle test results
# TODO STRUCTURE
    # todo hyperlinks to online docs where useful
    #todo much cleaner to  do residence times/stats for all polygon release groups given!
            #todo or better get user to define polygons like polygon statistcs, or merge with polygon stats
    # todo use update_interval everywhere as parmateter fo periodic actions
    # todo revert to index zero for all IDs and data loading
    # todo show defauls on param eros?
    # todo move writing to first case and make it a fieldgroup method
    # todo move particle comparison methods to wrapper methods
    # todo full use of initial setup, final set up and update with timers
    # todo get rid of used nseq in favour of instanceID
    # todo add check for use of known class prop types, eg 'maunal_update'
    # todo compact model only with self expanding buffer??
    # todo enable on the fly depth avering of fields if running depth avearged,
    #  currently disabled in base reader.setup_reader_fields
    # todo only have compact mode tracks, and add a convert at end if requested
    # todo remove depth range stats and make depth range part of stats
    # todo add part property from field wwhich checks if field exists
    # todo retain on the fly depth averaging?

# TODO IMPROVEMENTS
    # todo allow numpy arrays in "array" type
    # todo smart way to tell class_dict item does not belong to that type, without class name
    # todo allow isostr, datetime, np.dateime64 for dates
    # todo allow user to give "class" instead of class_name ( not an insatnce)
    # todo add run_dir option to all output reads
    # todo rotate particle relese polygns to reduce searches for points in side
    # todo extend inside polygon to have list of cells fully inside plogon for faster serach
    # todo integerise all periodic evets to model time steps
    # todo to enable mutliple readers,  do all particle tracking in lon-lat
    # todo replace retain_culled_part_locations with use of "last known location",
    #  todo and add "show_dead_particles" option to tracks plotting
    #todo plot routines using message logger
    #todo merge residence time into polygon stats?
    #todo add variance calc to on fly stats particle prop, by adding sum of squares heatmap/ploygon
    # todo read geojson polygons
    # todo free run through statr/gaps/ends when no active particles
    # todo read-ahead async reader
    # todo add CPC for check class parameters??
    # todo add default class instance checking
    #todo merge water depth range selection into all stats
    # more consisted crumb use for all message logger errors to aid debug
    #todo merge demo plots back into demos
    #todo particle property, fill value is fill value, not intial, value, put in netcdf, compact reader pyhton and matlab, than fills matrix
            #status to have not released before cetaion, dead afet death  in compact reader,
            #  ensures statatus is not released when filling upper left of reytangular matrix
    #todo say why no particles found, eg outside domain etc
 #todo Simplify
    # todo set up of tracks set up op of patricle params, no kwargs. based on prrop para, time varyinging,
        #  nice to have tme varying write at end
    #todo get rid of base tracks writer???
    #todo conver LSC grid to S layer on read, using smallest number of layers, while keeping bootom log layer?
    #todo tidy up particle concentrations, add grid data to netcdf

# TODO FUTURE
    # todo Kernal RK steps
    #todo aysc reader
    #todo FIELD group to manage readers/interp in multi-reader future
        # todo  move reader opertions to field group mangager to allow for future with multiple readers
        # todo attach reader/interp to each  field instance to
    # todo support for lat long inout/output
    # todo  as a utility set up reading geojson/ shapely polygons and show example
    # todo grid outline file as geojson?


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
    # field type reader, derived from reader field ,  or custom
    # simplfy run in depth average mode and depth averaing fields, swap to explict depth aver tags field names??

#TODO ISSUES
    #  todo in making custom fields how do i know fiels have been added before i use i
    #  todo how doi know part prop which depend on others are up to date before use




