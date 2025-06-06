from oceantracker.main import OceanTracker
from copy import deepcopy
from tests.unit_tests import test_definitions

def main(args):

    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__,args))
    ot.settings(time_step=1800,use_dispersion=False,
             use_A_Z_profile=False, )

    hm= test_definitions.hydro_model['demoSchism3D']
    p = deepcopy(hm['reader'])
    p.update(unkown_param = 1,field_variables=['a1'],field_variable_map=[])
    ot.add_class('reader', **p)

    # add a point release
    ot.add_class('release_groups', start_date='hh', release_start_date='xxx', **test_definitions.rg_start_in_datetime1)

    ot.add_class('tracks_writer',update_interval_1 = 1*3600, write_dry_cell_flag=False)

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role

    # add a gridded particle statistic to plot heat map
    p = deepcopy(test_definitions.LCS)
    p.update(grid_size=[-1,9.],grid_center=hm['x0'][0], grid_span=[1000,2000])
    ot.add_class('integrated_model',   **p)
    ot.add_class('resuspension', critical_friction_velocity=-0.01)

    try:
        case_info_file = ot.run()
    except Exception as e:
        print('has errors',str(e))
        # carry on




