Run in parallel
===============

[This note-book is in oceantracker/tutorials_how_to/]

Running in parallel can be done using the “run with parameters”
approach, not the helper class method. Simply build a list of “cases”
parameters, then pass this list, eg. main.run(case_list). The output
files for each case will be tagged with a processor number. The number
of active cases is be limited to be one less than the number of physical
processes available. For large runs, memory to store the hindcast for
each case may cause an error. To work around this, reduce the number of
processors with the setting “processors”.

The cases can be different, eg. have different release groups etc. A
small number of settings must be the same for all cases, eg. setting
“root_output_folder” must be the same for all cases. These settings will
be taken from the first case. Warnings are given if trying to use
different values of these settings than that given in the first case.

Is is strongly recommend to run parallel cases from within a python
script, rather than notebooks which have limitations in Windows and may
result in errors.

Example parallel release groups
-------------------------------

The below example runs a separate release group as its own parallel
“case”.

To run in parallel on windows requires run to be within a if **name** ==
‘**main**’ block. iPython note books ignores if **name** == ‘**main**’
statements, thus the below will not run when within a notebook in
windows. Use in notebooks also frequently gives “file in use by another
process” errors.

This code is in file
“oceantracker/tutorials_how_to/parallel_example.py”.

.. code:: ipython3

    # oceantracker parallel demo
    # first build params used by all cases
    # without required release groups
    params_single={
        'output_file_base' :'param_test1',      # name used as base for output files
        'root_output_dir':'output',             #  output is put in dir   'root_output_dir'\\'output_file_base'
        'time_step' : 120,  #  2 min time step as seconds  
        'reader':{'input_dir': '..\\demos\\demo_hindcast',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                        'file_mask': 'demoHindcastSchism*.nc',    # the file mask of the hindcast files
                            },
        'release_groups': {}   # empty release groups to add to below for each case                 
            }
    
    # define the required release  points
    points = [  [1597682.1237, 5489972.7479],
                [1598604.1667, 5490275.5488],
                [1598886.4247, 5489464.0424],
                [1597917.3387, 5489000],
            ]
    
    # build a list of params, with one release group fot each point
    from copy import deepcopy
    
    params=[]
    for p in points:
        # build params for this case
        case_params = deepcopy(params_single) # safer to work with a copy
        
        # add one point as a release group to this case
        case_params['release_groups']['mypoint1'] = {
                                        'points':[p],  # needs to be 1, by 2 list for single 2D point
                                        'release_interval': 3600,           # seconds between releasing particles
                                        'pulse_size': 10,                   # number of particles released each release_interval
                                    }
        params.append(case_params)  # add this case to the list 
    
    # below uses params to run the list of parallel cases
    from oceantracker import main
    
    # to run parallel in windows, must put run  call  inside the below block
    if __name__ == '__main__':
    
        main.run(params)
