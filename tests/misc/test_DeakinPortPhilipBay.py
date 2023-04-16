from oceantracker.main import run


import oceantracker.util.basic_util  as basic_util
from os import path
from oceantracker.util import  json_util, yaml_util

import argparse

def set_params(args, x0, duration_sec= 5. * 24 * 3600):


    case = {'run_params': {
        'duration': duration_sec,
        'write_tracks': True},
        'tracks_writer': {'output_step_count': 6},
        'solver': {'screen_output_step_count': 1, 'n_sub_steps': 6},

        'dispersion': {'A_H': 1.0, 'A_V': 0.001},
        'particle_properties':[{'name' :'eDNA', 'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay', 'decay_time_scale': 1. * 3600 * 24}],
        'particle_statistics': [{
            'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
            'calculation_interval': 1800, 'particle_property_list': ['eDNA'],
            'release_group_centered_grids': True,
            'grid_span': [25000., 25000.],
            'grid_size': [150, 151]}]
    }

    # set up one release group per release location to allow heat maps for each point
    rg= []
    for x in x0:
       rg.append({'points': [x], 'pulse_size': 250, 'release_interval': 1800})
    case['particle_release_groups'] = rg

    params = {'shared_params': {'output_file_base': 'PPBtest',
                                'root_output_dir': 'F:\\OceanTrackerOuput\\Deakin\\portPhillipBay',
                                },
              'reader': {'class_name': 'oceantracker.reader.schism_reader.SCHSIMreaderNCDF', 'input_dir': 'F:\\Hindcasts\Deakin_EricT\\PPB_Hydro_netCDF',
                         'file_mask': 'schout_*.nc',
                         'cords_in_lat_long': True,
                         # 'field_map': {'ECO_no3': 'ECO_no3'}, # fields to track at particle locations
                         },
              'case_list': [case]
              }

    if args.mode_debug: params['debug'] = True

    return params

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-mode_debug', action='store_true')
    parser.add_argument('-noplots', action='store_true')
    parser.add_argument('-norun', action='store_true')

    args = parser.parse_args()

    x0 = [[312197, 5795541],
          [294455, 5758887],
          ]

    params = set_params(args, x0, duration_sec=7. * 24 * 3600)

    params['reader']['input_dir'] = r'F:\Hindcasts\Hindcast_samples_tests\Deakin_EricT\PPB_Hydro_netCDF'
    params['reader']['file_mask']= 'schout_*.nc'
    params['shared_params']['root_output_dir'] = 'F:\\OceanTrackerOuput\\Deakin\\portPhillipBay'

    # for info write josn params
    json_util.write_JSON('PPB.json', params)
    yaml_util.write_YAML('PPB.yaml',params)
    if not args.norun:
        run_info_file, has_errors = run(params)
    else:
        run_info_file = path.join(
            params['shared_params']['root_output_dir'],
            params['shared_params']['output_file_base'],
            params['shared_params']['output_file_base'] + '_runInfo.json'
        )

    # do plots
    if not args.noplots:
        from oceantracker.post_processing.read_output_files import load_output_files
        from oceantracker.post_processing.plotting import plot_tracks, plot_statistics

        caseInfoFile = load_output_files.get_case_info_file_from_run_file(run_info_file)

        ax = None
        ax=[ 217641,      404133,     5702747,     5815571]

        track_data = load_output_files.load_particle_track_vars(
            caseInfoFile, var_list=['tide', 'water_depth','eDNA'], fraction_to_read=.02)

        plot_tracks.animate_particles(track_data, axis_lims=ax, title='Port Phillip Bay Schism test',show_dry_cells = False)

        dx=25000
        #ax = [217641+dx, 404133-dx, 5702747+dx, 5815571-dx]
        stats = load_output_files.load_stats_file(caseInfoFile,var_list=['eDNA'])

        # heat map of particle counts
        plot_statistics.animate_heat_map(stats, title='Port Phillip Bay, time based particle count heatmaps, built on the fly',
                                         logscale=False, release_group=2)

        # aminmate decaying particles
        plot_statistics.animate_heat_map(stats,var='eDNA', title='eDNA heatmaps, built on the fly, 1 day exp. decay',
                                         logscale=False, release_group=2)

