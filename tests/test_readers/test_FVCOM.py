from oceantracker.run_oceantracker import main
from oceantracker.util.ncdf_util import NetCDFhandler
from os import path
import numpy as np

points = [[ 650000, 7794453.5, -1. ], [ 649000, 7790000, -1. ]]

output_file_base='FVCOM_sample'
root_output_dir ='\output'
input_dir='D:\input\FVCOM'
file_mask ='AkvaplanNiva_sample.nc'
params={'shared_params' :{'output_file_base' : output_file_base,'root_output_dir':root_output_dir },
     'reader': {"class_name": 'oceantracker.reader.dev_FVCOM_reader.unstructured_FVCOM',
                'input_dir': input_dir, 'minimum_total_water_depth': 5,
                'file_mask': file_mask,},
    'base_case_params' : {'solver': {'n_sub_steps': 6},
    'run_params' : {'user_note':'test of notes'},
    'particle_release_groups': [{'points': points, 'pulse_size': 10, 'release_interval': 600}],
                        }
}

#nc= NetCDFhandler(path.join(input_dir,file_mask))

runInfo_file_name,has_errors= main.run(params)

from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars,  get_case_info_file_from_run_file
from oceantracker.post_processing.plotting.plot_tracks import animate_particles

case_info_file_name = get_case_info_file_from_run_file(runInfo_file_name)

track_data = load_particle_track_vars(case_info_file_name)

ax= np.asarray(points[0])
dx=15000
ax= [ax[0]-dx, ax[0]+dx,ax[1]-dx, ax[1]+dx]

animate_particles(track_data,  show_grid=True,axis_lims=ax,
                  heading='FVCOM reader test',
                  release_group=None,
                  back_ground_depth=True, show_dry_cells=True, interval=20)
