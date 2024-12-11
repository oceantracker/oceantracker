from os import path, sep
from oceantracker.main import OceanTracker
from oceantracker import  definitions
from plot_oceantracker import plot_tracks
import  argparse
import shutil
import numpy as np
from tests.unit_tests import test_definitions

def main(args):
    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__,args))
    ot.settings(time_step=1800,
                use_dispersion=False,
             use_A_Z_profile=False,
            regrid_z_to_uniform_sigma_levels=True)

    ot.add_class('tracks_writer',update_interval = 1*3600, write_dry_cell_flag=False,
                 NCDF_particle_chunk= 500) # keep file small

    #ot.settings(NUMBA_cache_code = True)
    hm = test_definitions.hydro_model['demoSchism']
    hm['reader'].update(input_dir= path.join(path.dirname(definitions.package_dir),'demos','demo_hindcast','ROMS'),
                        file_mask='ROMS3D_00*.nc')
    ot.add_class('reader', **hm['reader'])

    # add a point release
    ot.add_class('release_groups',points=  [-69.5, 43.5], release_interval= 1800)
    ot.add_class('release_groups', points= [-68.96, 44.1], release_interval=1800)

    poly_points = np.asarray([[-69., 43.5], [-69.2, 43.5], [-69.2, 43.7],[-69.1, 43.7],[-69., 43.5]])

    ot.add_class('release_groups',name='my_polygon_release',  # name used internal to refer to this release
                            class_name='PolygonRelease',  # class to use
                            release_interval = 1800,
                            points=poly_points)
    ot.add_class('release_groups', name='my_grid_release',  # name used internal to refer to this release
                 class_name='GridRelease',  # class to use
                 release_interval=1800,
                 grid_span=[.2,.2],
                 grid_size=[3,4],
                 grid_center=[-69.5, 43.5],
                 )
    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role
    ot.add_class('particle_properties', class_name='Speed', name='speed')
    ot.add_class('particle_statistics',name='my_heatmap',
                                             class_name='GriddedStats2D_timeBased',
                                            grid_span=[1,1.5],
                                             # the below are optional settings/parameters
                                             grid_size=[60, 121],  # number of east and north cells in the heat map
                                             release_group_centered_grids=True,  # center a grid around each release group
                                             update_interval=1800,  # time interval in sec, between doing particle statists counts
                                             particle_property_list=['speed'],  # request a heat map for the decaying part. prop. added above
                                             status_list=['moving'],  # only count the particles which are moving
                                             z_min=-10.,  # only count particles at locations above z=-2m
                                        )
    ot.add_class('particle_statistics',name='my_polygon_stats',
                                             class_name='PolygonStats2D_timeBased',
                                             # the below are optional settings/parameters
                                             polygon_list=[dict(points=poly_points+.05)],  # number of east and north cells in the heat map
                                             update_interval=1800,  # time interval in sec, between doing particle statists counts
                                             particle_property_list=['speed'],  # request a heat map for the decaying part. prop. added above
                                             status_list=['moving'],  # only count the particles which are moving
                                             z_min=-10.,  # only count particles at locations above z=-2m
                                        )
    case_info_file = ot.run()

    test_definitions.compare_reference_run(case_info_file, args)

    test_definitions.show_track_plot(case_info_file, args)





