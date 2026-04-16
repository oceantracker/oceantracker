from oceantracker.main import OceanTracker
from oceantracker.read_output.python import load_output_files
import pytest


@pytest.fixture
def default_stats_configuration(
    base_settings, reader_demo_schism3D, basic_point_release, schism3D_release_locations
):
    """Returns a pre-configured OceanTracker instance with common setup."""
    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_demo_schism3D)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": schism3D_release_locations["deep_point"]},
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
    default_stats_configuration,
    gridded_2D_timeBased_runningMean,
):
    ot = default_stats_configuration
    ot.add_class("particle_statistics", **gridded_2D_timeBased_runningMean)
    case_info_file = ot.run()
    assert case_info_file is not None


def test_gridded_statistics_2D_ageBased(
    default_stats_configuration, gridded_2D_ageBased
):
    ot = default_stats_configuration
    ot.add_class("particle_statistics", **gridded_2D_ageBased)
    case_info_file = ot.run()
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(case_info_file, name=gridded_2D_ageBased["name"])
    assert "count_all_released_age_bins" in stats, "count_all_released_age_bins missing from age-based stats output"
    assert stats["count_all_released_age_bins"].sum() > 0, "count_all_released_age_bins is all zeros — demographic computation produced no output"


def test_gridded_statistics_3D_timeBased(
    default_stats_configuration,
    gridded_3D_timeBased,
):
    ot = default_stats_configuration
    ot.add_class("particle_statistics", **gridded_3D_timeBased)
    case_info_file = ot.run()

    assert case_info_file is not None


@pytest.mark.skip(reason="Not implemented yet")
def test_gridded_statistics_3D_ageBased():
    assert True


def test_gridded_statistics_2D_schism_with_particle_prop(
    default_stats_configuration,
    a_pollutant,
    gridded_2D_timeBased_with_PartProp,
):
    ot = default_stats_configuration
    ot.add_class("particle_properties", **a_pollutant)  # Required by heat map config
    ot.add_class("particle_statistics", **gridded_2D_timeBased_with_PartProp)

    case_info_file = ot.run()

    assert case_info_file is not None


def test_polygon_statistics_2D_timeBased(
    default_stats_configuration, polygon_stats_2D_timeBased, schism3D_release_locations
):
    ot = default_stats_configuration
    ot.add_class(
        "particle_statistics",
        **{
            **polygon_stats_2D_timeBased,
            "polygon_list": schism3D_release_locations["polygons"],
        },
    )
    case_info_file = ot.run()
    assert case_info_file is not None


def test_polygon_statistics_2D_ageBased(
    default_stats_configuration, polygon_stats_2D_ageBased, schism3D_release_locations
):
    ot = default_stats_configuration
    ot.add_class(
        "particle_statistics",
        **{
            **polygon_stats_2D_ageBased,
            "polygon_list": schism3D_release_locations["polygons"],
        },
    )
    case_info_file = ot.run()
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(case_info_file, name=polygon_stats_2D_ageBased["name"])
    assert "count_all_released_age_bins" in stats, "count_all_released_age_bins missing from age-based stats output"
    assert stats["count_all_released_age_bins"].sum() > 0, "count_all_released_age_bins is all zeros — demographic computation produced no output"


def test_grid_center(
    default_stats_configuration,
    gridded_2D_timeBased,
    schism3D_release_locations,
):
    # **{**basic_point_release, "points": schism3D_release_locations["deep_point"]},
    ot = default_stats_configuration
    manually_centered_stats = {
        **(
            gridded_2D_timeBased
            | {
                "release_group_centered_grids": False,
                "grid_center": schism3D_release_locations["point"],

            }
        )
    }
    ot.add_class("particle_statistics", **manually_centered_stats)
    case_info_file = ot.run()
    assert case_info_file is not None
