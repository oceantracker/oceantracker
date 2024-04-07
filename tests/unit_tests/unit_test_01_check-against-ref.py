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

    ot.add_class('tracks_writer',update_interval = 1*3600, write_dry_cell_flag=False,
                 NCDF_particle_chunk= 500) # keep file small

    #ot.settings(NUMBA_cache_code = True)
    ot.add_class('reader',**test_definitions.reader1)

    # add a point release
    ot.add_class('release_groups',**test_definitions.rg_release_interval0)
    ot.add_class('release_groups', **test_definitions.rg_start_in_middle)
    ot.add_class('release_groups', **test_definitions.rg_outside_domain)

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**test_definitions.ps1)
    ot.add_class('resuspension', critical_friction_velocity=0.01)
    case_info_file = ot.run()

    reference_case_info_file = case_info_file.replace('output','reference_case_output')
    if args.reference_case:
        # rewrite reference case output
        shutil.copytree(path.dirname(case_info_file), path.dirname(reference_case_info_file),dirs_exist_ok=True)

    tracks= test_definitions.read_tracks(case_info_file)
    tracks_ref = test_definitions.read_tracks(reference_case_info_file)
    dx = np.abs(tracks['x']- tracks_ref['x'])
    print('x diffs 3 max/ 3 mean ', np.concatenate((np.nanmax(dx, axis=1),np.nanmean(dx, axis=1)),axis=1))




