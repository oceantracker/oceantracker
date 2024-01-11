from oceantracker.main import run
from oceantracker.post_processing.plotting import plot_statistics, plot_tracks, plot_utilities
from oceantracker.post_processing.read_output_files import load_output_files
from oceantracker.util import  cord_transforms
from os import path
import numpy as np
import argparse


def run_params(d):
    params = { 'user_note' : d['title'],
        'debug' : True,
        'time_step': d['time_step'],
        'dev_debug_plots' :d['debug_plots'],
        'use_A_Z_profile': d['use_A_Z_profile'],
        'max_run_duration': 5. * 24 * 3600 if d['max_days'] is None else  d['max_days']*24*3600.,
        'write_tracks': True,
        'output_file_base': d['output_file_base'],
        'root_output_dir': d['root_output_dir'],
        'regrid_z_to_uniform_sigma_levels': d['regrid_z_to_uniform_sigma_levels'],
        'release_groups': {'P1': {'points': d['x0'], 'pulse_size': d['pulse_size'], 'release_interval': 3600,'z_min':-1.}},
        'dispersion': {'A_H': 1.0, 'A_V': 0.001},
        'reader': {'file_mask': d['file_mask'],
                   'input_dir': d['root_input_dir'],
                   # 'field_map': {'ECO_no3': 'ECO_no3'}, # fields to track at particle locations
                   },
        'nested_readers': d['nested_readers'],
        'resuspension': {'critical_friction_velocity': 0.01}
        }
    if d['hgrid_file'] is not None:
        params['reader']['hgrid_file_name']= d['hgrid_file']
        params['open_boundary_type'] = 1

    if d['reader'] is not  None:  params['reader']['class_name'] = d['reader']

    params['velocity_modifiers'] = {'fall_vel': {'class_name': 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': -d['fall_vel']}}

    params['tracks_writer']= dict(turn_on_write_particle_properties_list=['n_cell','nz_cell','bc_cords'])

    return  params
def get_case(n):
    max_days = None
    ax = None

    nested_readers={}
    hgrid_file=None
    time_step=3600.
    fall_vel=0.
    reader = None
    pulse_size = 10
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
            title = 'NZ national test'
        case 101:
            root_input_dir = r'F:\Hindcasts\Hindcast_samples_tests\Auckland_uni_hauarki\new_format\01'
            output_file_base = 'SchismV5 test Hauarki'
            file_mask = '*.nc'

            x0 = [[-36.81612195216445, 174.82731398519584],
                  [-37.070731274878, 175.39302783837365],
                  [-36.4051733326401, 174.7771263023033],
                  [-36.85502113978176, 174.6807647189683]
                  ]
            x0= cord_transforms.WGS84_to_UTM(np.flip(np.asarray(x0),axis=1)).tolist()
            ax = None # Auck
            title = 'test schisim v5 - auckland test'


        case 102:
            #schism v5, WHOI, not working
            root_input_dir = r'F:\Hindcasts\Hindcast_samples_tests\WHOI_calvin\schism'
            output_file_base = 'SchismV5 test Hauarki'
            file_mask = '*.nc'

            x0 = [[-36.81612195216445, 174.82731398519584],
                  [-37.070731274878, 175.39302783837365],
                  [-36.4051733326401, 174.7771263023033],
                  [-36.85502113978176, 174.6807647189683]
                  ]
            x0= cord_transforms.WGS84_to_UTM(np.flip(np.asarray(x0),axis=1)).tolist()
            ax = None # Auck
            title = 'test schisim v5 - Calvin'

        case 150:
            root_input_dir = r'F:\Hindcasts\2023_Pelorus\Preliminary outputs'
            output_file_base = 'Pelourus_prelim'
            file_mask = 'schout*.nc'

            x0 = [[-41.26352277695916, 173.80657335148985],
                  [-41.07330690449923, 173.99402755852105],
                    ]
            x0=cord_transforms.WGS84_to_NZTM(np.flip(np.asarray(x0),axis=1)).tolist()
            ax=None# ax = [1727860, 1823449, 5878821, 5957660]  # Auck
            title= 'Pelourus prelim test'

        case 151:
            root_input_dir = r'F:\Hindcasts\2023WhangareiHarbour2012\schism_standard'
            output_file_base = 'WhangareiHarbour_test'
            file_mask = 'schout*.nc'
            hgrid_file = path.join(root_input_dir,'hgrid_Whangarei.gr3')

            x0 = [[-35.774216807463354, 174.34478905226064],
                  [-35.852727582604615, 174.50694708878515],
                  [-35.95198585006545, 174.5637958642573]
                    ]
            x0=cord_transforms.WGS84_to_NZTM(np.flip(np.asarray(x0),axis=1)).tolist()
            ax=None# ax = [1727860, 1823449, 5878821, 5957660]  # Auck
            title= 'Whangarei prelim test'
            time_step = 300.

        case 200:
            root_input_dir=r'F:\Hindcasts\colaborations\LakeSuperior\historical_sample\2022'
            x0 = [[439094.44415005075, 5265627.962025132, -10]]
            file_mask = 'nos.lsofs.fields.n000*.nc'
            output_file_base = 'FVCOM_Lake_Superior'

            max_days=30
            title = 'FVCOM test'
        case 300:
            root_input_dir = r'F:\Hindcasts\Hindcast_samples_tests\ROMS_samples'
            x0 =  [[616042, 4219971, -1], [616042, 4729971, -1], [616042, 4910000, -1],
                   [387649.9416260512, 4636593.611571449, -1], [-132118.97253055905, 4375233.36585782, -1], [-178495.6601573273, 4132294.9876834783, -1]]
            file_mask  =  'DopAnV2R3-ini2007_da_his.nc'
            output_file_base= 'ROMS'
            title = 'ROMS test'
        case 1000:
            # nested schisim
            pulse_size = 1
            root_input_dir = r'G:\Hindcasts_large\OceanNumNZ-2022-06-20\final_version\2012\07'
            output_file_base = 'shared_reader'
            file_mask = 'NZfinite*.nc'
            max_days = 7


            x0=[[-35.80822176918771, 174.43613622407605],# inside whargeri
                [-35.87936265079254, 174.52205865417034], # harbour jet
                [-35.94290227656262, 174.4761188861907],  # nearshore brembay
                [-35.91960370397214, 174.59610759097396],
                [-35.922300421719214, 174.665532083399], # hen and chickes, in outer grid
                ]
            x0 = cord_transforms.WGS84_to_NZTM(np.flip(np.asarray(x0), axis=1)).tolist()

            ax = [1727860, 1823449, 5878821, 5957660]  # Auck
            ax= None
            title = 'NZ national test'
            nested_readers= dict(nest1=dict(
                    class_name='oceantracker.reader.schism_reader.SCHISMreaderNCDF',
                    #input_dir = r'F:\Hindcasts\2023WhangareiHarbour2012\sample_schism_standard',
                    #file_mask = 'schout*.nc',
                    #hgrid_file_name=r'F:\Hindcasts\2023WhangareiHarbour2012\sample_schism_standard\hgrid_Whangarei.gr3',
                    input_dir = r'F:\Hindcasts\2023WhangareiHarbour2012\resampled_outputs',
                    file_mask = 'Whangarei*.nc',
                   hgrid_file_name=r'F:\Hindcasts\2023WhangareiHarbour2012\resampled_outputs\hgrid_Whangarei.gr3'
            ))



    return dict(x0=x0,root_input_dir=root_input_dir,output_file_base=output_file_base+f'_{n:02d}',title=title,time_step=time_step,reader= reader,
                file_mask=file_mask,ax=ax,max_days=max_days,nested_readers=nested_readers,hgrid_file=hgrid_file,    fall_vel= fall_vel,
                pulse_size=pulse_size
                )
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--test', default=None, type= int)
    parser.add_argument('-uniform', action='store_false')
    parser.add_argument('-noplots', action='store_true')
    parser.add_argument('-open', action='store_true')
    parser.add_argument('-norun', action='store_true')
    parser.add_argument('-debug_plots', action='store_true')
    parser.add_argument('-plot_file', action='store_true')
    args = parser.parse_args()

    root_output_dir = r'F:\OceanTrackerOutput\test_reader_formats'

    if args.test is None:
        tests =[100]
    else:
        tests=[args.test]


    for n in tests:
        d= get_case(n)
        d['root_output_dir'] = root_output_dir
        d['regrid_z_to_uniform_sigma_levels'] = args.uniform
        d['debug_plots'] = args.debug_plots
        d['use_A_Z_profile'] = True

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
            plot_file = path.join(params['root_output_dir'],params['user_note'].replace(' ','_') + '.mp4' ) if args.plot_file else None


            plot_tracks.animate_particles(track_data, axis_lims=ax, title=params['user_note'], movie_file=plot_file, show_grid=True)




