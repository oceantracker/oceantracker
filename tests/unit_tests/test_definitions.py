from os import path

import shutil
import numpy as np
from oceantracker import definitions

from copy import deepcopy

def base_settings(fn,args,label=None):
    s = path.split(fn)[-1].split('.')[0]
    if args.variant is not None: s+=f'_{args.variant:02d}'
    if label is not None: s += f'_{label}'
    d =  dict(output_file_base=s,
            root_output_dir=path.join(definitions.default_output_dir, 'unit_tests'),
            #root_output_dir=path.join('C:\oceantracker_output', 'unit_tests'),
            time_step=600.,  # 10 min time step
            use_random_seed = True,
            debug=True,

            )
    return d

image_dir= 'output'
reader_demo_schisim3D=   dict( # folder to search for hindcast files, sub-dirs will, by default, will also be searched
                 input_dir= path.join(path.dirname(definitions.package_dir),'tutorials_how_to','demo_hindcast','schsim3D'),  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                file_mask='demo_hindcast_schisim3D*.nc',
)  # file mask to search for
reader_demo_ROMS = deepcopy(reader_demo_schisim3D)
reader_demo_ROMS.update(input_dir=path.join(path.dirname(definitions.package_dir), 'tutorials_how_to', 'demo_hindcast', 'ROMS'),
                    file_mask='ROMS3D_00*.nc')

reader_demo_schisim2D=   dict( # folder to search for hindcast files, sub-dirs will, by default, will also be searched
                 input_dir= path.join(path.dirname(definitions.package_dir),'tutorials_how_to','demo_hindcast','schsim2D'),  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                file_mask='Random_order*.nc',)
reader_double_gyre=  dict(class_name='oceantracker.reader.generic_stuctured_reader.dev_GenericStructuredReader',
             input_dir=r'E:\H_Local_drive\ParticleTracking\hindcast_formats_examples\generic2D_structured_DoubleGyre',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
             file_mask='Double_gyre.nc',
             dimension_map=dict(time='t', rows='y', cols='x'),
             grid_variable_map=dict(time='Time', x=['x_grid', 'y_grid']),
             field_variable_map=dict(water_depth='Depth', water_velocity=['U', 'V'], tide='Tide'),
             )

reader_NZnational=dict(  input_dir = r'G:\Hindcasts_large\OceanNumNZ-2022-06-20\final_version\2022\01',
            file_mask = 'NZfinite*.nc')
reader_Sounds =dict(  input_dir = r'G:\Hindcasts_large\MalbroughSounds_10year_benPhD\2017',
            file_mask = 'schism_marl201701*.nc')
hydro_model = dict(demoSchism3D=dict(reader= reader_demo_schisim3D,
                            axis_lims=[1591000, 1601500, 5478500, 5491000],
                            x0=[[1594000, 5484200] ],
                            polygon=[[1597682., 5486972], [1598604, 5487275], [1598886, 5486464],
                                    [1597917., 5484000], [1597300, 5484000], [1597682, 5486972]],
                            ),
                demoROMS=dict(reader= reader_demo_ROMS,
                            axis_lims=None,
                            x0=[[-69.2, 43.4] ],
                            polygon= np.asarray([[-69., 43.5], [-69.2, 43.5], [-69.2, 43.7],[-69.1, 43.7],[-69., 43.5]]),
                            ),
                doubleGyre=dict(reader= reader_double_gyre,axis_lims=[0, 2, 0, 1]),
                NZnational=dict(reader= reader_NZnational,axis_lims= [1727860, 1823449, 5878821, 5957660],
                             x0=[[1750624.1218, 5921952.0475],
                                  [1814445.5871, 5882261.7676],
                                  [1838293.4656, 5940629.8263],
                                  [1788021.4244, 5940860.2283]
                                  ]),
                sounds = dict(reader=reader_Sounds,
                              axis_lims=None,#[1727860, 1823449, 5878821, 5957660],
                            x0=[[1667563.4554392125, 5431675.08653105],
                                [1683507.1281506484, 5452629.160486231]])
                   )
