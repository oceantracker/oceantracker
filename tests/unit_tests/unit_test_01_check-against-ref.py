from os import path, sep



from oceantracker.main import OceanTracker

from plot_oceantracker import plot_tracks
import  argparse
import shutil
import numpy as np
from tests.unit_tests import test_definitions

def main(args):
    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__,args))
    ot.settings(time_step=3600,use_dispersion=False,
            screen_output_time_interval=1800,
            use_A_Z_profile=True,
            regrid_z_to_uniform_sigma_levels=True,
            max_time_steps_per_file=100,
            #particle_buffer_initial_size= 10,
             #   NUMBA_cache_code=True,
                #NCDF_particle_chunk= 50000
                )

    ot.add_class('tracks_writer',update_interval = 900, write_dry_cell_flag=False,
               ) # keep file small

    #ot.settings(NUMBA_cache_code = True)
    hm = test_definitions.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'])

    # add a point release
    ot.add_class('release_groups',**test_definitions.rg_release_interval0)
    ot.add_class('release_groups', **test_definitions.rg_min_depth)
    ot.add_class('release_groups', **test_definitions.rg_start_in_datetime1)
    ot.add_class('release_groups', **test_definitions.rg_outside_domain)

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role
    ot.add_class('particle_properties', class_name='WaterSpeed')
    ot.add_class('particle_properties', class_name='AgeDecay', name='test_decay')
    ot.add_class('particle_properties', class_name='DistanceTravelled')

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**test_definitions.ps1)

    ot.add_class('particle_statistics', **test_definitions.poly_stats,
                 polygon_list=[dict(points=hm['polygon'])])

    ot.add_class('resuspension', critical_friction_velocity=0.01)


    case_info_file = ot.run()

    test_definitions.compare_reference_run(case_info_file, args)

    test_definitions.show_track_plot(case_info_file, args)

    return  ot.params



