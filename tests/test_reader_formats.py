from oceantracker.main import run
from oceantracker.post_processing.plotting import plot_statistics, plot_tracks, plot_utilities
from oceantracker.post_processing.read_output_files import load_output_files
from os import path
import argparse


def run_params(d):
    params = {
        'max_run_duration': 5. * 24 * 3600 if d['max_days'] is None else  d['max_days']*24*3600.,
        'write_tracks': True,
        'output_file_base': d['output_file_base'],
        'root_output_dir': d['root_output_dir'],
        'regrid_z_to_uniform_sigma_levels': d['regrid_z_to_uniform_sigma_levels'],
        'release_groups': {'P1': {'points': d['x0'], 'pulse_size': 5, 'release_interval': 3600}},
        'dispersion': {'A_H': 1.0, 'A_V': 0.001},
        'particle_statistics': {'S1': {
            'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
            'update_interval': 3600, 'particle_property_list': ['water_depth'],
            'grid_center': d['x0'][0], 'grid_span': [25000., 25000.],
            'grid_size': [120, 121]}},
        'reader': {'file_mask': d['file_mask'],
                   'input_dir': d['root_input_dir'],
                   # 'field_map': {'ECO_no3': 'ECO_no3'}, # fields to track at particle locations
                   },
        'resuspension': {'critical_friction_velocity': 0.01}
        }

    params['velocity_modifiers'] = {'fall_vel': {'class_name': 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': 0.000}}

    params['tracks_writer']= dict(turn_on_write_particle_properties_list=['n_cell','nz_cell','bc_cords'])

    return  params
def get_case(n):
    max_days = None
    ax = None
    match n:
        case 100:
            root_input_dir = r'G:\Hindcasts_large\OceanNumNZ-2022-06-20\final_version\2022\01'
            output_file_base = 'NZnational'
            file_mask = 'NZfinite*.nc'

            x0 = [[1750624.1218, 5921952.0475],
                  [1814445.5871, 5882261.7676],
                  [1838293.4656, 5940629.8263],
                  [1788021.4244, 5940860.2283]
                  ]
            ax = [1727860, 1823449, 5878821, 5957660]  # Auck
        case 200:
            root_input_dir=r'F:\Hindcasts\colaborations\LakeSuperior\historical_sample\2022'
            x0 = [[439094.44415005075, 5265627.962025132, -10]]
            file_mask = 'nos.lsofs.fields.n000*.nc'
            output_file_base = 'FVCOM_Lake_Superior'

            max_days=30

        case 300:
            root_input_dir = r'F:\Hindcasts\Hindcast_samples_tests\ROMS_samples'
            x0 =  [[616042, 4219971, -1], [616042, 4729971, -1], [616042, 4910000, -1],
                   [387649.9416260512, 4636593.611571449, -1], [-132118.97253055905, 4375233.36585782, -1], [-178495.6601573273, 4132294.9876834783, -1]]
            file_mask  =  'DopAnV2R3-ini2007_da_his.nc'
            output_file_base= 'ROMS'



    return dict(x0=x0,root_input_dir=root_input_dir,output_file_base=output_file_base+f'_{n:02d}',
                file_mask=file_mask,ax=ax,max_days=max_days)
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--test', default=None, type= int)
    parser.add_argument('-uniform', action='store_false')
    parser.add_argument('-noplots', action='store_true')
    parser.add_argument('-open', action='store_true')
    parser.add_argument('-norun', action='store_true')
    args = parser.parse_args()

    root_output_dir = r'F:\OceanTrackerOuput\test_reader_formats'

    if args.test is None:
        tests =[100]
    else:
        tests=[args.test]

    for n in tests:
        d= get_case(n)
        d['root_output_dir'] = root_output_dir
        d['regrid_z_to_uniform_sigma_levels'] = args.uniform

        params=  run_params(d)
        params['open_boundary_type'] = 1 if args.open else 0

        if not args.norun:
            caseInfoFile= run(params)

        else:
            caseInfoFile= path.join(d['root_output_dir'], d['output_file_base'],
                                    d['output_file_base']+'_caseInfo.json')


    # do plot
    if not args.noplots:
        track_data = load_output_files.load_track_data(caseInfoFile)
        if False:
            plot_utilities.display_grid(track_data['grid'], ginput=3, axis_lims=None)

        ax= d['ax']

        plot_tracks.animate_particles(track_data, axis_lims=ax, title='OceanNum NZ Schism test, fall velocity and critical friction  resuspension')
        #plot_tracks.plot_path_in_vertical_section(track_data, title='OceanNum, fall velocity and critical friction  resuspension ')

        stats_data = load_output_files.load_stats_data((caseInfoFile))
        plot_statistics.animate_heat_map(stats_data, axis_lims=ax, title='OceanNum Schism, time based particle count heatmaps, built on the fly,  log scale', logscale=True)

        plot_statistics.plot_heat_map(stats_data, axis_lims=ax, var='water_depth', title='Water_depth, Time based Heat maps built on the fly, no tracks recorded')


