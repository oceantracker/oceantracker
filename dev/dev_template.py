
# a tempate which uses demo hindcasts for dev testing
from os import path, sep
from oceantracker.main import OceanTracker
from oceantracker import definitions
from plot_oceantracker import plot_tracks
from read_oceantracker.python import  load_output_files
import  argparse
from os import path
# some polgons for demo hindcast

poly1 = [[1597682., 5486972], [1598604, 5487275], [1598886, 5486464],
          [1597917., 5484000], [1597300, 5484000], [1597682, 5486972]]
package_dir = definitions.package_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-plot', action='store_true')
    parser.add_argument('-save_plots', action='store_true')

    ot = OceanTracker()

    ot.settings(root_output_dir=path.join(definitions.default_output_dir, 'dev_output'),
        # below optional
        time_step=300,
        use_dispersion=True,
        screen_output_time_interval=1800,
        use_A_Z_profile=True,
        regrid_z_to_uniform_sigma_levels=True
                )

    # set up reader
    demo_hindcast_dir =path.join(path.dirname(definitions.package_dir), 'demos')
    ot.add_class('reader',  # folder to search for hindcast files, sub-dirs will, by default, will also be searched
            input_dir=path.join(demo_hindcast_dir, 'demo_hindcast', 'schsim3D'),
            file_mask='demo_hindcast_schisim3D*.nc')

    # add a point release
    ot.add_class('release_groups',name='release_interval0',  # name used internal to refer to this release
         class_name='PointRelease',  # class to use
         points=[[1594300, 5483400, -2]  ],
         release_interval=3600,  # seconds between releasing particles
         pulse_size=5)

    ot.add_class('release_groups', name='my_polygon_release',  # name used internal to refer to this release
         class_name='PolygonRelease',  # class to use
         # (x,y) points making up a 2D polygon
         points=poly1,
         # the below are optional settings/parameters
         release_interval=3600, pulse_size=5,
         z_min=-2., z_max=0.5)

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', name='a_pollutant',  # must have a user given name
         class_name='oceantracker.particle_properties.age_decay.AgeDecay',  # class_role is resuspension
         # the below are optional settings/parameters
         initial_value=1000,  # value of property when released
         decay_time_scale=7200.) # add a new property to particle_properties role
    ot.add_class('particle_properties', class_name='Speed', name='speed')

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics', name='my_heatmap',
         class_name='GriddedStats2D_timeBased',
         # the below are optional settings/parameters
         grid_size=[120, 121],  # number of east and north cells in the heat map
         release_group_centered_grids=True,  # center a grid around each release group
         update_interval=7200,  # time interval in sec, between doing particle statists counts
         particle_property_list=['a_pollutant'],  # request a heat map for the decaying part. prop. added above
         status_min='moving',  # only count the particles which are moving
         z_min=-10.,  # only count particles at locations above z=-2m
         start='2017-01-01T02:30:00',)

    ot.add_class('particle_statistics', class_name='PolygonStats2D_timeBased',
        update_interval= 3600,
        particle_property_list=['water_depth'],
        status_min= 'moving',
        z_min= -2,
        grid_size= [120, 121],
                 polygon_list=[dict(points=poly1)])
    ot.add_class('resuspension', critical_friction_velocity=0.002)

    case_info_file = ot.run()

    tracks=load_output_files.load_track_data(case_info_file)

    ax = [1591000, 1601500, 5478500, 5491000]
    anim = plot_tracks.animate_particles(tracks,axis_lims=ax,
                                show_grid=True, show_dry_cells=True)
