from oceantracker.main import run
from oceantracker.post_processing.plotting import plot_heat_maps
from oceantracker.post_processing.read_output_files import load_output_files
import oceantracker.util.basic_util  as basic_util
from oceantracker.util import  json_util, yaml_util
from oceantracker.post_processing.plotting import plot_tracks, plot_vertical_tracks, plot_heat_maps
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

    case ={'run_params':{
                'duration': 8. * 24 * 3600,
                'write_tracks': True,
                'block_dry_cells': False},
        'tracks_writer' : {'output_step_count': 3},
        'solver': { 'screen_output_step_count': 1,  'n_sub_steps': 2},
        'particle_release_groups': [ {'points': x0 ,'pulse_size':10, 'release_interval': 600}],
        'dispersion': {'A_H': 1.0 ,'A_V': 0.001},
        'velocity_modifiers' : [{'class_name': 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'mean': -0.000}],
        'trajectory_modifiers':[{'class_name': 'oceantracker.trajectory_modifiers.resuspension.BasicResuspension',
                                   'critical_friction_velocity': 0.00}],
                                'particle_statistics' : [{
                                 'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                                 'calculation_interval': 3600, 'particle_property_list': ['water_depth'],
                                'grid_center': x0[0],'grid_span': [25000.,25000.],
                                 'grid_size': [120, 121]}],
         'fields' : [{'class_name': 'oceantracker.fields.friction_velocity.FrictionVelocity'}]
        }


    params={ 'shared_params': {'output_file_base': 'jiliantest',
                                'root_output_dir': 'F:\\OceanTrackerOuput\\Vims\\Jilian'},
            'reader': {'class_name': 'oceantracker.reader.schism_reader.SCHSIMreaderNCDF',
                          'file_mask': 'schout_*.nc','input_dir': 'F:\\Hindcasts\\Hindcast_samples_tests\\VIMS\\Particle_ChesBay_Jilian_small',
                          'depth_average': args.depthaverage,
                          'field_variables_to_depth_average': ['water_velocity'],
                          'field_variables': {}, # fields to track at particle locations
                          },
               'case_list': [case]
               }

    if args.mode_debug: params['debug'] = True

    if not args.norun:
        run_info_file, has_errors = run(params)
    else:
        run_info_file = path.join(params['shared_params']['root_output_dir'], params['shared_params']['output_file_base'], params['shared_params']['output_file_base'] + '_runInfo.json')

        # do plot
    if not args.noplots:
        caseInfoFile = load_output_files.get_case_info_file_from_run_file(run_info_file)

        track_data = load_output_files.load_particle_track_vars(caseInfoFile, var_list=['tide', 'water_depth'], fraction_to_read=.05)
        m = load_output_files.load_stats_file(caseInfoFile, nsequence=0)
        caseInfo = load_output_files.read_case_info_file(caseInfoFile)
        param_base = path.join(caseInfo['output_files']['root_output_dir'], 'jilian_rawparams')
        json_util.write_JSON('test_param_files/jilianTest.json', params)
        yaml_util.write_YAML('test_param_files/jilianTest.yaml', params)

        ax=[365000,    400000,     4080000,    4120000]

        plot_tracks.animate_particles(track_data, axis_lims=ax, title='Jilian Schism test, fall velocity and critical friction  resuspension')

        plot_heat_maps.animate_heat_map(m, axis_lims=ax,
                                       title='Jilian Schism, time based particle count heatmaps, built on the fly,  log scale', logscale=True)


        plot_vertical_tracks.plot_path_in_vertical_section(track_data, title='Jilian, fall velocity and critical friction  resuspension ')

