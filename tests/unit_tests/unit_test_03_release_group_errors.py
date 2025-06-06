from oceantracker.main import OceanTracker
from copy import deepcopy
from tests.unit_tests import test_definitions

def main(args):
    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__, args))
    hm = test_definitions.hydro_model['demoSchism3D']

    ot.settings(time_step=1800,use_dispersion=False,backtracking=True,
             use_A_Z_profile=False, )


    #ot.settings(NUMBA_cache_code = True)
    ot.add_class('reader', **hm['reader'])

    # add a point release outside domain
    rg =  deepcopy(test_definitions.rg_start_in_datetime1)
    rg['points'] = [0,0,1]
    rg['z_min'] = -2
    ot.add_class('release_groups', **rg)

    ot.add_class('tracks_writer',update_interval = 1*3600, write_dry_cell_flag=False)

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**test_definitions.ps1)
    ot.add_class('resuspension', critical_friction_velocity=0.01)
    case_info_file = ot.run()




