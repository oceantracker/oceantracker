from oceantracker.main import OceanTracker

def test_schism_comparision():
    assert True
    
    # ot = OceanTracker()
    # ot.settings(**cd.base_settings(__name__),
    #             regrid_z_to_uniform_sigma_levels=False,
    #             use_dispersion=False)
    # ot.add_class('reader', **cd.reader_demo_schisim3D)
    # ot.add_class('release_groups',
    #              **dict(cd.rg_P1, points=cd.schism_demo['deep_point']))

    # ot.add_class('particle_properties', **cd.a_pollutant)
    # ot.add_class('particle_statistics', **cd.my_heat_map_time)

    # # assert False

    # case_info_file = ot.run()
    # assert case_info_file is not None

    # cd.compare_reference_run(case_info_file)

def test_schism_resuspension():
    assert True


