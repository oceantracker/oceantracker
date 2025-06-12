from oceantracker.main import OceanTracker

from tests.unit_tests import test_definitions

def main(args):
    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__,args))
    timestep =900
    ot.settings(time_step=timestep,
                screen_output_time_interval=1800,
             use_A_Z_profile=False,
            regrid_z_to_uniform_sigma_levels=False,
             NUMBA_cache_code=True,)

    ot.add_class('tracks_writer',update_interval = 1*3600, write_dry_cell_flag=False,
               time_steps_per_per_file= None if args.reference_case else 10  # dont split files ref case to test reading split files
               ) # keep file small

    #ot.settings(NUMBA_cache_code = True)
    hm = test_definitions.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'])

    # add a point release
    ot.add_class('release_groups',
                            name='point 1',  # name used internal to refer to this release
                             class_name='PointRelease',  # class to use
                             points=[[1594000, 5484200, -2]],
                             # the below are optional settings/parameters
                             release_interval=timestep,  # seconds between releasing particles
                             pulse_size=500)  # how many are released each interval
    ot.add_class('release_groups',
                            name='point 2',  # name used internal to refer to this release
                             class_name='PointRelease',  # class to use
                             points=[[1593000, 5484200, -2]],
                             # the below are optional settings/parameters
                             release_interval=timestep,  # seconds between releasing particles
                             pulse_size=500)  # how many are released each interval

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role
    ot.add_class('particle_properties', name='water_speed', class_name='VectorMagnitude2D',vector_part_prop='water_velocity')
    ot.add_class('particle_properties', class_name='AgeDecay', name='test_decay')
    ot.add_class('particle_properties', class_name='DistanceTravelled')

    # add a gridded particle statistic to plot heat map
    ps = dict(test_definitions.ps1)
    ot.add_class('particle_statistics', **dict(test_definitions.poly_stats,name='polystats_time',  polygon_list=[dict(points=hm['polygon'])]))


    ot.add_class('particle_statistics', **dict(test_definitions.poly_stats_age,name='poly_stats_age',   polygon_list=[dict(points=hm['polygon'])]))


    case_info_file = ot.run()


    test_definitions.show_track_plot(case_info_file, args)
    from oceantracker.read_output.python import load_output_files
    # check stats
    for name in ['polystats_time', 'poly_stats_age']:
        #stats_ref= load_output_files.load_stats_data(reference_case_info_file, name=name)
        stats= load_output_files.load_stats_data(case_info_file, name=name)
        #dc = stats['count'] - stats_ref['count']
        #print(' stats  name ',  name,'counts', stats_ref['count'].sum(), stats['count'].sum(),'max diff counts-ref run counts =',np.nanmax(np.abs(dc)))

    return  ot.params



