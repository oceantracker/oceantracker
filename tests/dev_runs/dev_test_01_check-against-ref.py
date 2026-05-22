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
                #regrid_z_to_uniform_sigma_levels=True # obsolete param
                )

    ot.add_class('tracks_writer',update_interval = 1*3600, write_dry_cell_flag=False,
                 turn_on_write_particle_properties_list=['nz_cell','z_fraction_water_velocity','z_fraction','water_velocity'],
               time_steps_per_per_file= None if args.reference_case else 10  # dont split files ref case to test reading split files

               ) # keep file small

    #ot.settings(NUMBA_cache_code = True)
    hm = dd.hydro_model['demoSchism3D']

    ot.add_class('reader', **hm['reader'], regrid_z_to_sigma_levels=True,
                 # test mapping with user give maps to existing variables
                 field_variable_map=dict(my_field='temp',
                                         water_velocity=['hvel', 'vertical_velocity'], ),
                 load_fields=['my_field'],  # request load user field
                 grid_variable_map=dict(x='SCHISM_hgrid_node_x',
                                        x_not_used='SCHISM_hgrid_node_x')
                 )

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

    ot.add_class('event_loggers', class_name='LogPolygonEntryAndExit',name='poly_entry_exit',
                                polygon_list=[dict(points=hm['polygon_around_point'])])

    if not args.norun:
        case_info_file = ot.run()
    else:
        case_info_file = dd.get_case_info_name_from_params(ot.params)

    dd.compare_reference(case_info_file, args)



    if args.plot:
        dd.show_track_plot(case_info_file,  args=args)



    dd.show_track_plot(case_info_file, args)

    return  ot.params


if __name__ == '__main__':

    main()
