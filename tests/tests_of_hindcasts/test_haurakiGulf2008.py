from oceantracker.main import run
from oceantracker.post_processing.plotting import plot_statistics
from oceantracker.post_processing.read_output_files import load_output_files
import argparse


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-depthaverage', action='store_true')
    parser.add_argument('-noplots', action='store_true')
    parser.add_argument('-mode_debug', action='store_true')
    args = parser.parse_args()

    x0 =[[1780846.7742,       5938985.617],
    [1652889.7849,      5820893.2627],
    [1701814.5161,      5492354.2771],
    [ 1530577.957,      4974564.7237],
    [1208803.7634,      4827706.2831],
    [1589852.1505,      6125208.1756]]
    x0=[ [1750624.1218,      5921952.0475],
        [1814445.5871,      5882261.7676],
        [1838293.4656,      5940629.8263],
        [1788021.4244,      5940860.2283]
         ]

    case ={'run_params':{
                'duration': 8. * 24 * 3600,
                'write_tracks': True},
        'tracks_writer' : {'output_step_count': 3},
        'particle_release_groups': [ {'points': x0 ,'pulse_size':5, 'release_interval': 1800}],
        'dispersion': {'A_H': 1.0 ,'A_V': 0.001},

        'particle_statistics' : [{
                                 'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                                 'calculation_interval': 3600, 'particle_property_list': ['water_depth'],
                                'grid_center': x0[0],'grid_span': [25000.,25000.],

                                 'grid_size': [120, 121]}]
        }


    params={ 'shared_params': {'output_file_base': 'Hauraki_test',

                            'root_output_dir': 'F:\\OceanTrackerOuput\\HaurakiGulfBen2008\\test'},
             'reader': {"class_name": 'oceantracker.reader.generic_unstructured_reader.GenericUnstructuredReader',
                        'file_mask': 'HaurakiDepthAv2008Day*.nc', 'input_dir': 'F:\\HindcastReWrites\\oceantrackerFMT\\HaurakiGulfBen2008',
                        'search_sub_dirs': True,
                        'dimension_map': {'time': 'time', 'node': 'node'},
                        'grid_variables': {'time': 'time',
                                           'x': ['x', 'y'],
                                           'triangles': 'tri'},
                        'field_variables': {'water_depth': 'depth',
                                            'water_velocity': ['u', 'v']},
                        'time_buffer_size': 24, 'isodate_of_hindcast_time_zero': '1970-01-01'},
           'case_list': [case]
           }

    if args.mode_debug: params['debug'] = True

    run_info_file, has_errors= run(params)

    # do plot
    if not args.noplots:
        caseInfoFile = load_output_files.get_case_info_file_from_run_file(run_info_file)

        ax=[     1727860,     1823449,     5878821,     5957660] # Auck

        plot_tracks.animate_particles(caseInfoFile, axis_lims=ax, title='OceanNum NZ Schism test, fall velocity and critical friction  resuspension')

        plot_heat_maps.animate_heat_map(caseInfoFile, axis_lims=ax,
                                       title='OceanNum Schism, time based particle count heatmaps, built on the fly,  log scale', logscale=True)

        particle_plot.plot_heat_map(caseInfoFile, axis_lims=ax, var='water_depth',
                                    title='Water_depth, Time based Heat maps built on the fly, no tracks recorded')

