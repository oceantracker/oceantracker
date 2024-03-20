Run in parallel
===============

[This note-book is in oceantracker/tutorials_how_to/]

Running in parallel can be done using the “run with parameter dict.”
approach, or the helper class method. Both build a base_case, which is
the parameter defaults for each case, plus a list of “cases” parameters
specific to each parallel case. The output files for each case will be
tagged with a case number, 0-n. The number of computationally active
cases is be limited to be one less than the number of physical processes
available.

The cases can be different, eg. have different release groups etc. A
small number of settings must be the same for all cases, eg. setting
“root_output_folder” must be the same for all cases. These settings will
be taken from the base case. Warnings are given if trying to use
different values within case parameters.

Is is strongly recommend to run parallel cases from within a python
script, rather than notebooks which have limitations in Windows and may
result in errors.

Note: For large runs, memory to store the hindcast for each case may
cause an error. To work around this, reduce the size of the hindcast
buffer, (“reader” class parameter “time_buffer_size”), or reduce the
number of processors (setting “processors”).

Example parallel release groups
-------------------------------

The below example runs a separate release group as its own parallel
“case”.

To run in parallel on windows requires the run to be within a if
**name** == ‘**main**’ block. iPython note books ignores if **name** ==
‘**main**’ statements, thus the below may not run when within a notebook
in windows. Use in notebooks also frequently gives “file in use by
another process” errors.

To avoid this run parallel case as a script, eg. code in file
“oceantracker/tutorials_how_to/P_running_cases_in_parallel.py”.

Run parallel with helper class
------------------------------

.. code:: ipython3

    # run in parallel using helper class method
    from oceantracker import main
    from  importlib import reload # force a reload to get around notebooks single name space
    reload(main)
    
    
    ot = main.OceanTracker()
    
    # setup base case
    # by default settings and classes are added to base case
    ot.settings(output_file_base= 'parallel_test2',      # name used as base for output files
        root_output_dir='output',             #  output is put in dir   'root_output_dir'/'output_file_base'
        time_step = 120,  #  2 min time step as seconds  
        )
    
    ot.add_class('reader',
                input_dir='../demos/demo_hindcast',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                file_mask= 'demoHindcastSchism*.nc',    # the file mask of the hindcast files
                )
    
    # now put a release group with one point into case list
    # define the required release  points
    points = [  [1597682.1237, 5489972.7479],
                [1598604.1667, 5490275.5488],
                [1598886.4247, 5489464.0424],
                [1597917.3387, 5489000],
            ]
    
    # build a list of params for each case, with one release group fot each point
    for n, p in enumerate(points):
        # add a release group with one point to case "n"
        ot.add_class('release_groups',
                    case=n, # this adds release group to the n'th case to run in //
                    name ='mypoint'+str(n), # must have unique name for each group
                    points= [p],  # needs to be 1, by 2 list for single 2D point
                    release_interval= 3600,           # seconds between releasing particles
                    pulse_size= 10,                   # number of particles released each release_interval
                    )
    
    # to run parallel in windows, must put run  call  inside the below "if __name__ == '__main__':" block
    if __name__ == '__main__':
        # base case and case_list exist as attributes ot.params and ot.case_list
        # run as parallel set of cases
        case_info_files= ot.run()
    
            
        # NOTE for parallel runs case_info_files is a list, one for each case run
        # so to load track files use    
        # tracks = load_output_files.load_track_data(case_info_files[n])
        #   where n is the case number 0,1,2...


