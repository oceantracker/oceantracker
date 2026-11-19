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


def test_manually_updated_props_initialised_in_reused_buffer_slots(
    base_settings, reader_demo_schism3D, schism3D_release_locations
):
    """ManuallyUpdatedParticleProperty values must be (re)set at release, as new particles go into
    buffer slots holding zeros (buffer expansion) or the values of a removed dead particle.
    """
    release_point = schism3D_release_locations["deep_point"]
    x0, y0 = release_point[:2]
    box = [[x0 - 10000, y0 - 10000], [x0 + 10000, y0 - 10000], [x0 + 10000, y0 + 10000], [x0 - 10000, y0 + 10000]]
    fall_value, fall_sd = -0.001, 0.0002

    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.settings(write_tracks=True, particle_buffer_initial_size=20, min_dead_to_remove=1, use_random_seed=True)
    ot.add_class("reader", **reader_demo_schism3D)
    ot.add_class("release_groups", name="rg", class_name="PointRelease", points=[release_point],
                 release_interval=3600, pulse_size=5, max_age=2 * 3600)
    # update_interval == release_interval, so every particle is inside the box at the update at its release
    ot.add_class("particle_statistics", name="pstats", class_name="PolygonStats2D_timeBased",
                 polygon_list=[{"points": box}], update_interval=3600,
                 max_count_per_particle=1, kill_when_max_counted=False)
    ot.add_class("particle_properties", class_name="ManuallyUpdatedParticleProperty", name="test_birth_value",
                 initial_value=-7, dtype="int32", time_varying=False, write=True)
    # its inside-polygon property is manually updated, so had stale/zero values and was never updated
    ot.add_class("event_loggers", name="poly_events", class_name="LogPolygonEntryAndExit", polygon_list=[{"points": box}])
    # note: "variance" is used as a standard deviation, ie. value + variance * N(0,1)
    ot.add_class("velocity_modifiers", name="fall", class_name="TerminalVelocity", value=fall_value, variance=fall_sd)
    case_info_file = ot.run()
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(case_info_file, name="pstats")
    tracks = load_output_files.load_track_data(case_info_file)
    n_released = int(stats["num_released_total"][-1])
    assert n_released > 50, "need enough pulses for slot reuse"

    # every particle counted exactly once, including those in reused slots
    assert stats["count"].sum() == n_released, f"counted {stats['count'].sum()} of {n_released} released particles"

    # property keeps its initial_value in expanded and reused slots
    v = tracks["test_birth_value"]
    assert v.shape == (n_released,)
    assert np.all(v == -7), f"{np.sum(v != -7)} of {v.size} particles do not have initial_value -7"

    # individual terminal velocities drawn at release
    tv = tracks["terminal_velocity"]
    assert tv.shape == (n_released,)
    assert np.all(tv != 0)
    assert np.unique(tv).size == tv.size
    assert abs(tv.mean() - fall_value) < 1e-4
    assert 0.5 * fall_sd < tv.std() < 1.5 * fall_sd

    # every particle is released inside the box, so has an entry event into polygon 0
    events = load_output_files.load_events_file(case_info_file, name="poly_events")
    entered = events["event_flag"] == 1
    np.testing.assert_array_equal(np.unique(events["ID"][entered]), np.arange(n_released))
    assert np.all(events["event_polygon"][entered] == 0)

    # resetting at release must not overwrite values given by the release
    np.testing.assert_array_equal(tracks["ID"], np.arange(n_released))
    assert np.all(tracks["IDrelease_group"] == 0)
    np.testing.assert_allclose(tracks["x0"][:, :2], np.tile([x0, y0], (n_released, 1)))
    assert np.unique(tracks["time_released"]).size == n_released // 5
