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
    
    ot.add_class('reader',input_dir= '../demos/demo_hindcast/schsim3D',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                          file_mask=  'demo_hindcast_schisim3D*.nc')  # hindcast file mask
    
    # now put a release group with one point into case list
    # define the required release  points
    points = [  [1597682.1237, 5489972.7479],
                [1598604.1667, 5490275.5488],
                [1598886.4247, 5489464.0424],
                [1597917.3387, 5489000],
            ]
    # run each point release in parrallel
    for n, p in enumerate(points):
        # add a release group with one point to case "n"
        ot.add_class('release_groups',
                    case=n, # this adds release group to the n'th case to run in //
                    name ='mypoint'+str(n), # optional name for each group
                    points= p,  # needs to be 1, by 2 list for single 2D point
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

    helper ----------------------------------------------------------------------
    helper Starting OceanTracker helper class
    helper   - Starting run using helper class
    Main      Python version: 3.11.9 | packaged by conda-forge | (main, Apr 19 2024, 18:27:10) [MSC v.1938 64 bit (AMD64)]
    Main >>> Warning: Oceantracker is not yet compatible with Python 3.11, as not all imported packages have been updated, eg netcdf4
    Main ----------------------------------------------------------------------
    Main OceanTracker starting main:
    Main     Starting package set up
    Main         -  Built OceanTracker package tree,	  0.603 sec
    Main         -  Built OceanTracker sort name map,	  0.000 sec
    Main     -  Done package set up to setup ClassImporter,	  0.603 sec
    Main >>> Warning: Deleted contents of existing output dir
    Main Output is in dir "f:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\parallel_test2"
    Main       hint: see for copies of screen output and user supplied parameters, plus all other output
    Main     >>> Note: to help with debugging, parameters as given by user  are in "user_given_params.json"
    Main ----------------------------------------------------------------------
    Main  OceanTracker version 0.50.0010-2024-03-30 - preliminary setup
    Main   - Found input dir "../demos/demo_hindcast/schsim3D"
    Main   - found hydro-model files of type  "SCHISM"
    Main Cataloging hindcast with 1 files in dir ../demos/demo_hindcast/schsim3D
    Main     -  Cataloged hydro-model files/variables in time order,	  0.008 sec
    Main >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    Main     -  sorted hyrdo-model files in time order,	  0.034 sec
    Main   - oceantracker:multiProcessing: processors:4
    Main   - parallel pool complete
    End --- Summary ----------------------------------------------------------
    End     >>> Note: Run summary with case file names in "*_runInfo.json"
    End     >>> Note: to help with debugging, parameters as given by user  are in "user_given_params.json"
    End >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    End     >>> Note: Run summary with case file names in "*_runInfo.json"
    End >>> Warning: Oceantracker is not yet compatible with Python 3.11, as not all imported packages have been updated, eg netcdf4
    End >>> Warning: Deleted contents of existing output dir
    End ----------------------------------------------------------------------
    End ----------------------------------------------------------------------
    End OceanTracker summary:  elapsed time =0:00:17.406447
    End       Cases -   0 errors,   0 warnings,  12 notes, check above
    End       Main  -   0 errors,   2 warnings,   3 notes, check above
    End   Output in None
    End ----------------------------------------------------------------------
    




Run parallel using param. dicts.
--------------------------------

.. code:: ipython3

    # oceantracker parallel demo, run different release groups as parallel processes
    from oceantracker.main import OceanTracker
    
    # make instance of oceantracker to use to set parameters using code, then run
    ot = OceanTracker()
    
    # first build base case, params used for all cases
    params=dict(debug =True,
        output_file_base= 'parallel_test1',      # name used as base for output files
        root_output_dir= 'output',             #  output is put in dir   'root_output_dir'/'output_file_base'
        time_step = 120,  #  2 min time step as seconds 
        ) 
    params['reader']= dict(input_dir= '../demos/demo_hindcast/schsim3D',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                          file_mask=  'demo_hindcast_schisim3D*.nc')
    
    # define the required release  points
    points = [  [1597682.1237, 5489972.7479],
                [1598604.1667, 5490275.5488],
                [1598886.4247, 5489464.0424],
                [1597917.3387, 5489000],
            ]
    
    # build a list of params for each case, with one release group for each point
    params['case_list'] =[]
    for n,p in enumerate(points):
        # add one point as a release group to this case
        d = dict( name= 'mypoint'+str(n),# better to give release group a unique name
                points= [p],  # needs to be 1, by 2 list for single 2D point
                release_interval= 3600,           # seconds between releasing particles
                pulse_size= 10,                   # number of particles released each release_interval
                )
        case_param =dict(release_groups=[d]) # release group list of one or more releases
        params['case_list'].append(case_param)
    
    # to run parallel in windows, must put run  call  inside the below "if __name__ == '__main__':" block
    if __name__ == '__main__':
    
        # run as parallel set of cases
        #    by default uses two less than the number of physical processors at one time, use setting "processors"
        case_info_files= main.run(params)
        
        # NOTE for parallel runs case_info_files is a list, one for each case run
        # so to load track files use    
        # tracks = load_output_files.load_track_data(case_info_files[n])
        #   where n is the case number 0,1,2...
        


.. parsed-literal::

    helper ----------------------------------------------------------------------
    helper Starting OceanTracker helper class
    Main      Python version: 3.11.9 | packaged by conda-forge | (main, Apr 19 2024, 18:27:10) [MSC v.1938 64 bit (AMD64)]
    Main >>> Warning: Oceantracker is not yet compatible with Python 3.11, as not all imported packages have been updated, eg netcdf4
    Main ----------------------------------------------------------------------
    Main OceanTracker starting main:
    Main     Starting package set up
    Main         -  Built OceanTracker package tree,	  0.010 sec
    Main         -  Built OceanTracker sort name map,	  0.000 sec
    Main     -  Done package set up to setup ClassImporter,	  0.010 sec
    Main >>> Warning: Deleted contents of existing output dir
    Main Output is in dir "f:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\parallel_test1"
    Main       hint: see for copies of screen output and user supplied parameters, plus all other output
    Main     >>> Note: to help with debugging, parameters as given by user  are in "user_given_params.json"
    Main ----------------------------------------------------------------------
    Main  OceanTracker version 0.50.0010-2024-03-30 - preliminary setup
    Main   - Found input dir "../demos/demo_hindcast/schsim3D"
    Main   - found hydro-model files of type  "SCHISM"
    Main Cataloging hindcast with 1 files in dir ../demos/demo_hindcast/schsim3D
    Main     -  Cataloged hydro-model files/variables in time order,	  0.009 sec
    Main >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    Main     -  sorted hyrdo-model files in time order,	  0.024 sec
    Main   - oceantracker:multiProcessing: processors:4
    Main   - parallel pool complete
    End --- Summary ----------------------------------------------------------
    End     >>> Note: Run summary with case file names in "*_runInfo.json"
    End     >>> Note: to help with debugging, parameters as given by user  are in "user_given_params.json"
    End >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    End     >>> Note: Run summary with case file names in "*_runInfo.json"
    End >>> Warning: Oceantracker is not yet compatible with Python 3.11, as not all imported packages have been updated, eg netcdf4
    End >>> Warning: Deleted contents of existing output dir
    End ----------------------------------------------------------------------
    End ----------------------------------------------------------------------
    End OceanTracker summary:  elapsed time =0:00:16.965963
    End       Cases -   0 errors,   0 warnings,  12 notes, check above
    End       Main  -   0 errors,   2 warnings,   3 notes, check above
    End   Output in None
    End ----------------------------------------------------------------------
    
