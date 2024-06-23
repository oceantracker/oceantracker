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

    # biological settings
    pulse_size = 75000
    start_month = 10  # October
    season_length = 5 * 30.  # days
    max_age = 4 * 7 * 24 * 3600.  # weeks for PLD

    # run settings
    year = 2021
    start_day = 28  # day of the month larval release starts
    runDurationInDays = 365  # days for a year
    release_period = 7 * 24 * 3600  # seconds between releasing particles - in weeks currently
    output_name = 'charybdis_full_1yr_500km_V7'  # name for the output files

    # release_locations
    x0 = [[-35.27076, 174.10454],  # Bay of Islands
          [-35.82864, 174.48577],  # Whangarei
          [-36.83625, 174.78007],  # Auckland
          [-36.31774, 175.48463],  # Tryphena Harbour GBI
          [-37.65516, 176.17783],  # Tauranga
          [-38.68000, 178.01400],  # Gisborne
          [-39.05710, 174.04109],  # Taranaki
          [-39.47149, 176.91264],  # Napier
          [-41.27009, 174.79770],  # Wellington
          [-41.26331, 174.02158],  # Picton
          [-41.25759, 173.27195],  # Nelson
          [-43.61146, 172.71692],  # Lyttelton
          [-44.38661, 171.26325],  # Timaru
          [-45.81108, 170.62899],  # Dunedin (Port Chalmers)
          [-46.59581, 168.34934]  # Bluff
          ]

    hostname = platform.node()
    print("Hostname:", hostname)
    if hostname == '2006d10148w':
        root_input_dir = f'G:\\Hindcasts_large\\2024_OceanNumNZ-2022-06-20\\final_version\\{year}'
        root_output_dir = 'F:\\OceanTrackerOutput\\test'
    else:
        # HPC
        root_input_dir = f'/hpcfreenas/hindcast/OceanNumNZ-2022-06-20/final_version/{year}'
        root_output_dir = '/hpcfreenas/kyleh'

    # convert to NZTM as (lon, lat)
    x0 = WGS84_to_NZTM(np.flip(np.asarray(x0), axis=1))

    # setup
    ot = OceanTracker()

    # ot.settings method use to set basic settings
    ot.settings(output_file_base=output_name,  # name used as base for output files
                root_output_dir=root_output_dir,  # output is put in dir   'root_output_dir'\\'output_file_base'
                time_step=15 * 60.,  # 15 min time step as seconds
                write_tracks=False,
                max_run_duration=3600 * 24 * runDurationInDays
                )
    # ot.set_class, sets parameters for a named class
    ot.add_class('reader',
                 input_dir=root_input_dir,  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                 file_mask='NZ*.nc')  # hindcast file mask

    # add  release locations            (ie locations where particles are released at the same times and locations)
    # note : can add multiple release groups
    t0 = datetime(year, start_month, start_day, )  # release start date - can change start day of the month
    for n, x in enumerate(x0):
        t = (t0 + timedelta(days=season_length)).isoformat()
        t=t0.isoformat()
        print(year, start_month, start_day, t0, t)
        ot.add_class('release_groups', name=f'P{n:02d}',  # user must provide a name for group first
                     points=[x],  # must be an N by 2 or 3 or list, convertible to a numpy array
                     release_interval=release_period,  # seconds between releasing particles - in weeks currently
                     pulse_size=pulse_size,  # number of particles released each release_interval
                     start=t,
                     # end = t,
                     duration=3600 * 24 * season_length,
                     max_age=max_age
                     )

    ot.add_class('particle_statistics',
                 class_name='oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_ageBased',
                 name=f'heat_maps',  # user must provide a name for group first
                 release_group_centered_grids=True,
                 update_interval=3600.,  # seconds between counts
                 grid_size=[200, 200],
                 grid_span=[500000., 500000.],  # meters around release point
                 age_bin_size=7 * 24 * 3600.,
                 max_age_to_bin=max_age
                 )

    # run oceantracker
    case_info_file_name = ot.run()

    # do plot
    if True:
        stats_data = load_output_files.load_stats_data(case_info_file_name)
        plot_statistics.animate_heat_map(stats_data, title='OceanNum Schism, time based particle count heatmaps, built on the fly,  log scale', logscale=True)

        plot_statistics.plot_heat_map(stats_data, release_group='', title='Test heat map')

