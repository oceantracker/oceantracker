from oceantracker.main import OceanTracker

import numpy as np
import dd

def main(args=None):
    args= dd.check_args(args)

    ot = OceanTracker()
    ot.settings(**dd.base_settings(__file__,args))
    ot.settings(time_step=1800,
                use_dispersion=False,
                screen_output_time_interval=1800,
                use_A_Z_profile=True,

                particle_buffer_initial_size= 500,
                #NUMBA_cache_code=True,
                use_resuspension=False,

                )

    ot.add_class('tracks_writer',update_interval = 1*3600, write_dry_cell_flag=False,
                 turn_on_write_particle_properties_list=['nz_cell','z_fraction_water_velocity','z_fraction','water_velocity'],
               time_steps_per_per_file= None if args.reference_case else 10  # dont split files ref case to test reading split files

               ) # keep file small

    #ot.settings(NUMBA_cache_code = True)
    hm = dd.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'], regrid_z_to_sigma_levels=True,)

    # add a point release
    ot.add_class('release_groups',**dd.rg_release_interval0)
    ot.add_class('release_groups', **dd.rg_start_in_datetime1)

    #ot.add_class('trajectory_modifiers', class_name='oceantracker.trajectory_modifiers.surface_float.SurfaceFloat', name='surface')

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **dd.pp1) # add a new property to particle_properties role
    ot.add_class('particle_properties',name='water_speed', class_name='VectorMagnitude2D',vector_part_prop='water_velocity')
    ot.add_class('particle_properties', class_name='AgeDecay', name='test_decay')
    ot.add_class('particle_properties', class_name='DistanceTravelled')

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**dd.my_heat_map_time)
    ot.add_class('particle_statistics', **dd.my_heat_map_age)

    ot.add_class('particle_statistics', **dd.my_poly_stats_time,   polygon_list=[dict(points=hm['polygon'])])
    ot.add_class('particle_statistics', **dd.my_poly_stats_age, polygon_list=[dict(points=hm['polygon'])])

    ot.add_class('particle_statistics', **dd.my_heat_map3D_time)
    ot.add_class('particle_statistics', **dd.my_heat_map2D_time_runningMean)

    if not args.norun:
        case_info_file = ot.run()
    else:
        case_info_file = dd.get_case_info_name_from_params(ot.params)

    dd.compare_reference(case_info_file, args)


    tests=dict()
    tracks = dd.load_tracks(case_info_file)
    tracks_ref = dd.load_tracks(case_info_file, ref_case=True)

    # check z fractions are in range 0-1
    z_fraction= tracks['z_fraction']
    sel = np.logical_or(z_fraction < -.01, z_fraction > 1.01)
    tests['z_fraction'] = not np.any(sel)
    print('zfraction out of range',  'z_fraction=', np.count_nonzero(sel))

    z_fraction_water_velocity= tracks['z_fraction_water_velocity']
    sel = np.logical_or(z_fraction_water_velocity < -.01,  z_fraction_water_velocity > 1.01)
    tests['z_fraction_water_velocity'] = not np.any(sel)
    print('zfraction out of range', 'z_fraction_water_velocity=', np.count_nonzero(sel))

    print('tests passed', tests)
    if args.plot:

        from matplotlib import pyplot as plt

        n_pulse= 0
        n_release= 0

        sel = np.logical_and(tracks['IDpulse'] == n_pulse, tracks['IDrelease_group'] == n_release)

        x = tracks['x'][:, sel,:]

        sel_ref = np.logical_and(tracks_ref['IDpulse'] == n_pulse, tracks_ref['IDrelease_group'] == n_release)
        x_ref =  tracks_ref['x'][:,sel_ref,:]

        x0 = x[0,:].T
        time = (tracks_ref['time']- tracks_ref['time'][0]) / 3600 / 24

        plt.plot(x_ref[:, :, 0], x_ref[:, :, 1], c='g')
        plt.plot(x[:,:, 0], x[:,:, 1], c='r')
        plt.title('tracks')
        plt.show()

        plt.plot(time, x_ref[:,:, 0]-x0[0], c='g')
        plt.plot(time, x[:, :,0]-x0[0], c='r')
        plt.title('x-east')
        plt.show()


        fig, axs = plt.subplots(4,1)

        ax= axs[0]
        ax.plot(time, tracks_ref['status'][:, sel_ref], c='g')
        ax.plot(time, tracks['status'][:, sel],'--', c='r')
        ax.set_title('status')

        ax = axs[1]
        ax.plot(time, tracks_ref['nz_cell'][:, sel_ref], c='g')
        ax.plot(time, tracks['nz_cell'][:, sel], '--', c='r')
        ax.set_title('nz_cell')

        ax = axs[2]
        ax.plot(time, tracks_ref['z_fraction_water_velocity'][:, sel_ref], c='g')
        ax.plot(time, tracks['z_fraction_water_velocity'][:, sel],'--', c='r')
        ax.set_title('z_fraction_water_velocity')

        ax = axs[3]
        ax.plot(time, tracks_ref['tide'][:, sel_ref],'--', c='g')
        ax.plot(time, tracks['tide'][:, sel],'--', c='r')
        ax.plot(time, x_ref[:, :, 2], c='g')
        ax.plot(time, x[:, :, 2], c='r')
        ax.set_title('z')

        plt.show()


    dd.show_track_plot(case_info_file, args)

    return  ot.params


if __name__ == '__main__':

    main()
