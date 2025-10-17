from os import path
import argparse

from oceantracker import definitions


image_dir= 'output' # where to write plots

# package demo hindcasts
demo_hindcast_dir= path.join(path.dirname(definitions.package_dir), 'tutorials_how_to', 'demo_hindcast')

default_root_ouput_dir = path.join(path.dirname(definitions.package_dir),'oceantracker_output')

reader_demo_schisim3D=   dict(input_dir= path.join(demo_hindcast_dir, 'schsim3D'),
                              file_mask='demo_hindcast_schisim3D*.nc')
reader_demo_ROMS= dict(input_dir=path.join(demo_hindcast_dir, 'ROMS'),
                       file_mask='ROMS3D_00*.nc')
reader_demo_schisim2D=   dict(input_dir= path.join(demo_hindcast_dir, 'schsim2D'),
                              file_mask='Random_order*.nc')

def get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('--test', type=int)
    parser.add_argument('--mod', type=int)
    parser.add_argument('-devmode', action='store_true')
    parser.add_argument('-norun', action='store_true')
    parser.add_argument('-native_z_grid', action='store_true')
    parser.add_argument('--variant', default=0, type=int)
    parser.add_argument('-backtracking', action='store_true')
    parser.add_argument('-reference_case', action='store_true')
    parser.add_argument('-plot', action='store_true')
    parser.add_argument('-save_plots', action='store_true')

    args = parser.parse_args()

    return args

def base_settings(func_name):
    args = get_args()
    d = dict(output_file_base=func_name,
             root_output_dir=default_root_ouput_dir,
             )
    return d

rg_P1 = dict(name='rg_basic',  # name used internal to refer to this release
                class_name='PointRelease',  # class to use
                release_interval=1800,  # seconds between releasing particles
                pulse_size=5)
schism_demo = dict(deep_point=[1594000, 5484200, -2],  # deep water
                   deep_polygon=[[1597682., 5486972], [1598604, 5487275], [1598886, 5486464],
                                 [1597917., 5484000], [1597300, 5484000], [1597682, 5486972]],
                   )
