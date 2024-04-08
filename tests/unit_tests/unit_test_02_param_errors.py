from os import path, sep
from oceantracker.main import OceanTracker

from plot_oceantracker import plot_tracks
import  argparse
import shutil
import numpy as np
from tests.unit_tests import test_definitions

def main(args):
    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__))
    ot.settings(time_step=1800,include_dispersion=False,
             use_A_Z_profile=False, )


    #ot.settings(NUMBA_cache_code = True)
    ot.add_class('reader', **test_definitions.demo_schisim)

    # add a point release
    ot.add_class('release_groups',start_date='hh', **test_definitions.rg_start_in_middle)

    ot.add_class('tracks_writer',update_interval_1 = 1*3600, write_dry_cell_flag=False,
                 NCDF_particle_chunk= 500) # keep file small

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**test_definitions.ps1)
    ot.add_class('resuspension', critical_friction_velocity=0.01)
    case_info_file = ot.run()