.. parsed-literal::

    helper --------------------------------------------------------------------------
    helper Starting OceanTracker helper class
    helper   - Starting run using helper class
    Main --------------------------------------------------------------------------
    Main OceanTracker starting main:
    Main   - Output dir set up.
    Main >>> Warning: Deleted contents of existing output dir
    Main     >>> Note: to help with debugging, parameters as given by user  are in "parallel_test2_raw_user_params.json"
    Main   Output is in dir "e:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\parallel_test2"
    Main         hint: see for copies of screen output and user supplied parameters, plus all other output
    Main --------------------------------------------------------------------------
    Main  OceanTracker version 0.5.0.000 2024-03-07 - preliminary setup
    Main      Python version: 3.10.10 | packaged by conda-forge | (main, Mar 24 2023, 20:00:38) [MSC v.1934 64 bit (AMD64)]
    Main   - Found input dir "../demos/demo_hindcast"
    Main   - found hydro-model files of type  "SCHISIM"
    Main       -  sorted hyrdo-model files in time order,	  0.026 sec
    Main   -  oceantracker:multiProcessing: processors:24
    Main   - parallel pool complete
    Main     >>> Note: run summary with case file names   "parallel_test2_runInfo.json"
    Main     >>> Note: to help with debugging, parameters as given by user  are in "parallel_test2_raw_user_params.json"
    Main     >>> Note: run summary with case file names   "parallel_test2_runInfo.json"
    Main >>> Warning: Deleted contents of existing output dir
    Main >>> Warning: Deleted contents of existing output dir
    Main --------------------------------------------------------------------------
    Main OceanTracker summary:  elapsed time =0:00:18.767578
    Main       Cases -   0 errors,   4 warnings,  20 notes, check above
    Main       Helper-   0 errors,   1 warnings,   2 notes, check above
    Main       Main  -   0 errors,   1 warnings,   2 notes, check above
    Main --------------------------------------------------------------------------
    




Run parallel using param. dicts.
--------------------------------

.. code:: ipython3

    # oceantracker parallel demo, run different release groups as parallel processes
    from oceantracker import main
    from  importlib import reload # force a reload to get around notebooks single name space
    reload(main)
    
    # first build base case, params used for all cases
    base_case={ "debug" :True,
        'output_file_base' :'parallel_test1',      # name used as base for output files
        'root_output_dir':'output',             #  output is put in dir   'root_output_dir'/'output_file_base'
        'time_step' : 120,  #  2 min time step as seconds  
        'reader':{'input_dir': '../demos/demo_hindcast',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                    'file_mask': 'demoHindcastSchism*.nc',    # the file mask of the hindcast files
            },
            }
    
    # define the required release  points
    points = [  [1597682.1237, 5489972.7479],
                [1598604.1667, 5490275.5488],
                [1598886.4247, 5489464.0424],
                [1597917.3387, 5489000],
            ]
    
    # build a list of params for each case, with one release group fot each point
    case_list=[]
    for n,p in enumerate(points):
        case_param = {}
        # add one point as a release group to this case
        case_param['release_groups']['mypoint'+str(n)] = {  # better to give release group a unique name
                                                'points':[p],  # needs to be 1, by 2 list for single 2D point
                                                'release_interval': 3600,           # seconds between releasing particles
                                                'pulse_size': 10,                   # number of particles released each release_interval
                                    }
        case_list.append(case_param)  # add this case to the list
    
    
    
    # to run parallel in windows, must put run  call  inside the below "if __name__ == '__main__':" block
    if __name__ == '__main__':
    
        # run as parallel set of cases
        #    by default uses one less than the number of physical processors at one time, use setting "processors"
        case_info_files= main.run_parallel(base_case, case_list)
        
        # NOTE for parallel runs case_info_files is a list, one for each case run
        # so to load track files use    
        # tracks = load_output_files.load_track_data(case_info_files[n])
        #   where n is the case number 0,1,2...
        


