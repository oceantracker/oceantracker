from oceantracker.main import OceanTracker

import dd

def main(args):
    ot = OceanTracker()
    ot.settings(**dd.base_settings(__file__, args))
    ot.settings(time_step=1800,use_dispersion=False,
                screen_output_time_interval=1800,
             use_A_Z_profile=True,

            particle_buffer_initial_size= 200,
             NUMBA_cache_code=True,
                use_resuspension = False,
                min_dead_to_remove=50,
        )
    hm = dd.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'],  regrid_z_to_sigma_levels=False)

    # add a point release
    ot.add_class('release_groups',**dict(dd.rg_basic,max_age=2*3600))

    ot.add_class('particle_properties', name='water_speed', class_name='VectorMagnitude2D',
                 vector_part_prop='water_velocity')

    ot.add_class('tracks_writer',
                 time_steps_per_per_file=None if args.reference_case else  5)

    ot.add_class('particle_properties', **dd.pp1)  # add a new property to particle_properties role

    ot.add_class('particle_statistics', **dd.my_heat_map_time)
    ot.add_class('particle_statistics', **dd.my_poly_stats_time, polygon_list=[dict(points=hm['polygon'])])

    case_info_file = ot.run()


    if True:
        dd.compare_reference_run_tracks(case_info_file, args)
        #dd.show_track_plot(case_info_file, args)

    return  ot.params



