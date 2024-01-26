from oceantracker.main import run
from oceantracker.post_processing.read_output_files import load_output_files
from oceantracker.post_processing.plotting import plot_tracks, plot_utilities, plot_statistics
from oceantracker.util.cord_transforms import WGS84_to_NZTM
import argparse
import numpy as np

poly_points=[[1597682.1237, 5489972.7479],
                        [1598604.1667, 5490275.5488],
                        [1598886.4247, 5489464.0424],
                        [1597917.3387, 5489000],
                        [1597300, 5489000], [1597682.1237, 5489972.7479]]

x0=[[1702396.742672811, 5365321.02654298], [1754437.3985253456, 5429551.69667285], [1687962.108202765, 5434139.601682127],
    [1665170.580092166, 5432100.532789115], [1678465.638156682, 5462176.798961039], [1648836.6516129032, 5474411.212319109],
    [1600214.7249769587, 5499389.806258503],
    [1646937.3576036866, 5578913.493085961], [1739622.9052534562, 5549346.994137291], [1703156.4602764978, 5444334.946147186]]

x0 = WGS84_to_NZTM(np.asarray([[173.321831,-41.201488+.005]])).tolist()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-mode_debug', action='store_true')
    parser.add_argument('-noplots', action='store_true')
    args = parser.parse_args()


    params={'output_file_base': 'soundstest',
            'root_output_dir': 'F:\\OceanTrackerOtuput\\Sounds\\test',
            'max_run_duration': 5*24*3600.,
            'write_tracks': True,
            'reader': {'class_name': 'oceantracker.reader.schism_reader.SCHISMreaderNCDF',
                      'file_mask': 'schism_marl201701*.nc', 'input_dir': 'G:\\Hindcasts_large\\MalbroughSounds_10year_benPhD\\2017',
                        'field_variables_to_depth_average': ['water_velocity'],
                      },
        'tracks_writer': {'output_step_count': 3},
        'release_groups': {'mypoints':{'points': x0, 'pulse_size': 1000, 'release_interval': 0}},
        'dispersion': {'A_H': 1.0, 'A_V': 0.001},
        'particle_statistics': {'my_stats':{
                'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                'update_interval': 3600, 'particle_property_list': ['water_depth'],
                'grid_center': x0[0], 'grid_span': [25000., 25000.],
                'grid_size': [120, 121]}},
                }

    if args.mode_debug: params['debug'] = True

    case_info_file= run(params)

    # do plot
    if not args.noplots:

        track_data = load_output_files.load_track_data(case_info_file, fraction_to_read=0.99)

        plot_tracks.plot_tracks(track_data)
        #plot_utilities.display_grid(caseInfoFile, ginput=10)

        #plot_tracks.animate_particles(caseInfoFile, title='metocean sounds Schism test, fall velocity and critical friction  resuspension')

        #plot_statistics.plot_heat_map(caseInfoFile, var='water_depth', title='Water_depth, Time based Heat maps built on the fly, no tracks recorded')



