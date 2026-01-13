from oceantracker.main import OceanTracker
from os import path
import dd
from oceantracker.util import json_util
from copy import deepcopy
import time


# need to use pool to keep memory of runs separate
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
    ot.settings(**dd.base_settings(__file__, args))
    ot.settings(time_step=1800,
                use_dispersion=False,
                screen_output_time_interval=1800,
             use_A_Z_profile=True,
            particle_buffer_initial_size= 200,
             NUMBA_cache_code=False,
                use_random_seed=True,
                use_resuspension = False,
            )


    hm = dd.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'])

    # add a point release
    ot.add_class('release_groups',**dict(dd.rg_release_interval0,
                 release_interval=3600))

    ot.add_class('particle_properties', **dd.pp1)  # add a new property to particle_properties role

    #ot.add_class('particle_statistics', **dict(dd.my_heat_map_age,
   #              update_interval=5*ot.params['time_step']   ))
   # ot.add_class('particle_statistics', **dd.my_poly_stats_age, polygon_list=[dict(points=hm['polygon'])])

    ot.add_class('tracks_writer', **dd.tracks_writer,
                 update_interval=1800,
                 time_steps_per_per_file= 10)

    params = deepcopy(ot.params)


    if  args.reference_case:
        # do full run without continue
        params.update(continuable=True, output_file_base=params['output_file_base']+'_full_run')
        case_info_file = run(params)
    else:
        # do split continuation runs
        params.update(continuable=True, max_run_duration = 12*3600,output_file_base=params['output_file_base']+'_first_run')
        case_info_file1 = run(params)

        # continue this run
        cs1 = json_util.read_JSON(case_info_file1)
        output_files = cs1['output_files']
        params = deepcopy(ot.params)
        params.update(continue_from=path.join(output_files['run_output_dir']),
                      output_file_base=params['output_file_base'] + '_full_run')
        case_info_file = run(params)


    dd.compare_reference(case_info_file, args, last_time=True)
    dd.show_track_plot(case_info_file, args)

    return  ot.params



