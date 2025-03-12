from os import path, sep



from oceantracker.main import OceanTracker

from plot_oceantracker import plot_tracks
import  argparse
import shutil
import numpy as np
from tests.unit_tests import test_definitions
from matplotlib import  pyplot as plt

def main(args):
    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__,args))


    time_step =60
    ot.settings(time_step=time_step,
                screen_output_time_interval=600,
             use_A_Z_profile=False,
            regrid_z_to_uniform_sigma_levels=False,
             NUMBA_cache_code=True,
                #NCDF_particle_chunk= 50000
                )

    ot.add_class('tracks_writer',update_interval = time_step, write_dry_cell_flag=True,)
    #ot.settings(NUMBA_cache_code = True)
    hm = test_definitions.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'])

    # add a point release
    ot.add_class('release_groups',
                 name='point1',
                 points=[1597682.1237, 5489972.7479],release_at_surface=True,
                 release_interval=0, pulse_size=5000)

    ot.add_class('velocity_modifiers', class_name='TerminalVelocity', name='fall_vel',value=-0.01)

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**test_definitions.ps1)



    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role
    ot.add_class('particle_properties', class_name='WaterSpeed')
    ot.add_class('particle_properties', class_name='AgeDecay', name='test_decay')
    ot.add_class('particle_properties', class_name='DistanceTravelled')


    # run with default resupension
    ot.add_class('resuspension', critical_friction_velocity=0.01, class_name='Resuspension')
    case_info_file1 = ot.run()

    # compare water depth at that in schism zcor
    if args.plot:
        from read_oceantracker.python import load_output_files
        cs = load_output_files.read_case_info_file(case_info_file1)
        from oceantracker.util.ncdf_util import NetCDFhandler
        nc = NetCDFhandler('../../tutorials_how_to/demo_hindcast/schsim3D/demo_hindcast_schisim3D_00.nc')

        d = nc.read_variables()
        from oceantracker.reader.util import reader_util
        zcor = d['zcor']
        depth_zcor= -reader_util.get_values_at_ragged_bottom(zcor[:,:,:,np.newaxis],d['node_bottom_index']-1)
        depth_zcor = np.squeeze(depth_zcor)
        depth = np.tile( d['depth'][np.newaxis, : ],(depth_zcor.shape[0],1))

        if True:
            nt = 3
            plt.scatter(depth[nt,:], depth_zcor[nt, :], s=4)
            plt.plot([0,35], [0,35],c='g')
            plt.xlabel('depth')
            plt.ylabel('zcorr depth')
            plt.show()


        plt.scatter(depth, depth-depth_zcor, s=4)
        plt.plot([0, 35], [0, 0], c='g')
        plt.xlabel('depth')
        plt.ylabel('depth - zcor_depth')
        plt.show()


    test_definitions.plot_vert_section(case_info_file1, fraction_to_read=0.01)

    if True:
        from read_oceantracker.python import load_output_files
        tracks1 = load_output_files.load_track_data(case_info_file1,fraction_to_read=0.01)
        plt.plot(tracks1['x'][:,:,2] + tracks1['water_depth'])
        plt.show()

    if True:
        test_definitions.show_track_plot(case_info_file1, args)



    # run with basic resupension
    if True:
        ot.add_class('resuspension', critical_friction_velocity=0.01, class_name='BasicResuspension')
        case_info_file2 = ot.run()
        test_definitions.show_track_plot(case_info_file2, args)
        test_definitions.plot_vert_section(case_info_file2, fraction_to_read=0.01)


    return  ot.params



