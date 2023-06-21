from oceantracker.run_oceantracker import main
from oceantracker.util import yaml_util, json_util
from os import path
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-norun', action='store_true')
parser.add_argument('-hpc', action='store_true')
args = parser.parse_args()

# https://tidesandcurrents.noaa.gov/ofs/lsofs/lsofs.html
# https://www.ncei.noaa.gov/thredds/catalog/model-lsofs-files/catalog.html
output_file_base='FVCOM_Lake_Superior_test'


if args.hpc:
    input_dir='/hpcfreenas/hindcast/LakeSuperior/'
    root_output_dir = '/hpcfreenas/ross/oceanTrackerOutput/LakeSuperior/'
else:
    input_dir='F:\\Hindcasts\\colaborations\\LakeSuperior\\historical_sample'
    root_output_dir = 'output'

print(args,input_dir)
file_mask ='nos.lsofs.fields.n000*.nc'

points = [[256203.6793068961, 5193002.88896844, -10],
           [416692.1617094234, 5216000.828769726, -10],
           [666422.5233426465, 5189371.635315605, -10],
           [429178.67979108455, 5417656.448290474, -10],
           [439094.44415005075, 5265627.962025132, -10]]

# just use one point
points= [[439094.44415005075, 5265627.962025132, -10]]

params={'shared_params' :{'output_file_base' : output_file_base,'root_output_dir':root_output_dir,
                          'time_step' : 20*60},
     'reader': {"class_name": 'oceantracker.reader.FVCOM_reader.unstructured_FVCOM',
                'input_dir': input_dir, 'search_sub_dirs': True,
                'file_mask': file_mask},
    'base_case_params' : {
        'run_params' : {'user_note':'test of notes'},
        'release_groups': [{'points': points, 'pulse_size': 250, 'release_interval': 7200}] ,
        'trajectory_modifiers': [{'class_name': 'oceantracker.resuspension.BasicResuspension',
                                                        'critical_friction_velocity': .000}],
        'fields' :[{'class_name' : 'oceantracker.fields.friction_velocity.FrictionVelocity'}],
        'particle_statistics':[
                  {'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                      'update_interval': 72000,   'grid_size': [320, 321],'grid_span':[ 250000,250000],'grid_center':points[0]}]
                          }
}

yaml_util.write_YAML(output_file_base+'.yaml',params)
json_util.write_JSON(output_file_base+'.json',params)

if args.norun:
    # infer run file name
    runInfo_file_name = path.join(params['shared_params']['root_output_dir'], params['shared_params']['output_file_base'], params['shared_params']['output_file_base'] + '_runInfo.json')
else:
    # run oceantracker
    runInfo_file_name,has_errors= main.run(params)


from oceantracker.post_processing.read_output_files import load_output_files
from oceantracker.post_processing.plotting import plot_utilities
from oceantracker.post_processing.plotting.plot_tracks import animate_particles, plot_tracks
from oceantracker.post_processing.plotting.plot_statistics import animate_heat_map, plot_heat_map
case_info_file_name = load_output_files.get_case_info_file_from_run_file(runInfo_file_name)
grid= load_output_files.load_grid(case_info_file_name)

#plot_utilities.display_grid(grid, ginput=6)

track_data = load_output_files.load_track_data(case_info_file_name,fraction_to_read=.1)

animate_particles(track_data,  show_grid=True,axis_lims=None,
                  heading='FVCOM reader test',show_dry_cells=False,
                  release_group=None, movie_file=output_file_base + '_animation01.mp4',
                                fps=15,size=6,
                  back_ground_depth=True, interval=20)
plot_tracks(track_data)

# heat maps from on the fly counts
stats_data = load_output_files.load_stats_data(case_info_file_name)

animate_heat_map(stats_data,  heading=output_file_base + ' particle count heat map',  vmax=100.,
                 movie_file=output_file_base + '_animation01.mp4',)
plot_heat_map(stats_data,  heading=output_file_base + ' particle count heat map', vmax=100.)