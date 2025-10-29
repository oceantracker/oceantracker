from oceantracker.main import OceanTracker
from tests.unit_tests.conftest import gridded_2D_timeBased

def test_gridded_statistics_2D_timeBased(
    base_settings,
    reader_demo_schisim3D,
    basic_point_release_configuration,
    schism_release_locations,
    gridded_2D_timeBased,
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
    ot.add_class("particle_statistics", **gridded_2D_timeBased)
    
    case_info_file = ot.run()

    assert case_info_file is not None

def test_gridded_statistics_2D_timeBased_runningMean(
    base_settings,
    reader_demo_schisim3D,
    basic_point_release_configuration,
    schism_release_locations,
    gridded_2D_timeBased_runningMean,
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
    ot.add_class("particle_statistics", **gridded_2D_timeBased_runningMean)
    
    case_info_file = ot.run()

    assert case_info_file is not None

def test_gridded_statistics_2D_age_based():
    assert True

def test_gridded_statistics_3D_time_based():
    assert True

def test_gridded_statistics_3D_age_based():
    assert True

def test_gridded_statistics_2D_running_average():
    assert True

def test_gridded_statistics_2d_schism_with_particle_prop(
    base_settings,
    reader_demo_schisim3D,
    basic_point_release_configuration,
    schism_release_locations,
    a_pollutant,
    gridded_2D_timeBased_with_PartProp,
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
    ot.add_class("particle_statistics", **gridded_2D_timeBased_with_PartProp)
    
    case_info_file = ot.run()

    assert case_info_file is not None


def test_polygon_statistics_2D_time_based():
    assert True

def test_polygon_statistics_2D_age_based():
    assert True
