from os import path, sep
from oceantracker.main import OceanTracker
from read_oceantracker.python import load_output_files
from plot_oceantracker import plot_tracks
import  argparse
import shutil
import numpy as np
from oceantracker import definitions

def set_output_loc(fn):
    d =  dict(output_file_base=path.split(fn)[-1].split('.')[0],
            root_output_dir=path.join(path.dirname(fn), 'output'),
            )
    return d

def base_settings(fn):
    d =  dict(output_file_base=path.split(fn)[-1].split('.')[0],
            root_output_dir=path.join(path.dirname(fn), 'output'),
            time_step=600.,  # 10 min time step
            USE_random_seed = True,
            NCDF_time_chunk=1,
            )
    return d

image_dir= 'output'
reader1=   dict( # folder to search for hindcast files, sub-dirs will, by default, will also be searched
                 input_dir= path.join(path.dirname(definitions.package_dir),'demos','demo_hindcast'),  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                 file_mask='demoHindcastSchism*.nc')  # file mask to search for

reader_double_gyre=  dict(class_name='oceantracker.reader.generic_stuctured_reader.GenericStructuredReader',
             input_dir=f'E:\H_Local_drive\ParticleTracking\hindcast_formats_examples\generic2D_structured_DoubleGyre',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
             file_mask='Double_gyre.nc',
             dimension_map=dict(time='t', rows='y', cols='x'),
             grid_variable_map=dict(time='Time', x=['x_grid', 'y_grid']),
             field_variable_map=dict(water_depth='Depth', water_velocity=['U', 'V'], tide='Tide'),
             hydro_model_cords_in_lat_long=False)

rg0 = dict( name='my_point_release',  # name used internal to refer to this release
         class_name='PointRelease',  # class to use
         points=[
              #[1595000, 5482600, -2],  # one or more (x,y,z) of release points
              [1594000, 5484200, -2]
                 ],
         # the below are optional settings/parameters
         release_interval=600,  # seconds between releasing particles
         pulse_size=5)  # how many are released each interval
rg1 = dict( name='my_point_release',  # name used internal to refer to this release
         class_name='PointRelease',  # class to use
         points=[
              [1595000, 5482600, -2],  # one or more (x,y,z) of release points
              [1594000, 5484200, -2]
                 ],
         # the below are optional settings/parameters
         release_interval=3600,  # seconds between releasing particles
         pulse_size=5)  # how many are released each interval
rg2 = dict(name='my_polygon_release',  # name used internal to refer to this release
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
ax = [1591000, 1601500, 5478500, 5491000]
def read_tracks(case_info_file):
    return load_output_files.load_track_data(case_info_file)