hydro_model['demoSchism2D'] =deepcopy(hydro_model['demoSchism3D'])
hydro_model['demoSchism2D']['reader'] = reader_demo_schisim2D

rg_basic = dict( name='rg_basic',  # name used internal to refer to this release
         class_name='PointRelease',  # class to use
         points=[[1594000, 5484200, -2]  ],
         # the below are optional settings/parameters
         release_interval=1800,  # seconds between releasing particles
         pulse_size=5)  # how many are released each interval

rg_release_interval0 = dict( name='release_interval0',  # name used internal to refer to this release
         class_name='PointRelease',  # class to use
         points=[[1594000, 5484200, -2]  ],
         # the below are optional settings/parameters
         release_interval=0,  # seconds between releasing particles
         pulse_size=5)  # how many are released each interval
rg_min_depth = dict(name='min_depth',  # name used internal to refer to this release
                    class_name='PointRelease',  # class to use
                    start=np.datetime64('2017-01-01T03:30:00'),
                    points=[[1594000, 5484200, -2]],
                    water_depth_min= 500,
                    #    tim=['2017-01-01T08:30:00','2017-01-01T01:30:00'],
                    # the below are optional settings/parameters
                    release_interval=3600,  # seconds between releasing particles
                    pulse_size=5)  # how many are released each interval
rg_outside_domain = dict( name='outside_open_boundary',  # name used internal to refer to this release
         class_name='PointRelease',  # class to use
        points=[[1594000, 0, -2]],
        max_cycles_to_find_release_points=10,
        #    dates=['2017-01-01T08:30:00','2017-01-01T01:30:00'],
         # the below are optional settings/parameters
         release_interval=3600,  # seconds between releasing particles
         pulse_size=5)  # how many are released each interval

rg_start_in_datetime1 = dict(name='start_in_datetime1',  # name used internal to refer to this release
                             class_name='PointRelease',  # class to use
                             points=[[1594000, 5484200, -2]],
                             start='2017-01-01T03:30:00',
                             # the below are optional settings/parameters
                             release_interval=3600,  # seconds between releasing particles
                             pulse_size=5)  # how many are released each interval

my_polygon_release = dict(name='my_polygon_release',  # name used internal to refer to this release
                          class_name='PolygonRelease',  # class to use
                          # (x,y) points making up a 2D polygon
                          points=[[1597682., 5486972], [1598604, 5487275], [1598886, 5486464],
                        [1597917., 5484000], [1597300, 5484000], [1597682, 5486972]],
                          # the below are optional settings/parameters
                          release_interval=3600, pulse_size=50,
                          )

rg3= dict(name='my_grid_release',  # name used internal to refer to this release
        class_name='GridRelease',  # class to use
        start='2017-01-01T02:30:00',
        grid_center=[1592000, 5489200],  # location of grid centre
        grid_span=[500, 1000],  # size of grid in meters
        grid_size=[3, 4],  # rows and columns in grid
        release_interval=1800, pulse_size=2,
        z_min=-2, z_max=-0.5)  # release at random depth between these values

rg1point= dict(name='one points',
             points=[1594500, 5487000, -1],
             release_interval=3600,
             pulse_size=10)

rg3points= dict(name='three points',
             points=[[1594500, 5487000, -1],
                     [1594500, 5483000, -1],
                     [1598000, 5486100, -1]],
             release_interval=1800,
             pulse_size=10)

pp1= dict(name='a_pollutant',  # must have a user given name
         class_name='oceantracker.particle_properties.age_decay.AgeDecay',  # class_role is resuspension
         # the below are optional settings/parameters
         initial_value=1000,  # value of property when released
         decay_time_scale=7200.)

