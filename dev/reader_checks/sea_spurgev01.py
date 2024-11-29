import  argparse
from os import path,chdir, mkdir


import  sys
from oceantracker.util import json_util, yaml_util
from oceantracker.main import OceanTracker
from plot_oceantracker import plot_tracks
from read_oceantracker.python import  load_output_files
if __name__ == "__main__":
    # nested schisim, glorys

    input_dir1 = r'D:\Hindcast_reader_tests\Glorys\glorys_seasuprge3D'
    file_mask1='cmems*.nc'
    input_dir1 = r'D:\Hindcast_reader_tests\Glorys\glorys_seasuprge2D'
    file_mask1 = 'surf*.nc'
    #input_dir1=r'D:\Hindcast_reader_tests\Glorys\ocean_num_glorys'
    #file_mask1='glorys_reanalysis_surface*.nc'

    input_dir2 = r'Z:\Hindcasts\NZ_region\2024_OceanNumNZ-2022-06-20\final_version\2022\04'
    output_dir = r'D:\OceanTrackerOutput'

    ot = OceanTracker()
    ot.settings(output_file_base = 'sea_spurge01',root_output_dir=output_dir, time_step=1800,
                #display_grid_at_start=True
                )
    ot.add_class('reader',input_dir=input_dir1,
                 file_mask = file_mask1)
    ot.add_class('nested_readers',input_dir=input_dir2, file_mask = 'NZfinite*.nc',
                 EPSG_code=2193,
                 hgrid_file_name= r'Z:\Hindcasts\NZ_region\2024_OceanNumNZ-2022-06-20\final_version\hgridNZ_run.gr3')


    pulse_size = 5


    file_mask = 'NZfinite*.nc'
    max_days = 5  # 30
    open_boundary_type = 1

    x0 = [ [174.665532083399,-35.922300421719214], # hen and chickes, in outer grid
           [167.70585302583135, -41.09760403942677],
           [168.18486957886807, -41.126477553835635],
           [178.78311081480544, -34.83205141270341],
          [ 178.9627420221942, -41.47295972674199]]
    ot.add_class('release_groups',points = x0, pulse_size=10, release_interval=1800)
    if True:
        case_info_file= ot.run()
    else:
        case_info_file = r'D:\OceanTrackerOutput\sea_spurge01\f'
    tracks =load_output_files.load_track_data(case_info_file,gridID=1) # plot inner grid
    anim = plot_tracks.animate_particles(tracks,
                                         show_grid=True, show_dry_cells=True, axis_labels=True,
                                         )



