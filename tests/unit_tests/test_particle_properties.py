from oceantracker.main import OceanTracker

def test_age_decay(
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
    ot.add_class("particle_properties", **a_pollutant)  # Required by heat map config

def test_distance_travelled():
    pass

def test_total_water_depth():
    pass

def test_water_speed():
    pass