from oceantracker.main import OceanTracker
import pytest

# @pytest.mark.dependency(depends=['test_basics::test_run_3D_model'])
# def test_point_release():
    # """This test relies on test_run_3D_model from test_basics.py"""
    # assert test_run_3D_model()

def test_polygon_release(
    base_settings,
    reader_schism3D,
    polygon_release_configuration,
    schism_release_locations,
):
    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        **{**polygon_release_configuration, "points": schism_release_locations["deep_polygon"]},
    )
    case_info_file = ot.run()

    assert case_info_file is not None

def test_grid_release(
    base_settings,
    reader_schism3D,
    grid_release_meters,
    schism_release_locations,
):
    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        **{**grid_release_meters, "grid_center": schism_release_locations["point"]},
    )
    case_info_file = ot.run()

    assert case_info_file is not None

def test_radius_release(
    base_settings,
    reader_schism3D,
    radius_release_meters,
    schism_release_locations,
):
    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        **{**radius_release_meters, "points": schism_release_locations["deep_point"]},
    )
    case_info_file = ot.run()

    assert case_info_file is not None

def test_downstream_point_release(
    base_settings,
    reader_schism3D,
    downstream_point_release_configuration,
    schism_release_locations,
):

    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        **{**downstream_point_release_configuration, "points": schism_release_locations["multi_point"]},
    )
    case_info_file = ot.run()

    assert case_info_file is not None