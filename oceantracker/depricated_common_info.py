from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker import definitions
# shared settings allpy to all parallel cases
shared_settings_defaults ={
                'root_output_dir':     PVC('root_output_dir', str, doc_str='base dir for all output files'),
                'add_date_to_run_output_dir':  PVC(False, bool, doc_str='Append the date to the output dir. name to help in keeping output from different runs separate'),
                'output_file_base':    PVC('output_file_base', str,doc_str= 'The start/base of all output files and name of sub-dir of "root_output_dir" where output will be written'),
                'time_step': PVC(3600., float, min=0.1, units='sec',doc_str='Time step in seconds for all cases'),
                'screen_output_time_interval': PVC(3600., float, doc_str='Time in seconds between writing progress to the screen/log file'),
                'backtracking':        PVC(False, bool, doc_str='Run model backwards in time'),
               'regrid_z_to_uniform_sigma_levels': PVC(True, bool, doc_str='much faster 3D runs by re-griding hydo-model fields in the z to uniform sigma levels on read, based on sigma most curve z_level profile. Some hydo-model are already uniform sigma, so this param is ignored, eg ROMS'),
               # 'debug_level':               PVC(0, int,min=0, max=10, doc_str='Gives  diferent levels of debug, in development'),
                'display_grid_at_start' : PVC(False, bool, doc_str='Pause during strat up to plot the grid for checking using matplotlib, clicking om image will print a coord'),
                'dev_debug_plots': PVC(False, bool, doc_str='show any debug plot generated at give dbug_level, not for general use'),
                'debug': PVC(False, bool, doc_str= 'more info on errors'),
                'dev_debug_opt': PVC(0, int,doc_str= 'does extra checks given by integer, not for general use'),
                'minimum_total_water_depth': PVC(0.25, float, min=0.0, units='m', doc_str='Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering'),
                #'write_output_files':     PVC(True,  bool, doc_str='Set to False if no output files are to be written, eg. for output sent to web'),
                'write_dry_cell_flag': PVC(True, bool,
                                doc_str='Write dry cell flag to all cells when writing particle tracks, which can be used to show dry cells on plots, currently cannot be used with nested grids '),
                'max_run_duration':    PVC(definitions.max_timedelta_in_seconds, float,units='sec',doc_str='Maximum duration in seconds of model run, this sets a maximum, useful in testing'),  # limit all cases to this duration
                'max_particles': PVC(10**9, int, min=1,  doc_str='Maximum number of particles to release, useful in testing'),  # limit all cases to this number
                'processors':          PVC(None, int, min=1,doc_str='number of processors used, if > 1 then cases in the case_list run in parallel'),
                'max_warnings':        PVC(50,    int, min=0,doc_str='Number of warnings stored and written to output, useful in reducing file size when there are warnings at many time steps'),  # dont record more that this number of warnings, to keep caseInfo.json finite
                'USE_random_seed':  PVC(False,  bool,doc_str='Makes results reproducible, only use for testing developments give the same results!'),
                'NUMBA_function_cache_size' :  PVC(4048, int, min=128, doc_str='Size of memory cache for compiled numba functions in kB'),
                'NUMBA_cache_code': PVC(False, bool,  doc_str='Speeds start-up by caching complied Numba code on disk in root output dir. Can ignore warning/bug from numba "UserWarning: Inspection disabled for cached code..."'),
                'multiprocessing_case_start_delay': PVC(None, float, min=0., doc_str='Delay start of each case run parallel, to reduce congestion reading first hydo-model file'),  # which large numbers of case, sometimes locks up at start al reading same file, so ad delay
                #'profiler': PVC('oceantracker', str, possible_values=available_profile_types,
               #                                        doc_str='in development- Default oceantracker profiler, writes timings of decorated methods/functions to run/case_info file use of other profilers in development and requires additional installed modules '),
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
            'include_dispersion': PVC(True, bool, doc_str='Include random walk, allows it to be turned off if needed for applications like Lagrangian coherent structures'),
    #  #'loops_over_hindcast':  PVC(0, int, min=0),  #, not implemented yet,  artifically extend run by rerun from hindcast from start, given number of times
      }


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


