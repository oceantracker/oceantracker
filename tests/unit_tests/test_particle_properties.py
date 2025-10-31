from oceantracker.main import OceanTracker
import pytest

def test_age_decay(
    base_settings,
    reader_schism3D,
    basic_point_release,
    schism_release_locations,
    a_pollutant,
):

    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": schism_release_locations["deep_point"]},
    )
    ot.add_class("particle_properties", **a_pollutant)  # Required by heat map config
    case_info_file = ot.run()

    assert case_info_file is not None

@pytest.mark.skip(reason="Not implemented yet")
def test_distance_travelled():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_total_water_depth():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_water_speed():
    pass