from oceantracker.main import run

from oceantracker.post_processing.read_output_files import load_output_files
import oceantracker.util.basic_util  as basic_util
from os import path
import argparse


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-mode_debug', action='store_true')
    parser.add_argument('-noplots', action='store_true')
    args = parser.parse_args()

    x0 =[[ 312197,    5795541],
         [294455,  5758887],
         [249697,  5734360],
         [343044,  5744852],
         [361391,  5766517],
         [394052,  5721500],
         ]

    case ={'run_params':{
                'duration': 8. * 24 * 3600,
                'write_tracks': True},
        'tracks_writer' : {'output_step_count': 3},
        'particle_release_groups': [ {'points': x0 ,'pulse_size':50, 'release_interval': 1800}],

        'dispersion': {'A_H': 1.0 ,'A_V': 0.001},

        'particle_statistics' : [{
                                 'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                                 'calculation_interval': 3*3600, 'particle_property_list': ['water_depth'],
                                'grid_center': x0[1],
                                'grid_span': [35000.,35000.],
                                 'grid_size': [120, 121]}]
        }


    params={ 'shared_params': {'output_file_base': 'PPBtest',

                            'root_output_dir': 'F:\\OceanTrackerOuput\\Deakin\\portPhillipBay',
                             },
        'reader': {'class_name': 'oceantracker.reader.schism_reader.SCHSIMreaderNCDF',     'input_dir': 'F:\\Hindcasts\Deakin_EricT\\PPB_Hydro_netCDF',
                      'file_mask': 'schout_*.nc',
                      'depth_average': True,
                    'cords_in_lat_long': True,
                    #'field_map': {'ECO_no3': 'ECO_no3'}, # fields to track at particle locations
                      },
           'case_list': [case]
           }

    if args.mode_debug: params['debug'] = True

    run_info_file, has_errors = run(params)

    # do plot
    caseInfoFile = load_output_files.get_case_info_file_from_run_file(run_info_file)
    caseInfo = load_output_files.read_case_info_file(caseInfoFile)

    param_base = path.join(caseInfo['output_files']['root_output_dir'], 'PPG_rawparams')
    json_util.write_JSON('test_param_files/PPBtest.json', params)
    basic_util.write_YAML('test_param_files/PPBTest.yaml', params)

    if not args.noplots:
        ax=None
        ax=[ 217641,      404133,     5702747,     5815571]
        plot_tracks.animate_particles(caseInfoFile, axis_lims=ax, title='Port Phillip Bay Schism test')

        dx=25000
        ax = [217641+dx, 404133-dx, 5702747+dx, 5815571-dx]

        plot_tracks.animate_heat_map(caseInfoFile, axis_lims=ax, title='Port Phillip Bay, time based particle count heatmaps, built on the fly,  log scale', logscale=True)

