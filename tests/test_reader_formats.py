from oceantracker.main import run
from plot_oceantracker import plot_tracks, plot_utilities
from read_oceantracker.python import load_output_files
from oceantracker.util import  cord_transforms
from os import path
import numpy as np
import argparse


def default_params():
    params = { 'user_note' : '',
        'debug' : True,
        'time_step': 1800,
        'dev_debug_plots' :False,
        'use_A_Z_profile': True,
        'max_run_duration': 5. * 24 * 3600,
        'write_tracks': True,
        'output_file_base': None,
        'root_output_dir': None,
         'EPSG_code_metres_grid': None,
        'regrid_z_to_uniform_sigma_levels': True,
        'particle_properties': [{'name':'part_decay',  'class_name': 'AgeDecay',
                                'decay_time_scale': 1. * 3600 * 24}],
        'release_groups':[ {'name':'P1', 'points': [], 'pulse_size': 10,
                             #     'coords_in_lat_lon_order': True, # only used if hydro-model is in
                                'release_interval': 1800,'z_min':-2.},

                            ],
        'dispersion': {'A_H': 1.0, 'A_V': 0.001},
        'reader': {'file_mask':None,
                   'input_dir': None,
                   # 'field_map': {'ECO_no3': 'ECO_no3'}, # fields to track at particle locations
                   },
        'nested_readers': [],

        'resuspension': {'critical_friction_velocity': 0.00}
        }



    params['tracks_writer']= dict(turn_on_write_particle_properties_list=['n_cell','nz_cell','bc_cords'])

    return  params