.. parsed-literal::

    Main --------------------------------------------------------------------------
    Main OceanTracker starting main:
    Main   - Output dir set up.
    Main >>> Warning: Deleted contents of existing output dir
    Main     >>> Note: to help with debugging, parameters as given by user  are in "parallel_test1_raw_user_params.json"
    Main   Output is in dir "e:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\parallel_test1"
    Main         hint: see for copies of screen output and user supplied parameters, plus all other output
    Main --------------------------------------------------------------------------
    Main  OceanTracker version 0.5.0.000 2024-03-07 - preliminary setup
    Main      Python version: 3.10.10 | packaged by conda-forge | (main, Mar 24 2023, 20:00:38) [MSC v.1934 64 bit (AMD64)]
    Main   - Found input dir "../demos/demo_hindcast"
    Main   - found hydro-model files of type  "SCHISIM"
    Main       -  sorted hyrdo-model files in time order,	  0.949 sec
    Main >>> Error: Setting root_output_dir cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting add_date_to_run_output_dir cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting output_file_base cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting time_step cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting screen_output_time_interval cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting backtracking cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting regrid_z_to_uniform_sigma_levels cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting display_grid_at_start cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting dev_debug_plots cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting debug cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting dev_debug_opt cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting minimum_total_water_depth cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting write_output_files cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting write_dry_cell_flag cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting max_run_duration cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting max_particles cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting processors cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting max_warnings cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting use_random_seed cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting numba_function_cache_size cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting numba_cache_code cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting multiprocessing_case_start_delay cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting profiler cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting EPSG_code_metres_grid cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main --------------------------------------------------------------------------
    Main >>> Fatal errors, can not continue
    Main >>> Error: Setting root_output_dir cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting add_date_to_run_output_dir cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting output_file_base cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting time_step cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting screen_output_time_interval cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting backtracking cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting regrid_z_to_uniform_sigma_levels cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting display_grid_at_start cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting dev_debug_plots cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting debug cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting dev_debug_opt cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting minimum_total_water_depth cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting write_output_files cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting write_dry_cell_flag cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting max_run_duration cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting max_particles cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting processors cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting max_warnings cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting use_random_seed cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting numba_function_cache_size cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting numba_cache_code cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting multiprocessing_case_start_delay cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting profiler cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main >>> Error: Setting EPSG_code_metres_grid cannot be set with a case
    Main       hint: Move parameter from cases to the base case
    Main       in: _run_parallel case #[0]
    Main --------------------------------------------------------------------------
    

::


    ---------------------------------------------------------------------------

    GracefulError                             Traceback (most recent call last)

    Cell In[1], line 42
         37 # to run parallel in windows, must put run  call  inside the below "if __name__ == '__main__':" block
         38 if __name__ == '__main__':
         39 
         40     # run as parallel set of cases
         41     #    by default uses one less than the number of physical processors at one time, use setting "processors"
    ---> 42     case_info_files= main.run_parallel(base_case, case_list)
    

    File e:\h_local_drive\particletracking\oceantracker\oceantracker\main.py:55, in run_parallel(base_case_params, case_list_params)
         53 def run_parallel(base_case_params, case_list_params=[{}]):
         54     ot = _OceanTrackerRunner()
    ---> 55     case_info_files  = ot.run(base_case_params, case_list_params)
         56     return case_info_files
    

    File e:\h_local_drive\particletracking\oceantracker\oceantracker\main.py:190, in _OceanTrackerRunner.run(self, params, case_list_params)
        187     case_info_file = self._run_single(params, run_builder)
        188 else:
        189     # run // case list with params as base case defaults for each run
    --> 190     case_info_file = self._run_parallel(params, case_list_params, run_builder)
        192 ml.close()
        193 return case_info_file
    

    File e:\h_local_drive\particletracking\oceantracker\oceantracker\main.py:299, in _OceanTrackerRunner._run_parallel(self, base_case_params, case_list_params, run_builder)
        293 # get any missing settings from defaults after merging with base case settings
        294 case_working_params['settings'] = merge_params_with_defaults(case_working_params['settings'],
        295                                                             common_info.all_setting_defaults, ml, crumbs=f'_run_parallel case #[{n_case}]',
        296                                                             caller=self, check_for_unknown_keys=True)
    --> 299 ml.exit_if_prior_errors(f'Errors in setting up case #{n_case}')
        300 case_run_builder = deepcopy(run_builder)
        301 case_run_builder['caseID'] = n_case
    

    File e:\h_local_drive\particletracking\oceantracker\oceantracker\util\messgage_logger.py:153, in MessageLogger.exit_if_prior_errors(self, msg)
        151     self.msg(m)
        152 self.print_line()
    --> 153 raise GracefulError('Fatal error cannot continue >>> ' +msg if msg is not None else '', hint='Check above or run.err file for errors')
    

    GracefulError: Error >> Fatal error cannot continue >>> Errors in setting up case #0
     hint= Check above or run.err file for errors

