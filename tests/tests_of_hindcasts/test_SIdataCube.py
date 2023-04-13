from oceantracker.main import run
from oceantracker.post_processing.plotting import plot_statistics
from oceantracker.post_processing.read_output_files import load_output_files
import argparse


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-depthaverage', action='store_true')
    parser.add_argument('-mode_debug', action='store_true')
    parser.add_argument('-noplots', action='store_true')
    args = parser.parse_args()

    x0 =[[1180342.7419,      4795140.0454, 0 ],
         [1264415.3226 ,      4759258.1378, 0],
         [1211995.9677,      4822240.7267,0 ],
         [1243245.9677,      4831476.15448, 0],
        ]
    x0 =[[1180342.7419,      4795140.0454, 0 ]]

   # '1225302.4194      4790295.2309'

    case ={'run_params':{
                'duration': 8. * 24 * 3600,

                'write_tracks': True},
        'tracks_writer' : {'turn_on_write_particle_properties_list':['n_cell'],'output_step_count': 3},
        'particle_release_groups': [ {'points': x0 ,'pulse_size':70, 'release_interval': 600}],
        'dispersion': {'A_H': 1.0 ,'A_V': 0.001},
        'velocity_modifiers' : [{'class_name': 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'mean': 0.001}],
        'trajectory_modifiers': [{'class_name': 'oceantracker.trajectory_modifiers.resuspension.BasicResuspension',
                                       'critical_friction_velocity': 0.00},],
        'particle_properties': [{'class_name': 'oceantracker.particle_properties.friction_velocity.FrictionVelocity'}],
        'particle_statistics': [{
            'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
            'calculation_interval': 3600, 'particle_property_list': ['water_depth'],
            'grid_center': x0[0], 'grid_span': [25000., 25000.],

            'grid_size': [120, 121]}]
        }

    params={ 'shared_params': {'output_file_base': 'SIdataCubetest',

                                'root_output_dir': 'F:\\OceanTrackerOuput\\OceanNum'},
            'reader': {'class_name': 'oceantracker.reader.schism_reader.SCHSIMreaderNCDF',
                          'file_mask': 'schout_*.nc', 'input_dir': 'F:\\Hindcasts\\OceanNumSouthlandCube\\2010\\01',
                          'depth_average': args.depthaverage,
                       'field_variables_to_depth_average': ['water_velocity'],

                          },
               'case_list': [case]
               }

    if args.mode_debug: params['debug'] = True

    run_info_file, has_errors= run(params)

    # do plot
    if not args.noplots:
        caseInfoFile = load_output_files.get_case_info_file_from_run_file(run_info_file)

        ax= None
        plot_tracks.animate_particles(caseInfoFile, axis_lims=ax, title='OceanNum Stewart Is Cube test')

        plot_heat_maps.animate_heat_map(caseInfoFile, axis_lims=ax,
                                       title='OceanNum Stewart , time based particle count heatmaps, built on the fly,  log scale', logscale=True)

        particle_plot.plot_heat_map(caseInfoFile, axis_lims=ax, var='water_depth',
                                    title='Water_depth, Time based Heat maps built on the fly, no tracks recorded')

        particle_plot.plot_path_in_vertical_section(caseInfoFile, title='OceanNum Stewart, fall velocity and critical friction  resuspension ')

