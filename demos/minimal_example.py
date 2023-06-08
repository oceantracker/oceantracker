# minimal_example.py
#-------------------
from oceantracker import main

# create parameters as a dictionary
params= {'shared_params' : {'output_file_base' :'minimal_example',
                           'root_output_dir':'output'},
    'reader': { 'class_name': 'oceantracker.reader.schism_reader.SCHSIMreaderNCDF',
                'input_dir': 'demo_hindcast',
                'file_mask': 'demoHindcastSchism3D.nc',
                },
    'base_case_params' : { 'solver': {'n_sub_steps': 12}, #not required but runs 5min steps in 1hr time step hindcast
                'release_groups':
                      [{'points': [[1595000, 5483300, -2],[1596000, 5487200, -2] ], # two 3D release locations
                        'pulse_size': 10, 'release_interval': 3600}
                       ]
                           }
        }

# run OceanTracker to give track output files
runInfo_file_name, has_errors = main.run(params)

# output now in folder output/minimal_example

# below is optional code for plotting
#-------------------------------------
from oceantracker.post_processing.plotting.plot_tracks import animate_particles, plot_tracks
from oceantracker.post_processing.read_output_files.load_output_files import get_case_info_file_from_run_file, load_particle_track_vars

# find case_info_file name, to used to locate output for the caseInfo file
case_info_file_name = get_case_info_file_from_run_file(runInfo_file_name)

# read particle tracks for plotting
track_data = load_particle_track_vars(case_info_file_name)

# plot tracks
anim = plot_tracks(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                            plot_file_name='output\\minimal_example.jpeg')

# animate particles
anim = animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                         title='Minimal example of OceanTracker with 3D point release',
                         movie_file='output\\minimal_example.mp4', show_dry_cells=True)

