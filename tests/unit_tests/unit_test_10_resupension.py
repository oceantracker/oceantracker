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
    ot.settings(time_step=60,
                screen_output_time_interval=600,
             use_A_Z_profile=False,
            regrid_z_to_uniform_sigma_levels=False,
             NUMBA_cache_code=True,
                #NCDF_particle_chunk= 50000
                )

    ot.add_class('tracks_writer',update_interval = 600, write_dry_cell_flag=True,)
    #ot.settings(NUMBA_cache_code = True)
    hm = test_definitions.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'])

    # add a point release
    ot.add_class('release_groups',
                 name='point1',
                 points=[1597682.1237, 5489972.7479],release_at_surface=True,
                 release_interval=0, pulse_size=1000)

    ot.add_class('velocity_modifiers', class_name='TerminalVelocity', name='fall_vel',value=-0.002)

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**test_definitions.ps1)



    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role
    ot.add_class('particle_properties', class_name='WaterSpeed')
    ot.add_class('particle_properties', class_name='AgeDecay', name='test_decay')
    ot.add_class('particle_properties', class_name='DistanceTravelled')


    # run with default resupension
    ot.add_class('resuspension', critical_friction_velocity=0.01, class_name='Resuspension')
    case_info_file1 = ot.run()
    test_definitions.show_track_plot(case_info_file1, args)
    test_definitions.plot_vert_section(case_info_file1, fraction_to_read=0.05)

    # run with basic resupension
    ot.add_class('resuspension', critical_friction_velocity=0.01, class_name='BasicResuspension')
    case_info_file2 = ot.run()
    test_definitions.show_track_plot(case_info_file2, args)
    test_definitions.plot_vert_section(case_info_file2, fraction_to_read=0.05)


    return  ot.params



