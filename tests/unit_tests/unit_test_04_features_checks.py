from os import path, sep
from oceantracker.main import OceanTracker
from oceantracker import  definitions
from plot_oceantracker import plot_tracks
import  argparse
import shutil
import numpy as np
from tests.unit_tests import test_definitions

def main(args):
    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__,args))
    ot.settings(time_step=1800,
                particle_buffer_initial_size=20000,
                min_dead_to_remove = 500,
                screen_output_time_interval=1800,
                add_path=[ path.join(definitions.ot_root_dir, 'tutorials_how_to')],
                processors=1)

    ot.add_class('tracks_writer',update_interval = 1800, write_dry_cell_flag=False)

    #ot.settings(NUMBA_cache_code = True)
    hm = test_definitions.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'])

    # add a point releases
    ot.add_class('release_groups',**dict(test_definitions.rg3points,pulse_size=100))

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
    #ot.add_class('trajectory_modifiers', class_name='SplitParticles', probability=1,   interval=2*3600,min_age=3600)

    ot.add_class('particle_properties', name='moving_time',  class_name='my_part_prop.TimeAtStatus',  required_status= 'moving')
    ot.add_class('particle_properties', name='stranded', class_name='my_part_prop.TimeAtStatus',   required_status='stranded_by_tide')

    case_info_file = ot.run()

    from read_oceantracker.python import load_output_files
    tracks = load_output_files.load_track_data(case_info_file)

    if args.plot:
        from matplotlib import pyplot as plt

        # plot last time step
        plt.hist(tracks['moving_time'][-1,:]/3600,np.arange(0,24,.5), label='moving')
        plt.hist(tracks['stranded'][-1,:]/60, np.arange(0, 24,.5),label='stranded')
        plt.xlabel('Time at status,  hours')
        plt.legend()
        plt.yscale('log')
        plt.show()







