#import pprofile
import cProfile
from os import makedirs, path, remove
import platform
import argparse
from datetime import datetime
import numpy as np

import oceantracker.main


from oceantracker.util.json_util import read_JSON , write_JSON

def get_params(datasource=1):
    time_step = 60  # 5min
    release_interval = 3600
    pulse_size = 50000
    calculation_interval = 3 * 3600
    if datasource==1:
        output_file_base= 'Sounds'
        input_dir =  r'Z:\Hindcasts\UpperSouthIsland\2020_MalbroughSounds_10year_benPhD\2008'
        file_mask  = 'schism_marl200801*.nc'
        root_output_dir = 'D:\\OceanTrackerOutput\\OceanTrackerProfiling'

    elif datasource==2:
        output_file_base= 'Sounds'
        input_dir =  '/hpcfreenas/hindcast/UpperSouthIsland/MarlbroughSounds_hindcast_10years_BenPhd_2019ver/'
        file_mask  = 'schism_marl200801*.nc'
        root_output_dir = '/hpcfreenas/ross/oceanTrackerOutput/profiling/'


    elif datasource==3:
        output_file_base= 'demo_SCHISM_3D'
        input_dir =  '..\\demos\\demo_hindcast'
        file_mask  = 'demoHindcastSchism3D.nc'
        root_output_dir = 'output'
        time_step = 60  # 1min
        release_interval = 600
        pulse_size = 200
        calculation_interval = 3600


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
        {'root_output_dir': root_output_dir, 'output_file_base': output_file_base, 'debug': False,
         'time_step': time_step,
        'screen_output_time_interval':6*time_step,
         'max_run_duration': 1 *24*3600,  # 1 days
         'processors': 30,
         #'NUMBA_cache_code' : True,
         'reader': {'input_dir': input_dir,
                    'file_mask': file_mask,
                    #'time_buffer_size': 3,
                    'load_fields': ['water_temperature']
                    },
        'write_tracks': False,
        'dispersion': {'A_H': .2, 'A_V': 0.001},
        'release_groups': [
                {'name':'p1','points': points,
                                'pulse_size': pulse_size, 'release_interval': release_interval,
                                'allow_release_in_dry_cells': True},
                {'name': 'p12' ,'class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
                            'points': poly_points,
                            'pulse_size': pulse_size,
                            'release_interval': release_interval}
                            ],
            'particle_properties': [ {'name':'decay1','class_name': 'oceantracker.particle_properties.age_decay.AgeDecay',
                                    'decay_time_scale': 1. * 3600 * 24}],

            'event_loggers':[ {'name':'event1','class_name': 'oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit',
                                'particle_prop_to_write_list': ['ID', 'x', 'IDrelease_group', 'status', 'age'],
                                'polygon_list': [{'user_polygon_name': 'A', 'points': (np.asarray(poly_points) + np.asarray([-5000, 0])).tolist()},                                                                                                                ]
                                                 }],
            'particle_statistics' :[ {'name': 'statas1','class_name': 'oceantracker.particle_statistics.gridded_statistics2D.GriddedStats2D_ageBased',
                                         'update_interval': calculation_interval, 'particle_property_list': ['water_depth'],
                                         'grid_size': [220, 221],
                                        'grid_span':[10000,20000],
                                         'min_age_to_bin': 0., 'max_age_to_bin': 3. * 24 * 3600, 'age_bin_size': 3600.},
                                     {'name': 'statas2', 'class_name': 'oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_ageBased',
                                         'update_interval': calculation_interval, 'particle_property_list': ['water_depth'],
                                         'min_age_to_bin': 0., 'max_age_to_bin': 3. * 24 * 3600, 'age_bin_size': 3600.,
                                         'polygon_list': [{'points': poly_points}]}
                                        ]
                    }


    return params

def run(profiler_name, params):

    profile_dir = path.join(path.dirname(__file__),'results')
    test_version = 1

    results_file = 'PItest_%03.0f' % test_version + params['output_file_base']
    full_ouput_dir = path.join(params['root_output_dir'], params['output_file_base'])

    case_info_file = path.join(full_ouput_dir, params['output_file_base'] + '_caseInfo.json')

    oceantracker.main.run(params)

    ci = read_JSON(case_info_file)
    d = path.join(profile_dir, profiler_name, params['output_file_base'], platform.processor().replace(' ', '_').replace(',', '_'))
    makedirs(d, exist_ok=True)
    fnn = path.join(d, results_file + '_CodeVer_' + ci['version_info']['str'].replace(' ', '_').replace(',', '_'))

    # copy case file
    #write_JSON(fnn +'_caseInfo.json', ci)

    print('Profile results in ', fnn)
    return fnn

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--datasource', default=1, type=int)
    parser.add_argument('--profiler', default=0, type=int)
    parser.add_argument('-scatch_tests', action='store_true')
    parser.add_argument('-test', action='store_true')
    parser.add_argument('-dev', action='store_true')
    args = parser.parse_args()

    params = get_params(args.datasource)

    # scatch_tests choices of classes
    if args.dev:
        params['base_case_params'].update({'interpolator': {'class_name': 'oceantracker.interpolator.scatch_tests.vertical_walk_at_particle_location_interp_triangle_native_grid.InterpTriangularNativeGrid_Slayer_and_LSCgrid'}})


    if args.test:
        params['max_run_duration'] = 12.*3600  # 12 hour test


    if args.profiler == 0:
        import cProfile
        import pstats
        import time
        profiler = cProfile.Profile()

        profiler.enable()
        fnn = run('cProfile', params)
        profiler.disable()

        prof_file = fnn + ".prof"
        profiler.dump_stats(prof_file)  # Save results to a file

        fn = fnn + "_tottime.txt"
        with open(fn, "w") as f:
            ps = pstats.Stats(prof_file, stream=f)
            ps.sort_stats('tottime')
            ps.print_stats()
            print('cProfile results in' , fn)

        if False:
            with open(fnn + "_cumtime.txt", "w") as f:
                ps = pstats.Stats(prof_file, stream=f)
                # ps.sort_stats('cumulative')
                ps.sort_stats('cumtime')
                ps.print_stats()

        remove(prof_file)

    elif args.profiler==1:
        import pyinstrument
        from pyinstrument import Profiler, renderers

        profiler = Profiler(interval=0.0001)
        profiler.start()
        fnn = run('pyinstrument', params)
        profiler.stop()

        with open(fnn + '.html', mode='w') as f:
            f.write(profiler.output_html(timeline=False))
        print('written Pyinstrument html')

    elif args.profiler == 2:
        #params['profiler'] = 'none'
        params['profiler'] = 'scalene'
        run('scalene', params)

    elif args.profiler == 3:
        params['profiler'] = 'line_profiler'
        run( 'line_profiler',params)

    print('Done')