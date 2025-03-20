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
                screen_output_time_interval=1800,
                use_A_Z_profile=False,
                regrid_z_to_uniform_sigma_levels=True,
                particle_buffer_initial_size= 500,
                NUMBA_cache_code=True,
                use_resuspension=False,

                )

    ot.add_class('tracks_writer',update_interval = 1*3600, write_dry_cell_flag=False,
               time_steps_per_per_file= None if args.reference_case else 10  # dont split files ref case to test reading split files

               ) # keep file small

    #ot.settings(NUMBA_cache_code = True)
    hm = test_definitions.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'])

    # add a point release
    ot.add_class('release_groups',**test_definitions.rg_release_interval0)
    ot.add_class('release_groups', **test_definitions.rg_min_depth)
    ot.add_class('release_groups', **test_definitions.rg_start_in_datetime1)
    ot.add_class('release_groups', **test_definitions.rg_outside_domain)

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

    tracks = test_definitions.read_tracks(case_info_file)
    tracks_ref = test_definitions.read_tracks(case_info_file, ref_case=True)

    test_definitions.compare_reference_run(case_info_file, args)

    if args.plot:

        from matplotlib import pyplot as plt

        n_pulse= 0
        sel = tracks['IDpulse'] == n_pulse
        x = tracks['x'][:, sel,:]

        sel_ref = tracks_ref['IDpulse'] == n_pulse
        x_ref =  tracks_ref['x'][:,sel_ref,:]

        plt.plot(x_ref[:, :, 0], x_ref[:, :, 1], c='g')
        plt.plot(x[:,:, 0], x[:,:, 1], c='r')
        plt.title('tracks')
        plt.show()

        plt.plot(tracks_ref['time'], x_ref[:,:, 0], c='g')
        plt.plot(tracks_ref['time'], x[:, :,0], c='r')
        plt.title('x-east')
        plt.show()

        plt.plot(tracks_ref['time'], x_ref[:,:, 2], c='g')
        plt.plot(tracks_ref['time'], x[:, :, 2], c='r')
        plt.title('z')
        plt.show()

        plt.plot(tracks_ref['time'], tracks_ref['status'][:, sel_ref], c='g')
        plt.plot(tracks_ref['time'], tracks['status'][:, sel], c='r')
        plt.title('status')
        plt.show()


    test_definitions.show_track_plot(case_info_file, args)

    return  ot.params



