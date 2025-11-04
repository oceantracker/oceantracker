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

@pytest.fixture
def water_speed_property():
    """Water speed vector magnitude property"""
    return dict(
        name="water_speed",
        class_name="VectorMagnitude2D",
        vector_part_prop="water_velocity",
    )

@pytest.fixture
def distance_travelled_property():
    """Distance travelled property"""
    return dict(
        class_name="DistanceTravelled",
    )

@pytest.fixture
def age_decay_property():
    """Age decay property"""
    return dict(
        class_name="AgeDecay",
        name="test_decay",
    )
