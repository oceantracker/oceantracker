# code to run particle tracking and plot Fig 1

from oceantracker.main import OceanTracker # load
ot= OceanTracker() # creat an instance to build parameter dictionary= ot.params

# add settings
ot.settings(output_file_base='OTpaper_exmaple_A',  root_output_dir='output', time_step= 600.)

 # add reader to acces the hyrdo-model
ot.add_class('reader',  input_dir=r'E:\H_Local_drive\ParticleTracking\oceantracker\demos\demo_hindcast',
                 file_mask=  'demoHindcastSchism*.nc')  # file mask to search for
# add a point release
ot.add_class('release_groups',name = 'my_point_release', class_name='PointRelease', # class to use
        points= [[1595000, 5482600, -2], [1594000, 5484200, -2]], # one or more (x,y,z) of release points
        release_interval= 600, pulse_size= 5)
# add polygon release
ot.add_class('release_groups',  name = 'my_polygon_release',  class_name='PolygonRelease',
        points=[[1597682., 5486972], [1598604, 5487275], [1598886, 5486464],  [1597917., 5484000], [1597300, 5484000], [1597682, 5486972]],
        release_interval= 600,  pulse_size= 50, z_min= -2., z_max = 0.5)   # release at random depth between these values
# add grid release
ot.add_class('release_groups',  name = 'my_grid_release', class_name='GridRelease', #
        grid_center=[1592000, 5489200], grid_span=[500, 1000], grid_size=[3, 4], # rows and columns in grid
        release_interval= 1800,  pulse_size= 2, z_min= -2, z_max = -0.5)   # release at random depth between these values
# add a decaying particle property,# with exponential decay based on age
ot.add_class('particle_properties', name ='a_pollutant', class_name='oceantracker.particle_properties.age_decay.AgeDecay',
            initial_value= 1000, decay_time_scale = 7200.) # 2 hour decay, property value decays as initial_value*exp(-age/decay_time_scale)
# add a gridded particle statistic to use as heat map
ot.add_class('particle_statistics', name = 'my_heatmap', class_name= 'GriddedStats2D_timeBased',
        grid_size=[120, 121],  release_group_centered_grids = True, update_interval = 600, # time interval in sec, between doing particle statists counts
        particle_property_list = ['a_pollutant'],  status_min ='moving', z_min =-10.)
ot.add_class('resuspension', critical_friction_velocity=0.01) #set value for particle resupension
run= True
if run:
    case_info_file= ot.run()

# separate run heat map run
ot= OceanTracker()
ot.settings(output_file_base='OTpaper_exmaple_A_heatmap', # name used as base for output files
            root_output_dir='output',             #  output is put in dir   'root_output_dir'\\'output_file_base'
            time_step= 600. #  10 min time step
            )
ot.add_class('reader',  # class role, them parameters
                # folder to search for hindcast files, sub-dirs will, by default, will also be searched
                input_dir=r'E:\H_Local_drive\ParticleTracking\oceantracker\demos\demo_hindcast',   # folder to search for hindcast files, sub-dirs will, by default, also be searched
                file_mask=  'demoHindcastSchism*.nc')  # file mask to search for
# add a decaying particle property,# with exponential decay based on age
ot.add_class('particle_properties', # add a new property to particle_properties role
            name ='a_pollutant', # must have a user given name
            class_name='oceantracker.particle_properties.age_decay.AgeDecay', #  class_role is resuspension
            # the below are optional settings/parameters
            initial_value= 1000, # value of property when released
            decay_time_scale = 7200.) # 2 hour decay, property value decays as initial_value*exp(-age/decay_time_scale)
ot.add_class('release_groups',  # class role
             name='my_point_release_heatmap',  # name used internal to refer to this release
             class_name='PointRelease',  # class to use
             points=[[1595000, 5482600, -2],  # one or more (x,y,z) of release points
                     [1594000, 5484200, -2]],
             # the below are optional settings/parameters
             release_interval=600,  # seconds between releasing particles
             pulse_size=5000)  # how many are released each interval

# add a gridded particle statistic to plot heat map
ot.add_class('particle_statistics',
                name = 'my_heatmap',
                class_name= 'GriddedStats2D_timeBased',
                # the below are optional settings/parameters
                grid_size=[120, 121],  # number of east and north cells in the heat map
                release_group_centered_grids = True, # center a grid around each release group
                update_interval = 600, # time interval in sec, between doing particle statists counts
                particle_property_list = ['a_pollutant'], # request a heat map for the decaying part. prop. added above
                status_min ='moving', # only count the particles which are moving
                z_min =-10.,  # only count particles at locations above z=-2m
                )

if run:
    stats_case_info= ot.run()
# plotting after run
from read_oceantracker.python import load_output_files
from  plot_oceantracker import plot_tracks,plot_statistics
from os import path
case_info_file =r'E:\H_Local_drive\ParticleTracking\oceantracker\tests\misc\output\OTpaper_exmaple_A\OTpaper_exmaple_A_caseInfo.json'
track_data = load_output_files.load_track_data(case_info_file)
ax= [1591000, 1601500, 5478500, 5491000]

# plot a single time step
single_time_step = 23
image_dir =r'E:\H_Local_drive\OceanTrackerPaper'

# Figure 1b)  particle snapshot
plot_tracks.animate_particles(track_data,axis_lims=ax,single_time_step =single_time_step,
                              show_grid=True, show_dry_cells=True,
                              movie_file= path.join(image_dir,'tracks_movie_frame.mp4'))

# Figure 1b)  particles sized by user added decaying particle property 'a_pollutant'
p1= plot_tracks.animate_particles(track_data,axis_lims=ax,single_time_step =single_time_step,
                              show_grid=True, show_dry_cells=True,part_color_map='hot',
                              size_using_data=track_data['a_pollutant'],colour_using_data=track_data['a_pollutant'],
                              movie_file= path.join(image_dir,'decay_movie_frame.mp4'))
case_info_file =r'E:\H_Local_drive\ParticleTracking\oceantracker\tests\misc\output\OTpaper_exmaple_A_heatmap\OTpaper_exmaple_A_heatmap_caseInfo.json'


stats_data = load_output_files.load_stats_data(case_info_file) # load gridded heatmap data
# Figure 1c)  Snapshot heat-map of particles counts, plotting  gridded a statistic  at last time step
plot_statistics.plot_heat_map(stats_data, 'my_point_release_heatmap' ,
                              logscale=True, axis_lims=ax,cmap='hot',
                              show_grid=True, colour_bar=False,
                              plot_file_name=path.join(image_dir,'heatmap_counts.png'))
# Figure 1d)  Snapshot heat-map of decaying particle property 'a_pollutant'
plot_statistics.plot_heat_map(stats_data, 'my_point_release_heatmap',
                              logscale=True, axis_lims=ax,#cmap='hot',
                              show_grid=True,var='a_pollutant',colour_bar=False,
                              plot_file_name=path.join(image_dir,'heatmap_decay.png'))







