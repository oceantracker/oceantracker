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