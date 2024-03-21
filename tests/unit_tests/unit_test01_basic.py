from os import path, sep
from oceantracker.main import OceanTracker
from read_oceantracker.python import load_output_files
from plot_oceantracker import plot_tracks


def base_settings(fn):
    d =  dict(output_file_base=path.split(fn)[-1].split('.')[0],
                root_output_dir=path.join(path.dirname(fn), 'output'),
                time_step=600.,  # 10 min time step
                max_run_duration=12*3600.
                )
    return d

reader1=   dict( # folder to search for hindcast files, sub-dirs will, by default, will also be searched
                 input_dir=r'E:\H_Local_drive\ParticleTracking\oceantracker\demos\demo_hindcast',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                 file_mask='demoHindcastSchism*.nc')  # file mask to search fo

rg1 = dict( name='my_point_release',  # name used internal to refer to this release
         class_name='PointRelease',  # class to use
         points=[[1595000, 5482600, -2],  # one or more (x,y,z) of release points
                 [1594000, 5484200, -2]],
         # the below are optional settings/parameters
         release_interval=600,  # seconds between releasing particles
         pulse_size=5)  # how many are released each interval
rg2 = dict(name='my_polygon_release',  # name used internal to refer to this release
         class_name='PolygonRelease',  # class to use
         # (x,y) points making up a 2D polygon
         points=[[1597682., 5486972], [1598604, 5487275], [1598886, 5486464],
                 [1597917., 5484000], [1597300, 5484000], [1597682, 5486972]],
         # the below are optional settings/parameters
         release_interval=600, pulse_size=50,
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

def read_tracks(case_info_file):
    return load_output_files.load_track_data(case_info_file)

def main():
    ot = OceanTracker()
    ot.settings(**base_settings(__file__))
    #ot.settings(numba_cache_code = True)
    ot.add_class('reader',**reader1)

    # add a point release
    ot.add_class('release_groups',**rg1)
    ot.add_class('release_groups',**rg2)  # class role
    ot.add_class('release_groups', **rg3)  # class role

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **pp1) # add a new property to particle_properties role

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**ps1)
    ot.add_class('resuspension', critical_friction_velocity=0.01)

    case_info_file = ot.run()
    return case_info_file

def read_test(case_info_file):
    track_data = read_tracks(case_info_file)
    return track_data

def plot_test(track_data):
    ax = [1591000, 1601500, 5478500, 5491000]
    single_time_step = 23
    image_dir = r'E:\H_Local_drive\OceanTrackerPaper'
    p1 = plot_tracks.animate_particles(track_data, axis_lims=ax, single_time_step=single_time_step,
                                       show_grid=True, show_dry_cells=True, part_color_map='hot',
                                       size_using_data=track_data['a_pollutant'], colour_using_data=track_data['a_pollutant'],
                                       movie_file=path.join(image_dir, 'decay_movie_frame.mp4'))

if __name__ == "__main__":
    case_info_file = main()

    track_data= read_test(case_info_file)
    plot_test(track_data)