from oceantracker.main import OceanTracker

import dd

def main(args):
    ot = OceanTracker()
    ot.settings(**dd.base_settings(__file__,args))
    ot.settings(time_step=1800,
                use_dispersion=False,
             use_A_Z_profile=False,
                NUMBA_cache_code=True,
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

    case_info_file = ot.run()

    dd.compare_reference_tracks(case_info_file, args)





