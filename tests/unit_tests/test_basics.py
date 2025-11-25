from oceantracker.main import OceanTracker
import pytest

@pytest.mark.skip(reason="Not implemented yet")
def test_param_errors():
    assert True

@pytest.mark.skip(reason="Not implemented yet")
def test_release_group_errors():
    assert True


@pytest.mark.skip(reason="Not implemented yet")
def test_feature_checks():
    assert True


@pytest.mark.skip(reason="Not implemented yet")
def test_in_depth_range():
    assert True


@pytest.mark.skip(reason="Not implemented yet")
def test_run_2D_model():
    assert True


def test_run_3D_model(
    base_settings,
    reader_demo_schism3D,
    basic_point_release,
    schism3D_release_locations,
):
    """Test SCHISM 3D native grid tracking"""

    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_demo_schism3D)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": schism3D_release_locations["deep_point"]},
    )
    # ot.add_class("particle_properties", **a_pollutant)
    # ot.add_class("particle_statistics", **my_heat_map_time)
    case_info_file = ot.run()

    assert case_info_file is not None