my_heat_map_time = dict(name='my_heatmap_time',
         class_name='GriddedStats2D_timeBased',
         # the below are optional settings/parameters
         grid_size=[120, 130],  # number of rows, cols cells in the heat map
        grid_span = [10000,10000],
         release_group_centered_grids=True,  # center a grid around each release group
         update_interval=7200,  # time interval in sec, between doing particle statists counts
         particle_property_list=['a_pollutant','water_depth'],  # request a heat map for the decaying part. prop. added above
         #status_list=[],  # only count the particles which are moving

         z_min=-10.,  # only count particles at locations above z=-2m
         start='2017-01-01T02:30:00',
         )
my_heat_map_age = dict(name='my_heatmap_age',
         class_name='GriddedStats2D_ageBased',
         # the below are optional settings/parameters
         grid_size=[120, 130],  # number of east and north cells in the heat map
        grid_span = [10000,10000],
         release_group_centered_grids=True,  # center a grid around each release group
         update_interval=7200,  # time interval in sec, between doing particle statists counts
         particle_property_list=['a_pollutant','water_depth'],  # request a heat map for the decaying part. prop. added above
         #status_list=[],  # only count the particles which are moving
        age_bin_size= 24*3600,
        max_age_to_bin=24*3600,
        z_min=-10.,  # only count particles at locations above z=-2m
         )

my_poly_stats_time =dict(name='my_poly_stats_time',
        class_name='PolygonStats2D_timeBased',
        update_interval= 3600,
        particle_property_list=['a_pollutant','water_depth'],
        #status_list=[],
        )
my_poly_stats_age = dict(class_name='PolygonStats2D_ageBased',
                         name='my_poly_stats_age',
                         max_age_to_bin=4*24*3600,
                         update_interval=3600,
                         particle_property_list=['a_pollutant', 'water_depth'],
                         )

my_resident_in_polygon =dict(name='my_resident_in_polygon',
        class_name='ResidentInPolygon',
        #status_list=[],
        )


LCS = dict(name='LSC test',
           class_name='dev_LagarangianStructuresFTLE2D',
         )
ax = [1591000, 1601500, 5478500, 5491000]



def load_tracks(case_info_file, ref_case=False,fraction_to_read=None):
    from oceantracker.read_output.python import load_output_files

    fn = case_info_file if not ref_case else case_info_file.replace('unit_tests', 'unit_test_reference_cases')

    return load_output_files.load_track_data(fn, fraction_to_read=fraction_to_read)

def read_tracks(case_info_file, ref_case=False,fraction_to_read=None):
    from oceantracker.read_output.python import load_output_files
    from oceantracker.read_output.python.read_ncdf_output_files import read_tracks_file, merge_track_files

    case_info_file = case_info_file if not ref_case else case_info_file.replace('unit_tests', 'unit_test_reference_cases')
    case_info = load_output_files.read_case_info_file(case_info_file)
    o = case_info['output_files']

    fn = path.join(o['run_output_dir'],o['tracks_writer'][0])
    #d = read_tracks_file(fn,fraction_to_read=fraction_to_read)
    d = merge_track_files(o['tracks_writer'],dir=o['run_output_dir'], fraction_to_read=fraction_to_read)
    return d
def get_case_inf_name(params):
    return path.join(params['root_output_dir'],params['output_file_base'],params['output_file_base']+'_caseInfo.json')
