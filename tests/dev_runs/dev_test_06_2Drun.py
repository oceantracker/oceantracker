from oceantracker.main import OceanTracker

import dd

def main(args):
    ot = OceanTracker()
    ot.settings(**dd.base_settings(__file__,args))
    ot.settings(time_step=1800,
                use_dispersion=False,
             use_A_Z_profile=False,
            NUMBA_cache_code=True,
            cache_hindcast_catalog=True,
            )

    ot.add_class('tracks_writer',update_interval = 1*3600, write_dry_cell_flag=False)

    #ot.settings(NUMBA_cache_code = True)
    hm = dd.hydro_model['demoSchism2D']
    hm['reader'].update( file_mask='Random_order*.nc')
    ot.add_class('reader', **hm['reader'])

    # add a point release
    ot.add_class('release_groups',**dd.rg_release_interval0)
    ot.add_class('release_groups', **dd.rg_start_in_datetime1)


    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **dd.pp1) # add a new property to particle_properties role
    ot.add_class('particle_properties',name='water_speed', class_name='VectorMagnitude2D',vector_part_prop='water_velocity')

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**dd.my_heat_map_time)

    ot.add_class('particle_statistics', **dd.my_poly_stats_time,
                 polygon_list=[dict(points=hm['polygon'])])
    ot.add_class('tracks_writer',update_interval = 1*3600, write_dry_cell_flag=False,
                 turn_on_write_particle_properties_list=['nz_cell','z_fraction_water_velocity','z_fraction','water_velocity'],
               time_steps_per_per_file= None if args.reference_case else 10  # dont split files ref case to test reading split files
                 )
    case_info_file = ot.run()

    dd.compare_reference(case_info_file, args)





