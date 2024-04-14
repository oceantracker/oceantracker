from oceantracker.main import OceanTracker
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--datadir',type=str)
    parser.add_argument('--root_output_dir', type=str)
    args = parser.parse_args()

    if args.datadir:
        input_dir = args.datadir
    else:
        input_dir = r'G:\Hindcasts_large\OceanNumNZ-2022-06-20\final_version\2017\01'

    if args.root_output_dir:
        root_output_dir = args.root_output_dir
    else:
        root_output_dir = r'F:\OceanTrackerOutput\bench_marks'

    ot = OceanTracker()
    ot.settings(time_step=15*60, use_A_Z_profile=False, write_tracks=False,
                max_run_duration= 10*24*3600,
                root_output_dir=root_output_dir, output_file_base='benchmark_v01')
    ot.add_class('reader',  input_dir = input_dir,    file_mask = 'NZfinite*.nc',
                 time_buffer_size=12)

    x0 = [-35.922300421719214, 174.665532083399]  # hen and chickes, in outer grid
    ot.add_class('release_groups', name='my_release_point',  # user must provide a name for release group
                 points=[[1838293.4656, 5940629.8263]],
                 release_interval=0,  # seconds between releasing particles
                 pulse_size=10**6,  # number of particles released each release_interval
                 )

    ot.run()

