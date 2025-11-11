from oceantracker.main import OceanTracker
import pytest


@pytest.fixture
def default_particle_properties_configuration(
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


def test_age_decay(default_particle_properties_configuration, a_pollutant):
    ot = default_particle_properties_configuration
    ot.add_class("particle_properties", **a_pollutant)
    case_info_file = ot.run()
    assert case_info_file is not None


def test_distance_travelled(default_particle_properties_configuration):
    ot = default_particle_properties_configuration
    ot.add_class(
        "particle_properties",
        class_name="DistanceTravelled",
    )
    case_info_file = ot.run()
    assert case_info_file is not None


def test_fractional_water_depth(default_particle_properties_configuration):
    ot = default_particle_properties_configuration
    ot.add_class(
        "particle_properties",
        class_name="FractionalWaterDepth",
    )
    case_info_file = ot.run()
    assert case_info_file is not None


def test_inside_polygons(
    default_particle_properties_configuration, schism_release_locations
):
    ot = default_particle_properties_configuration
    ot.add_class(
        "particle_properties",
        name="my_inside_poly",
        class_name="oceantracker.particle_properties.inside_polygons.InsidePolygonsNonOverlapping2D",
        polygon_list=schism_release_locations["polygons"],
    )
    case_info_file = ot.run()
    assert case_info_file is not None


def test_rouse_number(default_particle_properties_configuration):
    ot = default_particle_properties_configuration
    ot.add_class(
        "velocity_modifiers",
        name="my_terminal_velocity",
        class_name="TerminalVelocity",
        value=-0.001,
    )
    ot.add_class(
        "particle_properties",
        class_name="RouseNumber",
        name="rouse_number",
        terminal_velocity_name="my_terminal_velocity",
    )
    case_info_file = ot.run()
    assert case_info_file is not None


# @pytest.mark.skip()
def test_particle_load(default_particle_properties_configuration):
    ot = default_particle_properties_configuration
    ot.add_class(
        "particle_properties",
        name="my_particle_load",
        class_name="ParticleLoad",
        initial_value=100,
    )
    case_info_file = ot.run()
    assert case_info_file is not None


def test_total_water_depth(default_particle_properties_configuration):
    ot = default_particle_properties_configuration
    ot.add_class(
        "particle_properties",
        name="total_water_depth",
        class_name="TotalWaterDepth",
    )
    case_info_file = ot.run()
    assert case_info_file is not None


def test_water_speed(default_particle_properties_configuration):
    ot = default_particle_properties_configuration
    ot.add_class(
        "particle_properties",
        name="water_speed",
        class_name="VectorMagnitude2D",
        vector_part_prop="water_velocity",
    )
    case_info_file = ot.run()
    assert case_info_file is not None
