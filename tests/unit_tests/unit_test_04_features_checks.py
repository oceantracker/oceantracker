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
    ot.settings(time_step=1800 )

    ot.add_class('tracks_writer',update_interval = 1*3600, write_dry_cell_flag=False,
                 NCDF_particle_chunk= 500) # keep file small

    #ot.settings(NUMBA_cache_code = True)
    hm = test_definitions.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'])

    # add a point releases
    ot.add_class('release_groups',**test_definitions.rg3points)

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**test_definitions.ps1)

    ot.add_class('particle_statistics', **test_definitions.poly_stats,
                 polygon_list=[dict(points=hm['polygon'])])

    ot.add_class('resuspension', critical_friction_velocity=0.01)

    # features

    ot.add_class('trajectory_modifiers',class_name='CullParticles',
                        probability=1.,#interval=3600,
                        statuses=['stranded_by_tide','on_bottom']
                        )
    ot.add_class('trajectory_modifiers', class_name='CullParticles',
                 probability=.5,   interval=3600, statuses=['on_bottom']
                 )
    ot.add_class('trajectory_modifiers', class_name='SplitParticles',
                 probability=1,   interval=2*3600,min_age=3600
                 )
    case_info_file = ot.run()







