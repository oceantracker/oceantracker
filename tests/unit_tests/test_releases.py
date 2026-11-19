import numpy as np
import pytest
from oceantracker.main import OceanTracker
from oceantracker.read_output.python import load_output_files
from oceantracker.read_output.python.load_output_files import read_case_info_file


@pytest.fixture
def default_release_configuration(base_settings, reader_demo_schism3D):
    """Returns a pre-configured OceanTracker instance with base settings and reader."""
    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_demo_schism3D)
    return ot


def test_polygon_release_meter(
    default_release_configuration,
    polygon_release_configuration,
    schism3D_release_locations,
):
    ot = default_release_configuration
    ot.add_class(
        "release_groups",
        **{
            **polygon_release_configuration,
            "points": schism3D_release_locations["polygons"][0]["points"],
        },
    )
    case_info_file = ot.run()

    assert case_info_file is not None


def test_polygon_release_lon_lat(
    default_release_configuration,
    reader_schism3D_v5,
    polygon_release_configuration,
    schism3Dv5_release_locations,
):
    ot = default_release_configuration
    # rewriting default reader
    ot.add_class("reader", **reader_schism3D_v5)
    ot.add_class(
        "release_groups",
        **{
            **polygon_release_configuration,
            "points": schism3Dv5_release_locations["polygons"][0]["points"],
        },
    )
    case_info_file = ot.run()

    assert case_info_file is not None


def test_grid_release(
    default_release_configuration,
    grid_release_meters,
    schism3D_release_locations,
):
    ot = default_release_configuration
    ot.add_class(
        "release_groups",
        **{**grid_release_meters, "grid_center": schism3D_release_locations["point"]},
    )
    case_info_file = ot.run()

    assert case_info_file is not None


def test_radius_release(
    default_release_configuration,
    radius_release_meters,
    schism3D_release_locations,
):
    ot = default_release_configuration
    ot.add_class(
        "release_groups",
        **{**radius_release_meters, "points": schism3D_release_locations["deep_point"]},
    )
    case_info_file = ot.run()

    assert case_info_file is not None


def test_downstream_point_release(
    default_release_configuration,
    downstream_point_release_configuration,
    schism3D_release_locations,
):
    ot = default_release_configuration
    ot.add_class(
        "release_groups",
        **{
            **downstream_point_release_configuration,
            "points": schism3D_release_locations["multi_point"],
        },
    )
    case_info_file = ot.run()

    assert case_info_file is not None


def test_max_particles_limits_releases(
    default_release_configuration,
    basic_point_release,
    schism3D_release_locations,
):
    # pulses of 5 particles, so third pulse would exceed max_particles and is not released, nor are later pulses
    ot = default_release_configuration
    ot.settings(max_particles=12)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": [schism3D_release_locations["point"]]},
    )
    case_info_file = ot.run()

    case_info = read_case_info_file(case_info_file)
    assert case_info["run_info"]["number_particles_released"] == 10
    assert case_info["core_class_roles_info"]["particle_group_manager"]["particles_not_released_max_particles"] > 0
    strong_warnings = case_info["errors_warnings_notes"]["strong_warning"]
    assert sum("max_particles" in m for m in strong_warnings) == 1  # warned only once


@pytest.mark.parametrize(
    "release_fixture, points_key",
    [
        ("basic_point_release", "multi_point"),
        ("downstream_point_release_configuration", "multi_point"),
        ("grid_release_meters", "point"),
        ("radius_release_meters", "deep_point"),
        ("polygon_release_configuration", "polygons"),
    ],
)
def test_IDpulse_numbers_each_pulse(
    request, default_release_configuration, schism3D_release_locations, release_fixture, points_key
):
    # point and grid releases clone release info cached at setup, so IDpulse must be set per pulse, not cached
    locations = schism3D_release_locations
    location_param = {
        "multi_point": {"points": locations["multi_point"]},
        "point": {"grid_center": locations["point"]},
        "deep_point": {"points": locations["deep_point"]},
        "polygons": {"points": locations["polygons"][0]["points"]},
    }[points_key]

    ot = default_release_configuration
    ot.settings(write_tracks=True, max_run_duration=6 * 3600)
    ot.add_class("release_groups", **{**request.getfixturevalue(release_fixture), **location_param})
    case_info_file = ot.run()

    tracks = load_output_files.load_track_data(case_info_file)
    IDpulse, time_released = tracks["IDpulse"], tracks["time_released"]
    release_times = np.unique(time_released)
    assert release_times.size > 1
    # each particle's IDpulse is the zero based index of the pulse it was released in
    np.testing.assert_array_equal(IDpulse, np.searchsorted(release_times, time_released))


@pytest.mark.skip(reason="Not implemented yet")
def test_release_at_surface():
    pass


@pytest.mark.skip(reason="Not implemented yet")
def test_datetime_start_stop_releases():
    pass
