import numpy as np

from oceantracker.main import OceanTracker
from copy import deepcopy
from unit_tests import test_definitions

def main(args):
    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__, args))
    hm = test_definitions.hydro_model['demoSchism3D']

    ot.settings(time_step=900,use_dispersion=False,
             use_A_Z_profile=False, )


    #ot.settings(NUMBA_cache_code = True)
    ot.add_class('reader', **hm['reader'])

    ot.add_class('release_groups', name='my_radius_release',  # name used internal to refer to this release
             class_name='RadiusRelease',  # class to use
             points=[[1593000., 5487000], [1593000, 5484000],],
             radius = 1000, release_interval=1800, pulse_size=2,
             start = '2017-01-01T02:00:00',
             end='2017-01-01T12:00:00',
             max_age=3*3600)

    ot.add_class('release_groups', name='my_point_release',  # name used internal to refer to this release
             class_name='PointRelease',  # class to use
             points=[[1593000., 5491000], [1593000, 5481000],],
             release_interval=900, pulse_size=2)
    poly =np.asarray([[1597682., 5486972], [1598604, 5487275], [1598886, 5486464],
                     [1597917., 5484000], [1597300, 5484000], [1597682, 5486972]])
    #poly= poly - np.asarray([0,1000])
    ot.add_class( 'release_groups',name='my_polygon_release',  # name used internal to refer to this release
                    class_name='PolygonRelease',  # class to use
                    points=poly,
                    # the below are optional settings/parameters
                    release_interval=900, pulse_size=2,
                    z_min=-2., z_max=0.5)

    ot.add_class( 'release_groups',name='my_grid_release',  # name used internal to refer to this release
                    class_name='GridRelease',
                  release_interval=1800, pulse_size=2,
                  grid_center=[1601000, 5484000],
                  grid_span=[1000, 3000], grid_size=[3, 4],)

    ot.add_class('tracks_writer',update_interval = 900, write_dry_cell_flag=False)

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role

    # add a gridded particle statistic to plot heat map

    case_info_file = ot.run()

    test_definitions.compare_reference_run_tracks(case_info_file,args)
    test_definitions.show_track_plot(case_info_file, args,colour_with='IDrelease_group')

    return ot.params




