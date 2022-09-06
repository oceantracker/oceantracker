from oceantracker.main import run
from oceantracker.post_processing.read_output_files import load_output_files
import argparse

poly_points=[[1597682.1237, 5489972.7479],
                        [1598604.1667, 5490275.5488],
                        [1598886.4247, 5489464.0424],
                        [1597917.3387, 5489000],
                        [1597300, 5489000], [1597682.1237, 5489972.7479]]

x0=[[1702396.742672811, 5365321.02654298], [1754437.3985253456, 5429551.69667285], [1687962.108202765, 5434139.601682127],
    [1665170.580092166, 5432100.532789115], [1678465.638156682, 5462176.798961039], [1648836.6516129032, 5474411.212319109],
    [1600214.7249769587, 5499389.806258503],
    [1646937.3576036866, 5578913.493085961], [1739622.9052534562, 5549346.994137291], [1703156.4602764978, 5444334.946147186]]

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-depthaverage', action='store_true')
    parser.add_argument('-mode_debug', action='store_true')
    parser.add_argument('-noplots', action='store_true')
    args = parser.parse_args()



    case ={'run_params':{
                'duration': 8. * 24 * 3600,
                'write_tracks': True},
        'tracks_writer' : {'output_step_count': 3},
        'solver': { 'screen_output_step_count': 1,  'n_sub_steps': 2},
        'particle_release_groups': [ {'points': x0 ,'pulse_size':5, 'release_interval': 1800}],
        'dispersion': {'A_H': 1.0 ,'A_V': 0.001},

        'particle_statistics' : [{
                                 'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                                 'calculation_interval': 3600, 'particle_property_list': ['water_depth'],
                                'grid_center': x0[0],'grid_span': [25000.,25000.],

                                 'grid_size': [120, 121]}],
        'particle_properties': [{'class_name': 'oceantracker.particle_properties.friction_velocity.FrictionVelocity'}]
        }

    if not args.depthaverage:
        case['velocity_modifiers']= [{'class_name': 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'mean': 0.000}]
        case['trajectory_modifiers']=[{'class_name': 'oceantracker.trajectory_modifiers.resuspension.BasicResuspension',
                                   'critical_friction_velocity': 0.025}]

    params={ 'shared_params': {'output_file_base': 'soundstest',

                            'root_output_dir': 'F:\\OceanTrackerOuput\\Sounds\\test',
                               'max_duration': 5*24*3600.},
        'reader': {'class_name': 'oceantracker.reader.schism_reader.SCHSIMreaderNCDF',
                      'file_mask': 'schism_marl200801*.nc', 'input_dir': 'G:\\hindcasts\\marl_hindcast_BenPhd_2019ver\\2008',
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

        particle_plot.display_grid(caseInfoFile, ginput=10)

        plot_tracks.animate_particles(caseInfoFile, title='metocean sounds Schism test, fall velocity and critical friction  resuspension')

        particle_plot.plot_heat_map(caseInfoFile, var='water_depth', title='Water_depth, Time based Heat maps built on the fly, no tracks recorded')



