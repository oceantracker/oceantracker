#!/usr/bin/env python
# coding: utf-8

# # Run in parallel
# 
# [This note-book is in oceantracker/tutorials_how_to/]
# 
# Running in parallel can be done using the "run with parameter dict." approach, or the helper class method.   Both build a base_case, which is the parameter defaults for each case, plus a list of  "cases" parameters specific to each parallel case. The output files for each case will be tagged with a case number, 0-n. The number of computationally active cases is be limited to be one less than the number of physical processes available.   
# 
# The cases can be different, eg. have different release groups etc. A small number of settings must be the same for all cases, eg. setting "root_output_folder" must be the same for all cases. These settings will be taken from the base case.  Warnings are given if trying to use different values within case parameters. 
# 
# Is is strongly recommend to run parallel cases from within a python script, rather than notebooks which have limitations in Windows and may result in errors.
# 
# Note: For large runs, memory to store the hindcast for each case may cause an error. To work around this, reduce the  size of the hindcast buffer, ("reader" class parameter "time_buffer_size"), or reduce the number of processors (setting "processors").
# 
# ## Example parallel release groups
# 
# The below example runs a separate release group as its own parallel "case". 
# 
# To run in parallel on windows requires the run to be within a if __name__ == '__main__' block.  iPython note books ignores if __name__ == '__main__' statements, thus the below may not run when within a notebook in windows.  Use in notebooks also frequently gives "file in use by another process" errors.
# 
# To avoid  this run parallel case as a script, eg. code in file  "oceantracker/tutorials_how_to/P_running_cases_in_parallel.py".
# 
# ## Run parallel using param. dicts.

# In[2]:


# oceantracker parallel demo, run different release groups as parallel processes
from oceantracker import main

# first build base case, params used for all cases
base_case={
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
    case_param = main.param_template()
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
    main.run_parallel(base_case, case_list)


# ## Run parallel with helper class

# In[3]:


# run in parallel using helper class method
from oceantracker.main import OceanTracker

ot = OceanTracker()
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
                name ='mypoint'+str(n),
                points= [p],  # needs to be 1, by 2 list for single 2D point
                release_interval= 3600,           # seconds between releasing particles
                pulse_size= 10,                   # number of particles released each release_interval
                case=n) # this adds release group to the nth case to run in //

# to run parallel in windows, must put run  call  inside the below "if __name__ == '__main__':" block
if __name__ == '__main__':
    # base case and case_list exist as attributes ot.params and ot.case_list
    # run as parallel set of cases
    ot.run()

