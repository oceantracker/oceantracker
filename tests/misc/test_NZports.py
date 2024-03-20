import numpy as np

from oceantracker.main import OceanTracker
from plot_oceantracker import plot_statistics, plot_tracks
from read_oceantracker.python import load_output_files
from os import path
import argparse
from datetime import datetime, timedelta
from oceantracker.util.cord_transforms import WGS84_to_NZTM

import platform

hostname = platform.node()
print("Hostname:", hostname)

if __name__ == '__main__':


    # settings
    pulse_size = 10
    year= 2022
    start_month=3
    season_length =3*30. # days
    max_age = 18*7*24*3600. # days

    # release_locations
    x0= [[-41.2700912590534, 174.7977062393547],  # wellington
         [-39.47149746318145, 176.9126477054031],  # napier
         [-41.25759866044785, 173.2719552441583],# nelson
         [-43.61488245307373, 172.7176249482729], # lyttleton
         [-36.836259721057125, 174.78007793498807], # auckland
         ]

    hostname = platform.node()
    print("Hostname:", hostname)
    if hostname =='2006d10148w':
        root_input_dir=f'G:\\Hindcasts_large\\OceanNumNZ-2022-06-20\\final_version\\{year}'
        root_output_dir= 'F:\\OceanTrackerOutput\\test'
    else:
        # HPC
        root_input_dir = f'/hpcfreenas/hindcast/OceanNumNZ-2022-06-20/final_version/{year}'
        root_output_dir = '/hpcfreenas/kyleh'


    # convert to NZTM as (lon, lat)
    x0= WGS84_to_NZTM(np.flip(np.asarray(x0), axis=1))

    # setup
    ot = OceanTracker()

    # ot.settings method use to set basic settings
    ot.settings(output_file_base='NZports_test_run',  # name used as base for output files
                root_output_dir =root_output_dir,  # output is put in dir   'root_output_dir'\\'output_file_base'
                time_step=15*60.,  # 15 min time step as seconds
                write_tracks= False,
                )
    # ot.set_class, sets parameters for a named class
    ot.add_class('reader',
                 input_dir= root_input_dir,  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                 file_mask='NZ*.nc')  # hindcast file mask

    # add  release locations            (ie locations where particles are released at the same times and locations)
    # note : can add multiple release groups
    t0 =datetime(year,start_month,1,)
    for n, x in enumerate(x0):
        ot.add_class('release_groups', name=f'P{n:02d}',  # user must provide a name for group first
                 points=[x],  # must be an N by 2 or 3 or list, convertible to a numpy array
                 release_interval=3600.,  # seconds between releasing particles
                 pulse_size=pulse_size,  # number of particles released each release_interval
                 release_start_date=t0.isoformat(),
                 release_end_date=(t0+timedelta(days=season_length)).isoformat(),
                 max_age=max_age
                 )

    ot.add_class('particle_statistics',
                class_name='oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_agedBased',
                 name=f'heat_maps',  # user must provide a name for group first
                 release_group_centered_grids=True,
                 update_interval=3600.,  # seconds between counts
                 grid_size = [220, 221],
                 grid_span= [25000., 25000.], # meters around release point
                 age_bin_size= 7*24*3600.,
                 max_age_to_bin = max_age
                 )

    # run oceantracker
    case_info_file_name = ot.run()


    # do plot
    if True:

        stats_data = load_output_files.load_stats_data(case_info_file_name)
        plot_statistics.animate_heat_map(stats_data,  title='OceanNum Schism, time based particle count heatmaps, built on the fly,  log scale', logscale=True)

        plot_statistics.plot_heat_map(stats_data,release_group='',   title='Test hea map')


