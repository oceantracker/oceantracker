from oceantracker.main import run
from plot_oceantracker import plot_statistics
from read_oceantracker.python import load_output_files
import oceantracker.util.basic_util  as basic_util
from oceantracker.util import  json_util, yaml_util
from plot_oceantracker import plot_tracks, plot_vertical_tracks, plot_statistics
from os import path
import argparse


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-depthaverage', action='store_true')
    parser.add_argument('-mode_debug', action='store_true')
    parser.add_argument('-noplots', action='store_true')
    parser.add_argument('-norun', action='store_true')
    args = parser.parse_args()

    x0 =[[380638.11568,4093116.7806, 0 ]]

    case ={ }


    params={ 'output_file_base': 'jiliantest',
            'root_output_dir': 'F:\\OceanTrackerOtuput\\Vims\\Jilian',
            'reader': {'class_name': 'oceantracker.reader.schism_reader.SCHISMreaderNCDF',
                          'file_mask': 'schout_*.nc','input_dir': 'F:\\Hindcasts\\Hindcast_samples_tests\\VIMS\\Particle_ChesBay_Jilian_small',
                          'field_variables_to_depth_average': ['water_velocity'],
                          'load_fields': {}, # fields to track at particle locations
                          },
             'max_run_duration': 8. * 24 * 3600,
             'write_tracks': True,
             'block_dry_cells': False,
             'tracks_writer': {'output_step_count': 3},
             'release_groups': {'mypoints': {'points': x0, 'pulse_size': 10, 'release_interval': 600}},
             'dispersion': {'A_H': 1.0, 'A_V': 0.001},
             'velocity_modifiers': {'myfal_vel': {'class_name': 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': -0.000}},
             'particle_statistics':{'mygrid':{
                 'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                 'update_interval': 3600, 'particle_property_list': ['water_depth'],
                 'grid_center': x0[0], 'grid_span': [25000., 25000.],
                 'grid_size': [120, 121]}},
              }

    if args.mode_debug: params['debug'] = True

    if not args.norun:
        case_info_file = run(params)
    else:
        case_info_file = path.join(params['root_output_dir'], params['output_file_base'], params['output_file_base'] + '_caseInfo.json')

        # do plot
    if not args.noplots:
        track_data = load_output_files.load_track_data(case_info_file, var_list=['tide', 'water_depth'], fraction_to_read=.05)
        m = load_output_files.load_stats_data(case_info_file, name= 'mygid')

        ax=[365000,    400000,     4080000,    4120000]

        plot_tracks.animate_particles(track_data, axis_lims=ax, title='Jilian Schism test, fall velocity and critical friction  resuspension')

        plot_statistics.animate_heat_map(m, axis_lims=ax,
                                       title='Jilian Schism, time based particle count heatmaps, built on the fly,  log scale', logscale=True)


        plot_vertical_tracks.plot_path_in_vertical_section(track_data, title='Jilian, fall velocity and critical friction  resuspension ')

