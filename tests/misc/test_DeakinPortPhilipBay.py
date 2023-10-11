from oceantracker.main import run


import oceantracker.util.basic_util  as basic_util
from os import path
from oceantracker.util import  json_util, yaml_util

import argparse

def set_params(args, x0, duration_sec= 5. * 24 * 3600):


    # set up one release group per release location to allow heat maps for each point
    rg= {}
    for n, x in enumerate( x0):
       rg[f'P{n}']= {'points': [x], 'pulse_size': 150, 'release_interval': 1800}


    params = {'output_file_base': 'PPBtest','time_step': 1800,
              'root_output_dir': 'F:\\OceanTrackerOuput\\Deakin\\portPhillipBay',
              'reader': {'class_name': 'oceantracker.reader.schism_reader.SCHISMSreaderNCDF', 'input_dir': 'F:\\Hindcasts\Deakin_EricT\\PPB_Hydro_netCDF',
                         'file_mask': 'schout_*.nc',
                         'cords_in_lat_long': True,
                         # 'field_map': {'ECO_no3': 'ECO_no3'}, # fields to track at particle locations
                         },
            'release_groups' :rg,
            'max_run_duration': duration_sec,
            'write_tracks': True,
            'tracks_writer': {'update_interval':3600},
            'dispersion': {'A_H': 1.0, 'A_V': 0.001},
            'particle_properties':{'eDNA': { 'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay', 'decay_time_scale': 1. * 3600 * 24}
                                   },
            'particle_statistics': {'Gs1':{  'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                                            'update_interval': 1800, 'particle_property_list': ['eDNA'],
                                            'release_group_centered_grids': True,
                                            'grid_span': [25000., 25000.],
                                            'grid_size': [150, 151]}
                                    }
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
          [294455, 5760000],
          ]

    params = set_params(args, x0, duration_sec=7. * 24 * 3600)

    params['reader']['input_dir'] = r'F:\Hindcasts\Hindcast_samples_tests\Deakin_EricT\PPB_Hydro_netCDF'
    params['reader']['file_mask']= 'schout_*.nc'
    params['root_output_dir'] = 'F:\\OceanTrackerOuput\\Deakin\\portPhillipBay'

    if not args.norun:
        caseInfoFile = run(params)
    else:
        run_info_file = path.join(
            params['root_output_dir'],
            params['output_file_base'],
            params['output_file_base'] + '_runInfo.json'
        )

    # do plots
    if not args.noplots:
        from oceantracker.post_processing.read_output_files import load_output_files
        from oceantracker.post_processing.plotting import plot_tracks, plot_statistics


        ax = None
        ax=[ 217641,      404133,     5702747,     5815571]

        track_data = load_output_files.load_track_data(
            caseInfoFile, var_list=['tide', 'water_depth','eDNA'], fraction_to_read=.02)

        plot_tracks.animate_particles(track_data, axis_lims=ax, title='Port Phillip Bay Schism test',show_dry_cells = False)

        dx=25000
        #ax = [217641+dx, 404133-dx, 5702747+dx, 5815571-dx]
        stats = load_output_files.load_stats_data(caseInfoFile,var_list=['eDNA'],name='Gs1')

        # heat map of particle counts
        plot_statistics.animate_heat_map(stats, title='Port Phillip Bay, time based particle count heatmaps, built on the fly',
                                         logscale=False, release_group='P1')

        # aminmate decaying particles
        plot_statistics.animate_heat_map(stats,var='eDNA', title='eDNA heatmaps, built on the fly, 1 day exp. decay',
                                         logscale=False, release_group='P1')