from oceantracker.main import run
from oceantracker.post_processing.plotting import plot_statistics, plot_tracks
from oceantracker.post_processing.read_output_files import load_output_files
from os import path
import argparse


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-depthaverage', action='store_true')
    parser.add_argument('-mode_debug', action='store_true')
    parser.add_argument('-noplots', action='store_true')
    parser.add_argument('-norun', action='store_true')
    args = parser.parse_args()
    root_input_dir='F:\\Hindcasts\\Hindcast_parts\\OceanNumNZhindcast-2020-06-018\\2019\\07'
    root_output_dir= 'F:\\OceanTrackerOuput\\OceanNum\\test'
    output_file_base='NZnational'

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

    params ={
        'max_run_duration': 5. * 24 * 3600,
        'write_tracks': True,
        'tracks_writer' : {'output_step_count': 3},
        'output_file_base': output_file_base,
        'root_output_dir': root_output_dir,
        'release_groups': {'P1': {'points': x0 ,'pulse_size':5, 'release_interval': 1800}},
        'dispersion': {'A_H': 1.0 ,'A_V': 0.001},

        'particle_statistics' : {'S1':{
                                 'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                                 'update_interval': 3600, 'particle_property_list': ['water_depth'],
                                'grid_center': x0[0],'grid_span': [25000.,25000.],

                                 'grid_size': [120, 121]}},
         'reader': {'file_mask': 'NZ*.nc',
                   'input_dir': root_input_dir,
                      'depth_average': args.depthaverage,
                        'field_variables_to_depth_average': ['water_velocity'],
                      #'field_map': {'ECO_no3': 'ECO_no3'}, # fields to track at particle locations
                      },

           }

    if not args.depthaverage:
        params['velocity_modifiers']= {'fall_vel':{'class_name': 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': 0.000}}
        params['resuspension']={'critical_friction_velocity': 0.025}
    if args.mode_debug: params['debug'] = True

    if not args.norun:
        caseInfoFile, has_errors= run(params)

    else:
        run_dir= path.join(root_output_dir, output_file_base)
        caseInfoFile = load_output_files.get_case_info_files_from_dir(run_dir, case=1)

    # do plot
    if not args.noplots:

        ax=[800000,     2200000,     4400000,     6400000] # NZ
        ax=[1727860,     1823449,     5878821,     5957660] # Auck

        axBOP= [1856014.778854954,1978628.00674731, 5794851.51338963, 5889202.600050561]
        track_data = load_output_files.load_track_data(caseInfoFile)
        plot_tracks.animate_particles(track_data, axis_lims=ax, title='OceanNum NZ Schism test, fall velocity and critical friction  resuspension')
        plot_tracks.plot_path_in_vertical_section(track_data, title='OceanNum, fall velocity and critical friction  resuspension ')

        stats_data = load_output_files.load_stats_data((caseInfoFile))
        plot_statistics.animate_heat_map(stats_data, axis_lims=ax, title='OceanNum Schism, time based particle count heatmaps, built on the fly,  log scale', logscale=True)

        plot_statistics.plot_heat_map(stats_data, axis_lims=ax, var='water_depth', title='Water_depth, Time based Heat maps built on the fly, no tracks recorded')


