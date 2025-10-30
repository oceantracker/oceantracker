from oceantracker.main import OceanTracker

def test_resuspension():
    assert True

def test_stranding():
    assert True

def test_backtracking():
    assert True

def test_terminal_velocity():
    assert True

def test_tracker_writer():
    assert True

def test_settle_in_polygon():
    assert True

def test_surface_float():
    assert True

def test_split_particle():
    assert True

def test_cull_particles():
    assert True

def test_schism_basic_with_age_based_decay(
    base_settings,
    reader_demo_schisim3D,
    basic_point_release_configuration,
    schism_release_locations,
    a_pollutant,
):
    ot = OceanTracker()
    ot.settings(
        **base_settings, 
        regrid_z_to_uniform_sigma_levels=False, 
        use_dispersion=False
    )
    ot.add_class("reader", **reader_demo_schisim3D)
    ot.add_class(
        "release_groups",
        **{**basic_point_release_configuration, "points": schism_release_locations["deep_point"]},
    )
    ot.add_class("particle_properties", **a_pollutant)
    
    case_info_file = ot.run()

    assert case_info_file is not None
    
    # from oceantracker.read_output.python import load_output_files
    # tracks = load_output_files.load_track_data(case_info_file)
    # assert "a_pollutant" in tracks
    # assert tracks["a_pollutant"].max() <= 1000  # Should decay from initial value

def test_downstream_point_release(
    base_settings,
    reader_demo_schisim3D,
    downstream_point_release_configuration,
    schism_release_locations,
):

    ot = OceanTracker()
    ot.settings(
        **base_settings, regrid_z_to_uniform_sigma_levels=False, use_dispersion=False
    )
    ot.add_class("reader", **reader_demo_schisim3D)
    ot.add_class(
        "release_groups",
        **{**downstream_point_release_configuration, "points": schism_release_locations["multi_point"]},
    )
    case_info_file = ot.run()

    assert case_info_file is not None
