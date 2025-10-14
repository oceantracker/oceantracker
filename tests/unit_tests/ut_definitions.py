from os import path
import argparse

from oceantracker import definitions


image_dir= 'output' # where to write plots

# package demo hindcasts
root_hindcast_dir= path.join(path.dirname(definitions.package_dir),'tutorials_how_to','demo_hindcast')
reader_demo_schisim3D=   dict( input_dir= path.join(root_hindcast_dir,'schsim3D'),
                file_mask='demo_hindcast_schisim3D*.nc')
reader_demo_ROMS= dict(input_dir=path.join(root_hindcast_dir, 'ROMS'),
                file_mask='ROMS3D_00*.nc')
reader_demo_schisim2D=   dict( input_dir= path.join(root_hindcast_dir,'schsim2D'),
                file_mask='Random_order*.nc')

def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', type=int)
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