def compare_reference_run_tracks(case_info_file, args):


    if case_info_file is None : return


    reference_case_info_file = case_info_file.replace('unit_tests', 'unit_test_reference_cases')
    if args.reference_case:
        # rewrite reference case output
        shutil.copytree(path.dirname(case_info_file), path.dirname(reference_case_info_file), dirs_exist_ok=True)

    tracks = load_tracks(case_info_file)
    tracks_ref = load_tracks(case_info_file, ref_case=True)
    dx = np.abs(tracks['x'] - tracks_ref['x'])

    # print('x diffs 3 max/ 3 mean ', np.concatenate((np.nanmax(dx, axis=1),np.nanmean(dx, axis=1)),axis=1))

    print(f'(x,y,z) differences from reference run: "{path.basename(case_info_file).split(".")[0]}"' )
    print('\t min  ', np.nanmin(np.nanmin(dx, axis=0), axis=0))
    print('\t mean ', np.nanmean(np.nanmean(dx, axis=0), axis=0))
    print('\t max  ', np.nanmax(np.nanmax(dx, axis=0), axis=0))

    dt = tracks['time'] - tracks_ref['time']
    print('times, \t  min/max diff ', np.nanmin(dt), np.nanmax(dt))
    if False:
        from matplotlib import  pyplot as plt
        v='status'
        plt.plot(np.arange(dx.shape[0]),tracks[v]-tracks_ref[v] )
        plt.show(block=True)

def compare_reference_run_stats(case_info_file, args):
    from oceantracker.read_output.python import load_output_files
    case_info = load_output_files.read_case_info_file(case_info_file)

    reference_case_info_file = case_info_file.replace('unit_tests', 'unit_test_reference_cases')
    if args.reference_case:
        # rewrite reference case output
        shutil.copytree(path.dirname(case_info_file), path.dirname(reference_case_info_file), dirs_exist_ok=True)


    # check stats
    stats_params=case_info['working_params']['class_roles']['particle_statistics']
    for name, params in stats_params.items():
        if name not in case_info['output_files']['particle_statistics']: continue
        stats_ref= load_output_files.load_stats_data(reference_case_info_file, name=name)
        stats= load_output_files.load_stats_data(case_info_file, name=name)


        print(f'Stats  compare ref: "{name}"')
        print('\t counts, ref/new', stats_ref['count'].sum(), stats['count'].sum(),
              '\t\t\t max diff counts-ref run counts =',np.max(np.abs(stats['count'] - stats_ref['count'])))
        print('\t count all alive, ref/new', stats_ref['count_all_alive_particles'].sum(), stats['count_all_alive_particles'].sum(),
             'last time/age step', stats_ref['count_all_alive_particles'][-1,:].sum(), stats['count_all_alive_particles'][-1,:].sum(),
                      '\t max diff counts-ref run counts =',np.max(np.abs(stats['count_all_alive_particles'] - stats_ref['count_all_alive_particles'])))
        if 'particle_property_list' in params:
            for prop_name in params['particle_property_list']:
                if prop_name not in stats_ref: continue
                dc = np.abs(stats[prop_name] - stats_ref[prop_name])
                print(f'\t Property  "{prop_name}"', 'max mag.',
                      np.nanmax(np.abs(stats[prop_name])), np.nanmax(np.abs(stats_ref[prop_name])), ', max diff =', np.max(dc[np.isfinite(dc)]))

    pass
def show_track_plot(case_info_file, args,colour_with=None):
    from oceantracker.plot_output import plot_tracks
    if not args.plot : return
    if case_info_file is None :
        print('>>> Run failed no unit test plot')
        return

    tracks= load_tracks(case_info_file)

    movie_file1= path.join(image_dir, 'decay_movie_frame.mp4') if args.save_plots else None

    anim= plot_tracks.animate_particles(tracks,
                                        show_grid=True, show_dry_cells=True, axis_labels=True,
                                        #part_color_map='hot',
                                        colour_using_data=None if colour_with is None else tracks[colour_with],
                                        movie_file=movie_file1)

def plot_vert_section(case_info_file, args,fraction_to_read):
    if not args.plot: return

    from oceantracker.plot_output.plot_tracks import plot_path_in_vertical_section
    tracks = load_tracks(case_info_file,fraction_to_read=fraction_to_read)
    plot_path_in_vertical_section(tracks, particleID=np.arange(0,tracks['x'].shape[1],10))