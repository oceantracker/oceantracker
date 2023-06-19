# oceantracker parallel demo, runn diferent relese groups on parallell
from oceantracker import main

# first build base case, params used for all cases
base_case={
    'output_file_base' :'param_test1',      # name used as base for output files
    'root_output_dir':'output',             #  output is put in dir   'root_output_dir'\\'output_file_base'
    'time_step' : 120,  #  2 min time step as seconds  
    'reader':{'input_dir': '..\\demos\\demo_hindcast',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
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
for p in points:
    case_param = main.param_template()
    # add one point as a release group to this case
    case_param['release_groups']['mypoint1'] = {
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