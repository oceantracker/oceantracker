from oceantracker.main import OceanTracker
from tests.dev_runs import dd


def main(args):
    ot = OceanTracker()
    ot.settings(**dd.base_settings(__file__, args))
    ot.settings(time_step=1800,use_dispersion=False,
                screen_output_time_interval=1800,
            particle_buffer_initial_size= 100_000,
             #NUMBA_cache_code=True,
                use_resuspension = False,
                min_dead_to_remove=500,
        )
    hm = dd.hydro_model['demoSchism3D']
    ot.add_class('reader', **hm['reader'])

    # add a point release
    pulse_size = 1000
    ot.add_class('release_groups',**dict(dd.rg_basic,
                                         max_age=6*3600,
                                         pulse_size=pulse_size, release_interval=1800 ))

    ot.add_class('particle_properties', name='water_speed', class_name='VectorMagnitude2D',
                 vector_part_prop='water_velocity')

    rect_class ='oceantracker.tracks_writer.deprecated.track_writer_retangular.RectangularTracksWriter'
    ot.add_class('tracks_writer',update_interval=1800,
                 class_name= 'CompactTracksWriter' if args.reference_case else rect_class,
                 time_steps_per_per_file= 10)

    ot.add_class('particle_properties', **dd.pp1)  # add a new property to particle_properties role

    if not args.norun:
        case_info_file = ot.run()
    else:
        case_info_file=  r"C:\Auck_work\oceantracker_output\unit_tests\unit_test_18_rectangular_compact_tracks_00\unit_test_18_rectangular_compact_tracks_00_caseInfo.json"

    dd.compare_reference(case_info_file, args)


    return  ot.params



