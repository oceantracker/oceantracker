#import pprofile
import cProfile
from os import makedirs, path
#profiler = pprofile.Profile()
import platform
import argparse
from datetime import datetime
import numpy as np

from oceantracker.main import run

from oceantracker.util.json_util import read_JSON , write_JSON

def get_params(args):


    if args.datasource==1:
        output_file_base= 'demo_SCHISM_3D'
        input_dir =  '..\\demos\\demo_hindcast'
        file_mask  = 'demoHindcastSchism3D.nc'
        root_output_dir = 'output'
        n_sub_steps = 60  # 1min
        release_interval = 600
        pulse_size = 200
        calculation_interval = 3*3600


    elif args.datasource==2:
        output_file_base= 'Sounds'
        input_dir =  'G:\\Hindcasts_large\\MalbroughSounds_10year_benPhD\\2008'
        file_mask  = 'schism_marl200801*.nc'
        root_output_dir = 'F:\\OceanTrackerOuput\\OceanTrackerProfiling'
        n_sub_steps = 1  #30min
        release_interval = 3600
        pulse_size = 200
        calculation_interval = 3 * 3600



    points= [[1595000, 5482600. , -1],
             [1599000, 5486200, -1],
                [1597682.1237, 5489972.7479, -1],
                [1598604.1667, 5490275.5488, -1],
                [1598886.4247, 5489464.0424, -1],
                [1597917.3387, 5489000, -1]]
    poly_points = [[1597682.1237, 5489972.7479],
                   [1598604.1667, 5490275.5488],
                   [1598886.4247, 5489464.0424],
                   [1597917.3387, 5489000],
                   [1597300, 5489000], [1597682.1237, 5489972.7479]]



    params = \
        {'shared_params': {'root_output_dir': root_output_dir, 'output_file_base': output_file_base, 'debug': True},
         'reader': {'class_name': 'oceantracker.reader.schism_reader.SCHSIMreaderNCDF',
                    'input_dir': input_dir,
                    'file_mask': file_mask,
                    'field_variables': {'water_temperature': 'temp'}
                    },
         'base_case_params': {'run_params': {'write_tracks': False},
                              'dispersion': {'A_H': .2, 'A_V': 0.001},
                              'solver': {'n_sub_steps': n_sub_steps},
                              'particle_release_groups': [{'points': points,
                                                           'pulse_size': pulse_size, 'release_interval': release_interval,
                                                           'allow_release_in_dry_cells': True},
                                                          {'class_name': 'oceantracker.particle_release_groups.polygon_release.PolygonRelease',
                                                           'points': poly_points,
                                                           'pulse_size': pulse_size, 'release_interval': release_interval}
                                                          ],
                              'particle_properties': [{'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay',
                                                       'decay_time_scale': 1. * 3600 * 24}],
                              'event_loggers': [{'class_name': 'oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit',
                                                 'particle_prop_to_write_list': ['ID', 'x', 'IDrelease_group', 'status', 'age'],
                                                 'polygon_list': [{'user_polygon_name': 'A', 'points': (np.asarray(poly_points) + np.asarray([-5000, 0])).tolist()},
                                                                                                                ]
                                                 }],
                              'trajectory_modifiers': [{'class_name': 'oceantracker.trajectory_modifiers.resuspension.BasicResuspension',
                                                           'critical_friction_velocity': .001}],
                              'velocity_modifiers': [{'class_name': 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'variance': 0.001}],
                              'fields':  [{'class_name': 'oceantracker.fields.friction_velocity.FrictionVelocity'}],
                             'particle_statistics' : [
                                        {'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_agedBased',
                                         'calculation_interval': calculation_interval, 'particle_property_list': ['water_depth'],
                                         'grid_size': [220, 221],
                                         'min_age_to_bin': 0., 'max_age_to_bin': 3. * 24 * 3600, 'age_bin_size': 3600.},
                                        {'class_name': 'oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_ageBased',
                                         'calculation_interval': calculation_interval, 'particle_property_list': ['water_depth'],
                                         'min_age_to_bin': 0., 'max_age_to_bin': 3. * 24 * 3600, 'age_bin_size': 3600.,
                                         'polygon_list': [{'points': poly_points}]}
    ]
                              }
         }

    return params


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--datasource', default=1, type=int)
    parser.add_argument('--testtype', default=1, type=int)
    parser.add_argument('-dev', action='store_true')
    args = parser.parse_args()

    params= get_params(args)

    # dev choices of classes
    if args.dev:
        params['base_case_params'].update( {'interpolator': {'class_name' :'oceantracker.interpolator.dev.vertical_walk_at_particle_location_interp_triangle_native_grid.InterpTriangularNativeGrid_Slayer_and_LSCgrid'}})

    profile_dir= 'results'
    test_version = 1


    results_file = 'PItest_%03.0f' % test_version + params['shared_params']['output_file_base']
    full_ouput_dir=path.join(params['shared_params']['root_output_dir'], params['shared_params']['output_file_base'])
    run_info_file= path.join(full_ouput_dir, params['shared_params']['output_file_base']+'_runInfo.json')
    case_info_file = path.join(full_ouput_dir, params['shared_params']['output_file_base'] + '_caseInfo.json')


    if args.testtype==1:
        from pyinstrument import Profiler,renderers

        profiler = Profiler(interval=0.0002)
        profiler.start()
        run(params)
        profiler.stop()

        ri = read_JSON(run_info_file)

        d =  path.join(profile_dir,'pyinstrument', params['shared_params']['output_file_base'],platform.processor().replace(' ', '_').replace(',', '_') )
        makedirs(d,exist_ok=True)
        fnn=  path.join(d, results_file + '_CodeVer_' + ri['code_version_info']['version'].replace(' ', '_').replace(',', '_') )

        # copy case file
        ci = read_JSON(case_info_file)
        write_JSON(fnn +'_caseInfo.json', ci)

        # write pri
        with open(fnn  + '.html',mode='w') as f:  f.write(profiler.output_html(timeline=False))
        #with open(fnn+ '.html',mode='w') as f:          f.write(profiler.output(renderer=renderers.HTMLRenderer(timeline=False, show_all=False)))



    elif args.testtype == 2:
        import cProfile, pstats
        profiler = cProfile.Profile()
        profiler.enable()
        run(params)
        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats('cumtime')
        stats.print_stats()
    else:
        with cProfile.Profile() as pr:
            main()

            pr.print_stats()

            with profiler:
                main()


            # You can also write the result to the console:
            profiler.print_stats()

            # Or to a file:
            profiler.dump_stats("profiler_stats.txt")

