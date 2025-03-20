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
    ot.settings(time_step=60, screen_output_time_interval=1800,
                #use_dispersion=False,
            # use_A_Z_profile=False,
            regrid_z_to_uniform_sigma_levels=False,
             #NUMBA_cache_code=True,
                #NCDF_particle_chunk= 50000
                )

    ot.add_class('tracks_writer',update_interval = 600, write_dry_cell_flag=False,
                 turn_on_write_particle_properties_list=['z_fraction', 'z_fraction_water_velocity'],
               time_steps_per_per_file= None if args.reference_case else 10  # dont split files ref case to test reading split files
               ) # keep file small

    #ot.settings(NUMBA_cache_code = True)
    hm = test_definitions.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'])

    # add a point release
    ot.add_class('release_groups',**test_definitions.rg_ploy1)


    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role
    ot.add_class('particle_properties', class_name='WaterSpeed')
    ot.add_class('particle_properties', class_name='AgeDecay', name='test_decay')
    ot.add_class('particle_properties', class_name='DistanceTravelled')

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**test_definitions.ps1)



    ot.add_class('resuspension', critical_friction_velocity=0.01)
    ot.add_class('velocity_modifiers',name= 'terminal_velocity_test',
                                    class_name='TerminalVelocity', value= -0.001)

    case_info_file = ot.run()


    tracks= test_definitions.read_tracks(case_info_file)

    dz = tracks['x'][:,:,2] + tracks['water_depth']

    sel = tracks['z_fraction'] < 0
    print('z fraction  < 0  ', sel.sum())

    sel = tracks['z_fraction'] > 1
    print('z fraction  >1 ', np.count_nonzero(sel))

    test_definitions.show_track_plot(case_info_file, args)
    if args.plot:
        from matplotlib import pyplot as plt


        t = tracks['time']/3600/24
        t = t-t[0]
        plt.plot(t,dz)
        plt.title('distance above bottom, m')
        plt.xlabel('Time. days')
        plt.show()



    return  ot.params



