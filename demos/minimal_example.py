# minimal_example.py
#-------------------

from oceantracker.main import OceanTracker
# make instance of oceantracker to use to set parameters using code, then run
ot = OceanTracker()

# ot.settings method use to set basic settings
ot.settings(output_file_base='minimal_example', # name used as base for output files
            root_output_dir='output',             #  output is put in dir   'root_output_dir'\\'output_file_base'
            time_step= 120. #  2 min time step as seconds
            )
# ot.set_class, sets parameters for a named class
ot.add_class('reader', input_dir= '..\\demos\\demo_hindcast',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                      file_mask=  'demoHindcastSchism*.nc')  # hindcast file mask
# add  release locations from two points,
#               (ie locations where particles are released at the same times and locations)
#  note : can add multiple release groups
ot.add_class('release_groups', name ='my_release_point', # user must provide a name for release group
                     points= [[1595000, 5482600],
                              [1599000, 5486200]],      # must be an N by 2 or 3 or list, convertible to a numpy array
                    release_interval= 3600,           # seconds between releasing particles
                    pulse_size= 10,                   # number of particles released each release_interval
                    )

from oceantracker.util import json_util,yaml_util
from os import path
json_util.write_JSON(path.join('demo_param_files', 'minimal_example.json'), ot.params)
yaml_util.write_YAML(path.join('demo_param_files', 'minimal_example.yaml'), ot.params)

case_info_file_name = ot.run()
# case_info_file_name is a json file with useful ingo for post processing, eg output file names
# output now in folder output/minimal_example

# below is optional code for plotting
#-------------------------------------
from plot_oceantracker.plot_tracks import animate_particles, plot_tracks
from read_oceantracker.python.load_output_files import load_track_data

# read particle tracks for plotting
track_data = load_track_data(case_info_file_name)

# plot tracks
anim = plot_tracks(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                            plot_file_name='output\\minimal_example.jpeg')

# animate particles
anim = animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                         title='Minimal example of OceanTracker with 3D point release',
                         movie_file='output\\minimal_example.mp4', show_dry_cells=True)



