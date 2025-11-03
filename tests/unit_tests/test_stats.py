from oceantracker.main import OceanTracker
import pytest


@pytest.fixture
def default_stats_configuration(
    base_settings, reader_schism3D, basic_point_release, schism_release_locations
):
    """Returns a pre-configured OceanTracker instance with common setup."""
    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": schism_release_locations["deep_point"]},
    )
    return ot


def test_gridded_statistics_2D_timeBased(
    default_stats_configuration, gridded_2D_timeBased
):
    ot = default_stats_configuration
    ot.add_class("particle_statistics", **gridded_2D_timeBased)
    case_info_file = ot.run()
    assert case_info_file is not None


def test_gridded_statistics_2D_timeBased_runningMean(
    gridded_2D_timeBased_runningMean,
):
    ot = default_stats_configuration
    ot.add_class("particle_statistics", **gridded_2D_timeBased_runningMean)
    case_info_file = ot.run()
    assert case_info_file is not None


@pytest.mark.skip(reason="Not implemented yet")
def test_gridded_statistics_2D_age_based():
    assert True


def test_gridded_statistics_3D_time_based(
    gridded_3D_timeBased,
):
    ot = default_stats_configuration
    ot.add_class("particle_statistics", **gridded_3D_timeBased)
    case_info_file = ot.run()

    assert case_info_file is not None


@pytest.mark.skip(reason="Not implemented yet")
def test_gridded_statistics_3D_age_based():
    assert True


def test_gridded_statistics_2D_schism_with_particle_prop(
    a_pollutant,
    gridded_2D_timeBased_with_PartProp,
):
    ot = default_stats_configuration
    ot.add_class("particle_properties", **a_pollutant)  # Required by heat map config
    ot.add_class("particle_statistics", **gridded_2D_timeBased_with_PartProp)

    case_info_file = ot.run()

    assert case_info_file is not None


@pytest.mark.skip(reason="Not implemented yet")
def test_polygon_statistics_2D_time_based():
    assert True


@pytest.mark.skip(reason="Not implemented yet")
def test_polygon_statistics_2D_age_based():
    assert True
