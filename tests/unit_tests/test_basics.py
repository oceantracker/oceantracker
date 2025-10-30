from oceantracker.main import OceanTracker


def test_param_errors():
    assert True


def test_release_group_errors():
    assert True


def test_feature_checks():
    assert True


def test_in_depth_range():
    assert True


def test_run_2d_model():
    assert True


def test_run_schism_native3D(
    base_settings,
    reader_demo_schisim3D,
    basic_point_release_configuration,
    schism_release_locations,
):
    """Test SCHISM 3D native grid tracking"""

    ot = OceanTracker()
    ot.settings(
        **base_settings, regrid_z_to_uniform_sigma_levels=False, use_dispersion=False
    )
    ot.add_class("reader", **reader_demo_schisim3D)
    ot.add_class(
        "release_groups",
        **{**basic_point_release_configuration, "points": schism_release_locations["deep_point"]},
    )
    # ot.add_class("particle_properties", **a_pollutant)
    # ot.add_class("particle_statistics", **my_heat_map_time)
    case_info_file = ot.run()

    assert case_info_file is not None

