import numpy as np

from oceantracker.main import run
from plot_oceantracker import plot_statistics, plot_tracks
from read_oceantracker.python import load_output_files
from os import path
import argparse


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-mode_debug', action='store_true')
    parser.add_argument('-noplots', action='store_true')
    parser.add_argument('-norun', action='store_true')
    args = parser.parse_args()
    root_input_dir=r'F:\Hindcasts\Hindcast_samples_tests\Auckland_uni_hauarki\old_format'
    root_input_dir = r'F:\Hindcasts\Hindcast_samples_tests\Auckland_uni_hauarki\new_converted_to_old_ format'


    root_output_dir= 'F:\\OceanTrackerOtuput\\Auckland_uni_hauarki'
    output_file_base='test_old_format'

    x0 =[[1780846.7742,       5938985.617],
    [1652889.7849,      5820893.2627],
    [1701814.5161,      5492354.2771],
    [ 1530577.957,      4974564.7237],
    [1208803.7634,      4827706.2831],
    [1589852.1505,      6125208.1756]]
    x0=[ [1750624.1218,      5921952.0475],
        [1814445.5871,      5882261.7676],
        [1838293.4656,      5940629.8263],
        [1788021.4244,      5940860.2283]
         ]
    from oceantracker.util.cord_transforms import NZTM_to_WGS84, WGS84_to_UTM
    x0 = NZTM_to_WGS84(np.asarray(x0))
    x0 = WGS84_to_UTM(x0)

    params ={
        'max_run_duration': 5. * 24 * 3600,
        'write_tracks': True,
        'output_file_base': output_file_base,
        'root_output_dir': root_output_dir,
        'release_groups': {'P1': {'points': x0 ,'pulse_size':5, 'release_interval': 3600}},
        'dispersion': {'A_H': 1.0 ,'A_V': 0.001},
        'particle_statistics' : {'S1':{
                                 'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                                 'update_interval': 3600, 'particle_property_list': ['water_depth'],
                                'grid_center': x0[0].tolist(),'grid_span': [25000.,25000.],
                                 'grid_size': [120, 121]}},
         'reader': {'file_mask': 'sch*.nc',
                   'input_dir': root_input_dir,
                    'regrid_z_to_equal_sigma': True,
                    'hydro_model_cords_in_lat_long' : True,
                      #'field_map': {'ECO_no3': 'ECO_no3'}, # fields to track at particle locations
                      },
           }


    params['velocity_modifiers']= {'fall_vel':{'class_name': 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': 0.000}}
    params['resuspension']={'critical_friction_velocity': 0.01}
    if args.mode_debug: params['debug'] = True

    pass

    if not args.norun:
        caseInfoFile= run(params)

    else:
        caseInfoFile= path.join(root_output_dir, output_file_base,output_file_base+'_caseInfo.json')

    # do plot
    if not args.noplots:

        ax=[800000,     2200000,     4400000,     6400000] # NZ
        ax=[1727860,     1823449,     5878821,     5957660] # Auck


        track_data = load_output_files.load_track_data(caseInfoFile)
        plot_tracks.animate_particles(track_data, title='Hauraki test ',movie_file='HG.MP4',show_grid=True,show_dry_cells=True)
        #plot_tracks.plot_path_in_vertical_section(track_data, title='OceanNum, fall velocity and critical friction  resuspension ')

        stats_data = load_output_files.load_stats_data((caseInfoFile))
        plot_statistics.animate_heat_map(stats_data, axis_lims=ax, title='OceanNum Schism, time based particle count heatmaps, built on the fly,  log scale', logscale=True)

        plot_statistics.plot_heat_map(stats_data, axis_lims=ax, var='water_depth', title='Water_depth, Time based Heat maps built on the fly, no tracks recorded')


