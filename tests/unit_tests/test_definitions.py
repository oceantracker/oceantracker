import datetime
from os import path, sep
from oceantracker.main import OceanTracker
from read_oceantracker.python import load_output_files
from plot_oceantracker import plot_tracks
import  argparse
import shutil
import numpy as np
from oceantracker import definitions
from oceantracker.util import cord_transforms


def set_output_loc(fn):
    d =  dict(output_file_base=path.split(fn)[-1].split('.')[0],
            root_output_dir=path.join(path.dirname(fn), 'output'),
            )
    return d

def base_settings(fn,args,label=None):
    s = path.split(fn)[-1].split('.')[0]
    if args.variant is not None: s+=f'_{args.variant:02d}'
    if label is not None: s += f'_{label}'
    d =  dict(output_file_base=s,
            root_output_dir=path.join(path.dirname(fn), 'output'),
            time_step=600.,  # 10 min time step
            use_random_seed = True,
            NCDF_time_chunk=1,
            debug=True
            )
    return d

image_dir= 'output'
reader_demo_schisim=   dict( # folder to search for hindcast files, sub-dirs will, by default, will also be searched
                 input_dir= path.join(path.dirname(definitions.package_dir),'demos','demo_hindcast'),  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                 file_mask='demoHindcastSchism*.nc',
)  # file mask to search for

reader_double_gyre=  dict(class_name='oceantracker.reader.generic_stuctured_reader.dev_GenericStructuredReader',
             input_dir=f'E:\H_Local_drive\ParticleTracking\hindcast_formats_examples\generic2D_structured_DoubleGyre',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
             file_mask='Double_gyre.nc',
             dimension_map=dict(time='t', rows='y', cols='x'),
             grid_variable_map=dict(time='Time', x=['x_grid', 'y_grid']),
             field_variable_map=dict(water_depth='Depth', water_velocity=['U', 'V'], tide='Tide'),
             hydro_model_cords_in_lat_long=False)

reader_NZnational=dict(  input_dir = r'G:\Hindcasts_large\OceanNumNZ-2022-06-20\final_version\2022\01',
            file_mask = 'NZfinite*.nc')
reader_Sounds =dict(  input_dir = r'G:\Hindcasts_large\MalbroughSounds_10year_benPhD\2017',
            file_mask = 'schism_marl201701*.nc')
hydro_model = dict(demoSchism=dict(reader= reader_demo_schisim,
                            axis_lims=[1591000, 1601500, 5478500, 5491000],
                            x0=[[1594000, 5484200] ],
                            polygon=[[1597682., 5486972], [1598604, 5487275], [1598886, 5486464],
                                    [1597917., 5484000], [1597300, 5484000], [1597682, 5486972]],
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

rg_release_interval0 = dict( name='release_interval0',  # name used internal to refer to this release
         class_name='PointRelease',  # class to use
         points=[[1594000, 5484200, -2]  ],
         # the below are optional settings/parameters
         release_interval=0,  # seconds between releasing particles
         pulse_size=5)  # how many are released each interval
rg_datetime = dict( name='start_in_middle1',  # name used internal to refer to this release
         class_name='PointRelease',  # class to use
        start=np.datetime64('2017-01-01T03:30:00'),
        points=[[1594000, 5484200, -2]],
        #    tim=['2017-01-01T08:30:00','2017-01-01T01:30:00'],
         # the below are optional settings/parameters
         release_interval=3600,  # seconds between releasing particles
         pulse_size=5)  # how many are released each interval
rg_outside_domain = dict( name='outside_open_boundary',  # name used internal to refer to this release
         class_name='PointRelease',  # class to use
        points=[[1594000, 0, -2]],
        #    dates=['2017-01-01T08:30:00','2017-01-01T01:30:00'],
         # the below are optional settings/parameters
         release_interval=3600,  # seconds between releasing particles
         pulse_size=5)  # how many are released each interval

rg_start_in_middle = dict( name='start_in_middl21',  # name used internal to refer to this release
         class_name='PointRelease',  # class to use
        points=[[1594000, 5484200, -2]],
        start='2017-01-01T03:30:00',
         # the below are optional settings/parameters
         release_interval=3600,  # seconds between releasing particles
         pulse_size=5)  # how many are released each interval

rg_ploy1 = dict(name='my_polygon_release',  # name used internal to refer to this release
         class_name='PolygonRelease',  # class to use
         # (x,y) points making up a 2D polygon
         points=[[1597682., 5486972], [1598604, 5487275], [1598886, 5486464],
                 [1597917., 5484000], [1597300, 5484000], [1597682, 5486972]],
         # the below are optional settings/parameters
         release_interval=3600, pulse_size=50,
         z_min=-2., z_max=0.5)

rg3= dict(name='my_grid_release',  # name used internal to refer to this release
        class_name='GridRelease',  # class to use
        start='2017-01-01T02:30:00',
        grid_center=[1592000, 5489200],  # location of grid centre
        grid_span=[500, 1000],  # size of grid in meters
        grid_size=[3, 4],  # rows and columns in grid
        release_interval=1800, pulse_size=2,
        z_min=-2, z_max=-0.5)  # release at random depth between these values

rg3points= dict(name='three points',
             points=[[1594500, 5487000, -1],
                     [1594500, 5483000, -1],
                     [1598000, 5486100, -1]],
             release_interval=3600,
             pulse_size=10)

pp1= dict(name='a_pollutant',  # must have a user given name
         class_name='oceantracker.particle_properties.age_decay.AgeDecay',  # class_role is resuspension
         # the below are optional settings/parameters
         initial_value=1000,  # value of property when released
         decay_time_scale=7200.)

ps1 = dict(name='my_heatmap',
         class_name='GriddedStats2D_timeBased',
         # the below are optional settings/parameters
         grid_size=[120, 121],  # number of east and north cells in the heat map
         release_group_centered_grids=True,  # center a grid around each release group
         update_interval=7200,  # time interval in sec, between doing particle statists counts
         particle_property_list=['a_pollutant'],  # request a heat map for the decaying part. prop. added above
         status_min='moving',  # only count the particles which are moving
         z_min=-10.,  # only count particles at locations above z=-2m
         start='2017-01-01T02:30:00',
         )

poly_stats =dict(
        class_name='PolygonStats2D_timeBased',
        update_interval= 3600,
        particle_property_list=['water_depth'],
        status_min= 'moving',
        z_min= -2,
        grid_size= [120, 121])
LCS = dict(name='LSC test',
           class_name='dev_LagarangianStructuresFTLE2D',
         )
ax = [1591000, 1601500, 5478500, 5491000]



def read_tracks(case_info_file):
    return load_output_files.load_track_data(case_info_file)

