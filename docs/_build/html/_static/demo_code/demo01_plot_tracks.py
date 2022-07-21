from os import path
import argparse
from oceantracker import main
from oceantracker.util import json_util
from oceantracker.post_processing.plotting.plot_tracks import plot_tracks
from oceantracker.post_processing.read_output_files.load_output_files import get_case_info_file_from_run_file, load_particle_track_vars

parser = argparse.ArgumentParser()
parser.add_argument('-noplot', action='store_true')
args = parser.parse_args()

# work to get this demos name and demo dir
demo_dir, demo_name =path.split(__file__)
demo_dir = path.dirname(demo_dir)
demo_name = demo_name.split('.')[0]

# read parameters
params= json_util.read_JSON(path.join(demo_dir, 'demo_json', demo_name + '.json'))

# run OceanTracker
runInfo_file_name, has_errors = main.run(params)

if args.noplot: exit(0)

# find case_info_file name, to use to locate output for the case
case_info_file_name = get_case_info_file_from_run_file(runInfo_file_name)

# read particle tracks for case
track_data = load_particle_track_vars(case_info_file_name)

# plot tacks
plot_tracks(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
            plot_file_name=path.join( params['shared_params']['root_output_dir'], demo_name + '_tracks.jpeg'))