from oceantracker.main import run
from plot_oceantracker import plot_tracks
from read_oceantracker.python import load_output_files
from oceantracker.util import  cord_transforms
from os import path
import numpy as np
import argparse


def default_params():
    params = { 'user_note' : '',
        'debug' : True,
        'time_step': 3600,
        'dev_debug_plots' :False,
        'use_A_Z_profile': True,
        'max_run_duration': 5. * 24 * 3600,
        'write_tracks': True,
        'output_file_base': None,
        'root_output_dir': None,
         'EPSG_code_metres_grid': None,
        'regrid_z_to_uniform_sigma_levels': True,
        'particle_properties': {'part_decay':
                                    {'class_name': 'AgeDecay', 'decay_time_scale': 1. * 3600 * 24}},
        'release_groups': {'P1': {'points': [], 'pulse_size': 10,
                                  'coords_allowed_in_lat_lon_order': True, # only used if hydro-model is in
                                  'release_interval': 3600,'z_min':-1.},
                        'Poly1': {'class_name':'PolygonRelease',
                                            'points': [], 'pulse_size': 10,
                                         'coords_allowed_in_lat_lon_order': True,  # only used if hydro-model is in
                                         'release_interval': 3600, 'z_min': -1.}},
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

    nested_readers={}
    hgrid_file=None
    time_step=3600.
    fall_vel=0.
    reader_class = None
    pulse_size = 10
    open_boundary_type = 0
    reader= None
    is3D=True
    water_depth_file = None
    poly_points=None
    title = ''

    params= default_params()
    show_grid = True
    geo_cords= False
  

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

        case 120:
            root_input_dir = r'G:\Hindcasts_large\2024_hauraki_gulf_auck_uni\2020\01'
            output_file_base = 'Test Hauraki'
            file_mask = 'schout*.nc'
            params['EPSG_code_metres_grid'] = 2193
            x0=[[-36.832885812299395, 174.76309434822716],
                [-36.70276297564815, 174.81729496997661]]
            ax = None # Auck
            title = 'Auckland test'
            poly_points=[[-36.80778038251076, 175.17304722424294],
                        [-36.78224101024911, 175.19670975597626],
                         [-36.78141701777142, 175.16790319560525],
                         [-36.80778038251076, 175.17304722424294]]
            geo_cords = True

        case 141:
            #schism v5,
            root_input_dir = r'F:\Hindcasts\Hindcast_samples_tests\WHOI_calvin\SCHISM_v2'
            output_file_base = 'Xlavin Schim v5'
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
            root_input_dir=r'F:\Hindcasts\colaborations\LakeSuperior\historical_sample\2022'
            x0 = [[439094.44415005075, 5265627.962025132, -10]]
            file_mask = 'nos.lsofs.fields.n000*.nc'
            output_file_base = 'FVCOM_Lake_Superior'

            max_days=30
            title = 'FVCOM test'
        case 300:
            #ROMS
            root_input_dir = r'F:\Hindcasts\Hindcast_samples_tests\ROMS_samples'
            x0 =  [[616042, 4219971, -1], [616042, 4729971, -1], [616042, 4910000, -1],
                   [387649.9416260512, 4636593.611571449, -1], [-132118.97253055905, 4375233.36585782, -1], [-178495.6601573273, 4132294.9876834783, -1]]
            file_mask  =  'DopAnV2R3-ini2007_da_his.nc'
            output_file_base= 'ROMS'
            title = 'ROMS test'

        case 400:
            # DELFT FM
            root_input_dir = r'F:\Hindcast_reader_tests\Delft3D\DELF3DFM_silawasi'
            x0= [[-0.4876992148036644, 129.18935660697986],
                 [-2.788645108730445, 123.88768495956097]]

            file_mask = 'NSulawesi_*.nc'
            output_file_base = 'DELF3D-FM'
            title = 'DELF3D-FM test'
            is3D = False

        case 401:
            # DELFT FM exmouth
            root_input_dir = r'F:\Hindcast_reader_tests\Delft3D\AIMS_Exmouth'

            x0=[[230372.0534805571, 7581341.601568772]]
            file_mask = 'Exmouth_FlowFM*.nc'
            output_file_base = 'DELF3D-FM_Exmouth'
            title = 'DELF3D-FM test'
            #reader = 'oceantracker.reader.dev_delft_fm.DELFTFM'
            is3D = False
            show_grid = False

        case 402:
            # DELFT FM AIMS_Grenvelingen
            root_input_dir = r'F:\Hindcast_reader_tests\Delft3D\AIMS_Grenvelingen'

            x0=[[57706.375512704304, 421967.24984360463]]
            file_mask = 'Grevelingen-FM_*_map.nc'
            output_file_base = 'DELF3D-FM_Grevelingen'
            title = 'DELF3D-FM test'
            #reader = 'oceantracker.reader.dev_delft_fm.DELFTFM'
            is3D = True
            show_grid = False
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
        case 1100:
            #OCEANUM GLORYS
            x0 =  [
                #[-73.48272505246274, -173.7097571108972],
                   [-70., -130],
                [-69.52499266063822,-130],
                [-70.5, -130],
                [-71, -130],
                [-71, -125],
                [-71.3, -128.2],
                [-71.46114498134901, 171.2627422568032],
                  # [-76.,- 160.]
                   ]

            x0 = [       # [-73.48272505246274, -173.7097571108972],
                [-72.,176],
                [-70.72144746302578, 170.34],
                [-73.55945050776178, 171.22711508577942],
                [-74.55945050776178, 175.],
                [-67., 169],
                 ]

            x0 = np.flip(np.asarray(x0), axis=1)
            #x0[:,0] += -90. + 360 # todo hack to get ross sea right acros date line in utm transform
            x0 = cord_transforms.WGS84_to_UTM(x0).tolist()


            file_mask  =  'RossSea*.nc'
            output_file_base= 'GLORYS'
            title = 'GLORYS test'
            root_input_dir = r'F:\Hindcasts\Hindcast_samples_tests\Glorys\Antartica'
            reader = 'oceantracker.reader.dev.dev_ross_sea_GLORYS_reader.GLORYSreaderSurface'
            is3D = False
            water_depth_file = r'F:\Hindcasts\Hindcast_samples_tests\Glorys\Ross_sea2D\static.nc'
            open_boundary_type = 1
            max_days = 90
            time_step = 3600.
            pulse_size = 5
            params['particle_properties']['part_decay']['decay_time_scale']= 28*24*3600.
        case 1000:
            # nested schisim
            pulse_size = 1
            root_input_dir = r'G:\Hindcasts_large\OceanNumNZ-2022-06-20\final_version\2012\07'
            output_file_base = 'shared_reader'
            file_mask = 'NZfinite*.nc'
            max_days = 7
            open_boundary_type = 1

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
                   input_dir = r'F:\Hindcasts\2023WhangareiHarbour2012\sample_schism_standard',
                    file_mask = 'schout*.nc',
                    hgrid_file_name=r'F:\Hindcasts\2023WhangareiHarbour2012\sample_schism_standard\hgrid_Whangarei.gr3',
                #          input_dir = r'F:\Hindcasts\2023WhangareiHarbour2012\resampled_outputs',
                    #file_mask = 'Whangarei*.nc',
                   #hgrid_file_name=r'F:\Hindcasts\2023WhangareiHarbour2012\resampled_outputs\hgrid_Whangarei.gr3'

            ))

        case 2000:
            root_input_dir = 'dummy_data_dir'
            file_mask = 'single_ocean_gyre2D.nc'
            output_file_base = 'dummy_data_single_ocean_grye'
            x0 = [[20000, 10000],
                   ]
            reader ='oceantracker.reader.dummy_data_reader.DummyDataReader'

    params['release_groups']['P1']['points'] = x0
    params['release_groups']['Poly1']['points'] = poly_points

    params['particle_statistics'] = {'grid1':
                                      {'class_name': 'GriddedStats2D_timeBased',
                                       'grid_center': x0[0],
                                       'coords_allowed_in_lat_lon_order': True,
                                       'grid_span' : [.1,.15] if geo_cords else [10000,10000],
                                       'update_interval': 3600, 'particle_property_list': ['water_depth'], 'status_min': 'moving', 'z_min': -2,
                                       'grid_size': [120, 121]},
                                     'poly1':
                                         {'class_name': 'PolygonStats2D_timeBased',
                                          'coords_allowed_in_lat_lon_order': True,
                                          'polygon_list':[dict(points=poly_points)],
                                            'update_interval': 3600, 'particle_property_list': ['water_depth'], 'status_min': 'moving', 'z_min': -2,
                                          'grid_size': [120, 121]}
                                     }

    params.update(note=title,output_file_base=output_file_base,
                  max_run_duration= max_days*24*3600, time_step= time_step, open_boundary_type=open_boundary_type)
    params['reader'].update(input_dir=root_input_dir,
                            file_mask=file_mask,
                            class_name=reader)
    if water_depth_file is not None:
        params['reader']['water_depth_file'] = water_depth_file
        params['reader']['load_fields'] = ['water_depth']

    if params['reader']['class_name'] is  None:   del params['reader']['class_name']

    if poly_points is None:
        del params['release_groups']['Poly1']
        del params['particle_statistics']['poly1']

    params['release_groups']['P1'].update(pulse_size=pulse_size)

    if is3D:
        params['velocity_modifiers'] = {'fall_vel': {'class_name': 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': fall_vel}}

    if hgrid_file is not None:
        params['reader']['hgrid_file_name']= hgrid_file

    if nested_readers is not None: params['nested_readers']=nested_readers
    plot_opt=dict(ax=ax,show_grid=show_grid)
    return params, plot_opt


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--test', default=None, type= int)
    parser.add_argument('-uniform', action='store_false')
    parser.add_argument('-noplots', action='store_true')
    parser.add_argument('-skip_run', action='store_true')
    parser.add_argument('-debug_plots', action='store_true')
    parser.add_argument('-save_plot', action='store_true')
    args = parser.parse_args()

    root_output_dir = r'F:\OceanTrackerOutput\test_reader_formats'

    if args.test is None:
        tests =[100]
    else:
        tests=[args.test]


    for n in tests:
        params, plot_opt= get_case(n)
        #params['display_grid_at_start'] = True # ti use giput to get cords
        params.update( root_output_dir = root_output_dir,
                    regrid_z_to_uniform_sigma_levels = args.uniform,
                    debug_plots = args.debug_plots,
                    use_A_Z_profile = True,
                    debug=True,
                    #numba_cache_code=True
                    #display_grid_at_start=True
                       )

        if not args.skip_run:
            caseInfoFile= run(params)

        else:
            caseInfoFile= path.join(params['root_output_dir'],params['output_file_base'],
                                    params['output_file_base']+'_caseInfo.json')

        # do plot
        if not args.noplots:
            track_data = load_output_files.load_track_data(caseInfoFile)
            if False:
                plot_utilities.display_grid(track_data['grid'], ginput=3, axis_lims=None)
            plot_base = path.join(params['root_output_dir'],params['output_file_base'],params['output_file_base'])

            plot_file = plot_base + '_tracks_01.mp4' if args.save_plot else None

            plot_tracks.animate_particles(track_data, axis_lims=plot_opt['ax'],
                                          title=params['user_note'], movie_file=plot_file, aspect_ratio=None,
                                          show_grid=plot_opt['show_grid'])

            plot_file = plot_base + '_decay_01.mp4' if args.save_plot else None
            plot_tracks.animate_particles(track_data, axis_lims=plot_opt['ax'],
                              title='Ross Sea',
                              colour_using_data=track_data['part_decay'], part_color_map='hot_r',
                              size_using_data=track_data['part_decay'],
                              vmax=1.0, vmin=0,
                              movie_file=plot_file,
                              fps=24,
                              aspect_ratio=None,
                              interval=20, show_dry_cells=False)




