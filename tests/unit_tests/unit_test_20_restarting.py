from os import path, sep



from oceantracker.main import OceanTracker

from plot_oceantracker import plot_tracks
import  argparse
import shutil
import numpy as np
from tests.unit_tests import test_definitions

def main(args):
    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__, args))
    ot.settings(time_step=1800,use_dispersion=False,
                screen_output_time_interval=1800,
             use_A_Z_profile=True,
            regrid_z_to_uniform_sigma_levels=False,
            particle_buffer_initial_size= 100,
             NUMBA_cache_code=True,
                use_resuspension = False,
                restart_interval = 3*3600
                )




    hm = test_definitions.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'])

    # add a point release
    ot.add_class('release_groups',**test_definitions.rg_basic)


    if False:
        ot.add_class('tracks_writer', update_interval=1 * 3600, write_dry_cell_flag=False,
                     time_steps_per_per_file=None if args.reference_case else 10  # dont split files ref case to test reading split files
                     )  # keep file small

        # add a decaying particle property,# with exponential decay based on age
        ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role
        ot.add_class('particle_properties', class_name='WaterSpeed')
        ot.add_class('particle_properties', class_name='AgeDecay', name='test_decay')
        ot.add_class('particle_properties', class_name='DistanceTravelled')

        # add a gridded particle statistic to plot heat map
        ot.add_class('particle_statistics',**test_definitions.ps1)

        ot.add_class('particle_statistics', **test_definitions.poly_stats,
                 polygon_list=[dict(points=hm['polygon'])])


    case_info_file = ot.run()

    if False:
        test_definitions.compare_reference_run(case_info_file, args)
        test_definitions.show_track_plot(case_info_file, args)

    return  ot.params



