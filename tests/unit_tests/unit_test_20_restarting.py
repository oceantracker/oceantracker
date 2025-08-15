from oceantracker.main import OceanTracker
from os import path
from tests.unit_tests import test_definitions
from oceantracker.util import json_util
from copy import deepcopy
import time

def run(params):
    from multiprocessing import Pool
    with Pool(processes=1) as pool:
        # Use map to apply worker_function to a list of numbers in parallel
        case_info_file = pool.map(worker_function, [params])
    return case_info_file[0]
def worker_function(params):
    from oceantracker.oceantracker_params_runner import OceanTrackerParamsRunner
    ot_params = OceanTrackerParamsRunner()
    results = ot_params.run(params)
    return results

def main(args):
    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__, args))
    ot.settings(time_step=1800,
                use_dispersion=False,
                screen_output_time_interval=1800,
             use_A_Z_profile=True,
            regrid_z_to_uniform_sigma_levels=False,
            particle_buffer_initial_size= 200,
             NUMBA_cache_code=True,
                use_random_seed=True,
                use_resuspension = False,
                restart_interval = None if args.reference_case else 3*3600,
                throw_debug_error= 0 if args.reference_case else 1,
            )


    hm = test_definitions.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'])

    # add a point release
    ot.add_class('release_groups',**test_definitions.rg_release_interval0)

    ot.add_class('particle_properties', **test_definitions.pp1)  # add a new property to particle_properties role

    #ot.add_class('particle_statistics', **test_definitions.my_heat_map_time)
    #ot.add_class('particle_statistics', **test_definitions.my_poly_stats_time, polygon_list=[dict(points=hm['polygon'])])

    ot.add_class('particle_statistics', **test_definitions.my_heat_map_age)
    #ot.add_class('particle_statistics', **test_definitions.my_poly_stats_time, polygon_list=[dict(points=hm['polygon'])])

    ot.add_class('tracks_writer', update_interval=1800,
                 time_steps_per_per_file=None if args.reference_case else 10)

    params = deepcopy(ot.params)
    case_info_file =  run(params)

    # do restart
    if not args.reference_case:
        params.update( restart = True,throw_debug_error=0)
        case_info_file = run(params)

    test_definitions.compare_reference_run_tracks(case_info_file, args)
    test_definitions.show_track_plot(case_info_file, args)

    return  ot.params



