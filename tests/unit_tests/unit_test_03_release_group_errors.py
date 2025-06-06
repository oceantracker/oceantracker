from oceantracker.main import OceanTracker
from copy import deepcopy
from tests.unit_tests import test_definitions

def main(args):
    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__, args))
    hm = test_definitions.hydro_model['demoSchism3D']

    ot.settings(time_step=900,use_dispersion=False,backtracking=True,
             use_A_Z_profile=False, )


    #ot.settings(NUMBA_cache_code = True)
    ot.add_class('reader', **hm['reader'])

    ot.add_class('release_groups', name='my_point_release',  # name used internal to refer to this release
             class_name='PointRelease',  # class to use
             points=[[1594000., 5487000], [1594000, 5481000],],
             release_interval=900, pulse_size=1)

    ot.add_class( 'release_groups',name='my_polygon_release',  # name used internal to refer to this release
                    class_name='PolygonRelease',  # class to use
                    points=[[1597682., 5486972], [1598604, 5487275], [1598886, 5486464],
                            [1597917., 5484000], [1597300, 5484000], [1597682, 5486972]],
                    # the below are optional settings/parameters
                    release_interval=900, pulse_size=1,
                    z_min=-2., z_max=0.5)

    ot.add_class('tracks_writer',update_interval = 900, write_dry_cell_flag=False)

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role

    # add a gridded particle statistic to plot heat map

    case_info_file = ot.run()

    test_definitions.show_track_plot(case_info_file, args,colour_with='IDrelease_group')

    return ot.params




