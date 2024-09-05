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
    ot.settings(time_step=1800,
                use_dispersion=False,
             use_A_Z_profile=False,
            regrid_z_to_uniform_sigma_levels=True)

    ot.add_class('tracks_writer',update_interval = 1*3600, write_dry_cell_flag=False,
                 NCDF_particle_chunk= 500) # keep file small

    #ot.settings(NUMBA_cache_code = True)
    hm = test_definitions.hydro_model['demoSchism']
    hm['reader'].update(input_dir=r'E:\H_Local_drive\ParticleTracking\oceantracker\demos\demo_hindcast\schsim2D',
                        file_mask='Random_order*.nc')
    ot.add_class('reader', **hm['reader'])

    # add a point release
    ot.add_class('release_groups',**test_definitions.rg_release_interval0)
    ot.add_class('release_groups', **test_definitions.rg_start_in_middle)
    ot.add_class('release_groups', **test_definitions.rg_outside_domain)
    ot.add_class('release_groups', **test_definitions.rg_datetime)

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role
    ot.add_class('particle_properties', class_name='Speed', name='speed')

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**test_definitions.ps1)

    ot.add_class('particle_statistics', **test_definitions.poly_stats,
                 polygon_list=[dict(points=hm['polygon'])])

    case_info_file = ot.run()


    test_definitions.compare_reference_run(case_info_file, args)

    test_definitions.show_track_plot(case_info_file, args)