def get_case(n):
    max_days = 5
    ax = None

    nested_readers=[]
    hgrid_file=None
    time_step=3600.
    fall_vel= -0.01
    pulse_size = 10
    open_boundary_type = 0
    reader= None
    is3D=True
    water_depth_file = None
    poly_points=None
    title = ''

    params= default_params()
    show_grid = False
    geo_cords= False
  

    match n:
        case 100:
            root_input_dir = r'G:\Hindcasts_large\2024_OceanNumNZ-2022-06-20\final_version\2022\01'
            output_file_base = 'NZnational'
            file_mask = 'NZfinite*.nc'

            x0 = [[1750624.1218, 5921952.0475],
                  [1814445.5871, 5882261.7676],
                  [1838293.4656, 5940629.8263],
                  [1788021.4244, 5940860.2283]
                  ]
            ax = [1727860, 1823449, 5878821, 5957660]  # Auck
            title = 'NZ national test'

        case 120:
            root_input_dir = r'G:\Hindcasts_large\2024_hauraki_gulf_auck_uni\2020\01'
            output_file_base = 'Test Hauraki'
            file_mask = 'schout*.nc'
            params['EPSG_code_metres_grid'] = 2193
            x0=[[-36.832885812299395, 174.76309434822716],
                [-36.70276297564815, 174.81729496997661]]
            ax = None # Auck
            title = 'Auckland test'

            geo_cords = True

        case 121:
            root_input_dir = r'Z:\Hindcasts\UpperSouthIsland\2020_MalbroughSounds_10year_benPhD\2009'
            output_file_base = 'SoundsBen_Phd'
            file_mask = 'schism_marl2009*.nc'
            params['EPSG_code_metres_grid'] = 2193
            x0=[[-40.788387332710876, 172.8418709119585],
                [-40.905652106497435, 173.88863555540422]]
            x0 = cord_transforms.WGS84_to_NZTM(np.flip(np.asarray(x0), axis=1)).tolist()
            ax = None # Auck
            title = 'Auckland test'

            geo_cords = True
        case 141:
            #schism v5,
            root_input_dir = r'F:\Hindcast_reader_tests\Schimsv5\WHOI_calvin\SCHISM_v5'
            output_file_base = 'Xlavin Schim v5'
            file_mask = '*.nc'

            x0 = [[-41.26352277695916, 173.80657335148985],
                  [-41.07330690449923, 173.99402755852105],
                  ]
            x0 = cord_transforms.WGS84_to_NZTM(np.flip(np.asarray(x0), axis=1)).tolist()
            ax = None # Auck
            title = 'test schisim v5 - Calvin'
        case 142:
            #schism v5 auckland,
            root_input_dir = r'F:\Hindcast_reader_tests\Schimsv5\HaurakiGulfv5\01'
            output_file_base = 'SchismV5 test Hauarki'
            file_mask = '*.nc'
            x0=[[-36.832885812299395, 174.76309434822716]]
            x0= np.flip(np.asarray(x0),axis=1)
            ax = None # Auck
            title = 'test schisim v5 - Auck'
        case 150:
            root_input_dir = r'F:\Hindcast_parts\pelorus2024'
            output_file_base = 'Pelourus_prelim'
            file_mask = 'pack2017*.nc'

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

        case 152:
            root_input_dir = r'G:\Hindcasts_large\2024_hauraki_gulf_auck_uni\2020'
            output_file_base = 'test_Hauarki'
            file_mask = 'schout*.nc'

            x0 = [[-36.81612195216445, 174.82731398519584],
                  [-37.070731274878, 175.39302783837365],
                  [-36.4051733326401, 174.7771263023033],
                  [-36.85502113978176, 174.6807647189683]
                  ]
            x0= cord_transforms.WGS84_to_UTM(np.flip(np.asarray(x0),axis=1)).tolist()
            ax = None # Auck
            title = 'test_ Hauarki'

        case 200:
            # FVCOM
            root_input_dir=r'F:\Hindcast_reader_tests\FVCOM_LakeSuperior\historical_sample\2022'
            x0 = [[47.540046778478064, -87.64392022390314]]
            x0 = np.flip(np.asarray(x0), axis=1)
            file_mask = 'nos.lsofs.fields.n000*.nc'
            output_file_base = 'FVCOM_Lake_Superior'

            max_days=30
            title = 'FVCOM test'
        case 300:
            #ROMS test
            root_input_dir = r'F:\Hindcast_reader_tests\ROMS_samples'
            x0 = [[41.91527213998341, -70.33170368895726], # cape code
                 [44.78577529626732, -66.39180546827933],
                  [33.85502775199189, -73.47506471772721],
                  [37.01033167397936, -75.88494735794337],
                  ]

            x0 = np.flip(np.asarray(x0), axis=1)
            file_mask  =  'DopAnV2R3-ini2007_da_his.nc'
            output_file_base= 'ROMS'
            title = 'ROMS test'
            show_grid = True
        case 301:
            #ROMS MOANA
            root_input_dir = r'F:\Hindcast_reader_tests\MOANA_project_National_hindcast\Hourly_nestfiles'
            x0 =  [[616042, 4219971, -1], [616042, 4729971, -1], [616042, 4910000, -1],
                   [387649.9416260512, 4636593.611571449, -1], [-132118.97253055905, 4375233.36585782, -1], [-178495.6601573273, 4132294.9876834783, -1]]
            x0 = [[-36.81612195216445, 174.82731398519584],
                  [-37.070731274878, 175.39302783837365],
                  [-36.4051733326401, 174.7771263023033],
                  [-36.85502113978176, 174.6807647189683]
                  ]
            x0 = np.flip(np.asarray(x0),axis=1)
            file_mask  =  'nz5km_his*.nc'
            output_file_base= 'ROMS'
            title = 'ROMS test'
            show_grid = True
        case 400:
            # DELFT FM
            root_input_dir = r'F:\Hindcast_reader_tests\Delft3D\DELF3DFM_silawasi'
            x0= [[-0.4876992148036644, 129.18935660697986],
                 [-2.788645108730445, 123.88768495956097]]
            x0 = np.flip(np.asarray(x0),axis=1)
            file_mask = 'NSulawesi_*.nc'
            output_file_base = 'DELF3D-FM-z-layer'
            title = 'DELF3D-FM test-z-layer'
            is3D = True

        case 401:
            # DELFT FM exmouth
            root_input_dir = r'F:\Hindcast_reader_tests\Delft3D\AIMS_Exmouth'

            x0=[[230372.0534805571, 7581341.601568772]]
            file_mask = 'Exmouth_FlowFM*.nc'
            output_file_base = 'DELF3D-FM_Exmouth'
            title = 'DELF3D-FM test'
            reader = 'oceantracker.reader.dev_delft_fm.DELFTFM'
            is3D = False
            show_grid = False
        case 402:
            # DELFT FM -sigma
            root_input_dir = r'F:\Hindcast_reader_tests\Delft3D\AIMS_FlowFM'

            x0=[[230372.0534805571, 7581341.601568772]]
            file_mask = 'FlowFM_map*.nc'
            output_file_base = 'DELF3D-FM-sigma'
            title = 'DELF3D-FM sigma'
            #reader = 'oceantracker.reader.dev_delft_fm.DELFTFM'

            show_grid = True

        case 403:
            # DELFT FM AIMS_Uralia
            root_input_dir = r'F:\Hindcast_reader_tests\Delft3D\AIMS_Uralia'

            x0=[[230372.0534805571, 7581341.601568772]]
            file_mask = 'Uralia_FlowFM_map*.nc'
            output_file_base = 'DELF3D-FM_Uralia'
            title = 'DELF3D-FM AIMS_Uralia'
            #reader = 'oceantracker.reader.dev_delft_fm.DELFTFM'
            is3D = False
            show_grid = False
        case 404:
            # Grenvelingen
            root_input_dir = r'F:\Hindcast_reader_tests\Delft3D\Grenvelingen'

            x0=[[57706.375512704304, 421967.24984360463]]
            file_mask = 'Grevelingen-FM_*_map.nc'
            output_file_base = 'DELF3D-FM_Grevelingen'
            title = 'DELF3D-FM test'
            #reader = 'oceantracker.reader.dev_delft_fm.DELFTFM'
            is3D = True
            show_grid = False
        case 500:
            # NEMO
            root_input_dir = r'F:\Hindcast_reader_tests\NEMO\NemoNorthSeaORCA025-N006_data'
            file_mask = '*.nc'
            x0=[[57706.375512704304, 421967.24984360463]]

            output_file_base = 'Nemo01'
            title = 'Nemo test'
            reader = 'oceantracker.reader.dev.dev_nemo_reader.NemoReader'
            is3D = True

        case   1100:
            # batic sea GLORYS


            x0 = [ [58.36351222050503, 21.7318678553635],
                [55.54839701166633, 16.870008930959628],

                   ]
            x0=np.asarray(x0)
            x0[:,:2] = np.flip(x0[:,:2], axis=1)
            # x0[:,0] += -90. + 360 # todo hack to get ross sea right acros date line in utm transform

            file_mask = '*.nc'
            output_file_base = 'GLORYS'
            title = 'GLORYS test'
            root_input_dir = r'F:\Hindcast_reader_tests\Glorys\BalticSea'
            # reader = 'oceantracker.reader.dev.dev_ross_sea_GLORYS_reader.GLORYSreader'
            open_boundary_type = 1
            max_days =10
            time_step = 1800.
            pulse_size = 10
            fall_vel = -0.01
            is3D =True



        case 2000:
            # nested schisim
            pulse_size = 5
            root_input_dir = r'Z:\Hindcasts\NZ_region\2024_OceanNumNZ-2022-06-20\final_version\2012\09'
            output_file_base = 'shared_reader'
            file_mask = 'NZfinite*.nc'
            max_days =5# 30
            open_boundary_type = 1

            x0=[[-35.80822176918771, 174.43613622407605],# inside whargeri
                [-35.87936265079254, 174.52205865417034], # harbour jet
                [-35.94290227656262, 174.4761188861907],  # nearshore brembay
                [-35.91960370397214, 174.59610759097396],
                [-35.922300421719214, 174.665532083399],  # hen and chickes, in outer grid
                [-35.922300421719214, 174.665532083399], # hen and chickes, in outer grid
                ]
            x0 = cord_transforms.WGS84_to_NZTM(np.flip(np.asarray(x0), axis=1)).tolist()
            x0=[   [ 1727195 ,    6035149],
                    [1737357,     6029638],
                    [1742484 ,    6021345],
                    [1743472 ,    6019861]]
            ax=  [  1715000 ,    1755000 ,    6010000 ,    6050000] # northland
            title = 'nested test'
            nested_readers= [dict(name='nest1',
                    input_dir = r'D:\Hindcasts\NorthIsland\2023WhangareiHarbour2012\Existing_Sep2012_temp',
                    hgrid_file_name=r'D:\Hindcasts\NorthIsland\2023WhangareiHarbour2012\hgrid.gr3',
                    # input_dir = r'F:\Hindcasts\2023WhangareiHarbour2012\2012_outputs\Existing_Sep2012_temp',
                    #  hgrid_file_name=r'F:\Hindcasts\2023WhangareiHarbour2012\hgrid.gr3',
                    file_mask = 'schout*.nc',

            )]


        case 3000:
            root_input_dir = 'dummy_data_dir'
            file_mask = 'single_ocean_gyre2D.nc'
            output_file_base = 'dummy_data_single_ocean_grye'
            x0 = [[20000, 10000],
                   ]
            reader ='oceantracker.reader.dummy_data_reader.DummyDataReader'

    params['release_groups'][0]['points'] = x0

    params['particle_statistics'] = [{ 'name' :'grid1','class_name': 'GriddedStats2D_timeBased',
                                       'grid_center': x0[0][:2],
                                       'grid_span' : [.1,.15] if geo_cords else [10000,10000],
                                       'update_interval': 3600, 'particle_property_list': ['water_depth'], 'status_min': 'moving', 'z_min': -2,
                                       'grid_size': [120, 121]},
                                     ]

    params.update(user_note=title,output_file_base=output_file_base,

                  max_run_duration= max_days*24*3600, time_step= time_step, open_boundary_type=open_boundary_type)
    params['reader'].update(input_dir=root_input_dir,
                            file_mask=file_mask,
                            class_name=reader)
    if water_depth_file is not None:
        params['reader']['water_depth_file'] = water_depth_file
        params['reader']['load_fields'] = ['water_depth']

    if params['reader']['class_name'] is  None:   del params['reader']['class_name']


    params['release_groups'][0].update(pulse_size=pulse_size)

    if is3D:
        params['velocity_modifiers'] = [
           {'name':'fall_vel',
              'class_name': 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity',
              'value': fall_vel}]

    if hgrid_file is not None:
        params['reader']['hgrid_file_name']= hgrid_file


    if nested_readers is not None:
        params['nested_readers']=nested_readers

    plot_opt=dict(ax=ax,show_grid=show_grid)
    return params, plot_opt


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--test', default=None, type= int)
    parser.add_argument('-uniform', action='store_false')
    parser.add_argument('-gridplot', action='store_true')
    parser.add_argument('-noplots', action='store_true')
    parser.add_argument('-skip_run', action='store_true')
    parser.add_argument('-debug_plots', action='store_true')
    parser.add_argument('-save_plot', action='store_true')
    args = parser.parse_args()

    root_output_dir = r'D:\OceanTrackerOutput\test_reader_formats'

    if args.test is None:
        tests =[100]
    else:
        tests=[args.test]


    for n in tests:
        params, plot_opt= get_case(n)
        #params['display_grid_at_start'] = True # ti use giput to get cords
        params.update( root_output_dir = root_output_dir,
                    regrid_z_to_uniform_sigma_levels = args.uniform,
                    dev_debug_plots = args.debug_plots,
                    use_A_Z_profile = True,
                    debug=True,
                       display_grid_at_start=args.gridplot,
                    #NUMBA_cache_code=True
                    #display_grid_at_start=True
                       )

        if not args.skip_run:
            caseInfoFile= run(params)

        else:
            caseInfoFile= path.join(params['root_output_dir'],params['output_file_base'],
                                    params['output_file_base']+'_caseInfo.json')

        # do plot
        if not args.noplots and caseInfoFile is not None:
            track_data = load_output_files.load_track_data(caseInfoFile)
            if False:
                plot_utilities.display_grid(track_data['grid'], ginput=3, axis_lims=None)
            plot_base = path.join(params['root_output_dir'],params['output_file_base'],params['output_file_base'])

            plot_file = plot_base + '_tracks_01.mp4' if args.save_plot else None

            plot_tracks.animate_particles(track_data, axis_lims=None,
                                          title=params['user_note'], movie_file=plot_file, aspect_ratio=None,
                                          show_grid=plot_opt['show_grid'])

            plot_tracks.plot_path_in_vertical_section(track_data, particleID=0,)

            plot_file = plot_base + '_decay_01.mp4' if args.save_plot else None
            plot_tracks.animate_particles(track_data, axis_lims=plot_opt['ax'],
                              title='Ross Sea',
                              colour_using_data=track_data['hydro_model_gridID'],
                           #part_color_map='hot_r',
                            part_color_map='hot',
                              #size_using_data=track_data['part_decay'],
                              vmax=1, vmin=-1,
                              movie_file=plot_file,
                              fps=24,
                              aspect_ratio=None,
                              interval=20, show_dry_cells=False)




