from os import path
import argparse
import shutil
from oceantracker import definitions
import  numpy as np
from oceantracker.read_output.python import load_output_files

image_dir= 'output' # where to write plots

# package demo hindcasts
package_dir = path.dirname(definitions.package_dir)
demo_hindcast_dir= path.join(package_dir, 'tutorials_how_to', 'demo_hindcast')

default_root_ouput_dir = path.join(path.dirname(package_dir),'oceantracker_output','unit_tests')

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

a_pollutant= dict(name='a_pollutant',  # must have a user given name
         class_name='oceantracker.particle_properties.age_decay.AgeDecay',  # class_role is resuspension
         # the below are optional settings/parameters
         initial_value=1000,  # value of property when released
         decay_time_scale=7200.)

my_heat_map_time = dict(name='my_heatmap_time',
         class_name='GriddedStats2D_timeBased',
         # the below are optional settings/parameters
         grid_size=[120, 130],  # number of rows, cols cells in the heat map
        grid_span = [10000,10000],
         release_group_centered_grids=True,  # center a grid around each release group
         update_interval=7200,  # time interval in sec, between doing particle statists counts
         particle_property_list=['a_pollutant','water_depth'],  # request a heat map for the decaying part. prop. added above
         #status_list=[],  # only count the particles which are moving

         z_min=-10.,  # only count particles at locations above z=-2m
         start='2017-01-01T02:30:00',
         )




def compare_reference_run(case_info_file, args):

    if case_info_file is None : return

    case_dir =  path.dirname(case_info_file)
    reference_case_dir = case_dir.replace('unit_tests', 'unit_tests_reference_cases')
    reference_case_info_file = path.join(reference_case_dir,path.basename(case_info_file))

    case_info = load_output_files.read_case_info_file(case_info_file)

    if args.reference_case:
        # rewrite reference case output
        shutil.copytree(case_dir, reference_case_dir, dirs_exist_ok=True)

    tracks = load_output_files.load_track_data(case_info_file)
    tracks_ref = load_output_files.load_track_data(reference_case_info_file)
    dx = np.abs(tracks['x'] - tracks_ref['x'])

    # print('x diffs 3 max/ 3 mean ', np.concatenate((np.nanmax(dx, axis=1),np.nanmean(dx, axis=1)),axis=1))

    print(f'(x,y,z) differences from reference run: "{path.basename(case_info_file).split(".")[0]}"' )
    print('\t min  ', np.nanmin(np.nanmin(dx, axis=0), axis=0))
    print('\t mean ', np.nanmean(np.nanmean(dx, axis=0), axis=0))
    print('\t max  ', np.nanmax(np.nanmax(dx, axis=0), axis=0))

    dt = tracks['time'] - tracks_ref['time']
    print('times, \t  min/max diff ', np.nanmin(dt), np.nanmax(dt))

    # compare stats
    stats_params = case_info['working_params']['class_roles']['particle_statistics']
    for name, params in stats_params.items():
        if name not in case_info['output_files']['particle_statistics']: continue
        stats_ref = load_output_files.load_stats_data(reference_case_info_file, name=name)
        stats = load_output_files.load_stats_data(case_info_file, name=name)

        print(f'Stats  compare ref: "{name}"')
        print('\t counts, ref/new', stats_ref['count'].sum(), stats['count'].sum(),
              '\t\t\t max diff counts-ref run counts =', np.max(np.abs(stats['count'] - stats_ref['count'])))
        print('\t count all alive, ref/new', stats_ref['count_all_alive_particles'].sum(),
              stats['count_all_alive_particles'].sum(),
              'last time/age step', stats_ref['count_all_alive_particles'][-1, :].sum(),
              stats['count_all_alive_particles'][-1, :].sum(),
              '\t max diff counts-ref run counts =',
              np.max(np.abs(stats['count_all_alive_particles'] - stats_ref['count_all_alive_particles'])))
        if 'particle_property_list' in params:
            for prop_name in params['particle_property_list']:
                if prop_name not in stats_ref: continue
                prop_sum = f'sum_{prop_name}'
                dc = np.abs(stats[prop_sum] - stats_ref[prop_sum])
                print(f'\t Property sums "{prop_sum}"', 'max mag. ref/new',
                      np.nanmax(np.abs(stats_ref[prop_sum])), np.nanmax(np.abs(stats[prop_sum])), ', max diff =',
                      np.max(dc[np.isfinite(dc)]))
                dc = np.abs(stats[prop_name] - stats_ref[prop_name])
                print(f'\t Property  "{prop_name}"', 'max mag. ref/new',
                      np.nanmax(np.abs(stats_ref[prop_name])), np.nanmax(np.abs(stats[prop_name])),
                      ', max diff =', np.max(dc[np.isfinite(dc)]))