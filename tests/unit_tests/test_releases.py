import pytest
from oceantracker.main import OceanTracker


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


@pytest.mark.skip(reason="Not implemented yet")
def test_release_at_surface():
    pass


@pytest.mark.skip(reason="Not implemented yet")
def test_datetime_start_stop_releases():
    pass
