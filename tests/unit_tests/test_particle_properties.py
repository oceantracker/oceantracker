from oceantracker.main import OceanTracker
from oceantracker.particle_properties._base_particle_properties import CustomParticleProperty
from oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier
from oceantracker.read_output.python import load_output_files
from oceantracker.shared_info import shared_info as si
import numpy as np
import pytest


class UpdateCounter(CustomParticleProperty):
    # counts how often update is called for each particle
    def update(self, n_time_step, time_sec, active):
        self.data[active] += 1


class RecordAgeAtRelease(_BaseTrajectoryModifier):
    # records the age trajectory modifiers see for particles released at the current time step,
    # and whether any of them were placed in buffer slots freed by removing dead particles
    ages_at_release = []
    buffer_slot_reused = False
    max_buffer_index = -1

    def update(self, n_time_step, time_sec, active):
        cls = RecordAgeAtRelease
        part_prop = si.class_roles.particle_properties
        new = active[part_prop["time_released"].get_values(active) == time_sec]
        if new.size == 0: return
        cls.ages_at_release.append(part_prop["age"].get_values(new))
        cls.buffer_slot_reused |= bool(new.min() <= cls.max_buffer_index)
        cls.max_buffer_index = max(cls.max_buffer_index, int(new.max()))


@pytest.fixture
def default_particle_properties_configuration(
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
    default_particle_properties_configuration, schism3D_release_locations
):
    ot = default_particle_properties_configuration
    ot.add_class(
        "particle_properties",
        name="my_inside_poly",
        class_name="oceantracker.particle_properties.inside_polygons.InsidePolygonsNonOverlapping2D",
        polygon_list=schism3D_release_locations["polygons"],
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


def test_custom_property_updated_once_per_time_step(
    default_particle_properties_configuration, base_settings
):
    ot = default_particle_properties_configuration
    ot.settings(write_tracks=True)
    ot.add_class(
        "particle_properties",
        name="update_count",
        class_name="tests.unit_tests.test_particle_properties.UpdateCounter",
    )
    case_info_file = ot.run()
    assert case_info_file is not None

    tracks = load_output_files.load_track_data(case_info_file)
    age, count = tracks["age"], tracks["update_count"]
    released = tracks["status"] >= 0
    # one update in the time step a particle is released, then one per time step
    np.testing.assert_array_equal(count[released], age[released] / base_settings["time_step"] + 1)
