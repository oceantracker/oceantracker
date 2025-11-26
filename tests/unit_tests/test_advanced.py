from oceantracker.main import OceanTracker
import pytest


@pytest.fixture
def default_advanced_tests_configuration(
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


def test_regridding(default_advanced_tests_configuration):
    ot = default_advanced_tests_configuration
    # Override settings with regrid option
    ot.settings(regrid_z_to_uniform_sigma_levels=True)
    case_info_file = ot.run()
    assert case_info_file is not None


def test_resuspension(default_advanced_tests_configuration):
    ot = default_advanced_tests_configuration
    ot.add_class("resuspension", critical_friction_velocity=0.005)
    case_info_file = ot.run()
    assert case_info_file is not None


def test_backtracking(default_advanced_tests_configuration):
    ot = default_advanced_tests_configuration
    # Override settings with backtracking option
    ot.settings(backtracking=True)
    case_info_file = ot.run()
    assert case_info_file is not None


def test_terminal_velocity(default_advanced_tests_configuration):
    ot = default_advanced_tests_configuration
    ot.add_class(
        "velocity_modifiers",
        name="terminal_velocity_test",
        class_name="TerminalVelocity",
        value=-0.001,
    )
    case_info_file = ot.run()
    assert case_info_file is not None


def test_track_writer(default_advanced_tests_configuration):
    ot = default_advanced_tests_configuration
    # Override settings with write_tracks option
    ot.settings(write_tracks=True)
    case_info_file = ot.run()
    assert case_info_file is not None


def test_settle_in_polygon(default_advanced_tests_configuration, schism3D_release_locations):
    ot = default_advanced_tests_configuration
    ot.add_class(
        "trajectory_modifiers",
        name="SurfaceFloat",
        class_name="SettleInPolygon",
        polygon=schism3D_release_locations['polygons'][0],
        probability_of_settlement=0.1,
        settlement_duration=14400,
    )
    case_info_file = ot.run()
    assert case_info_file is not None


def test_surface_float(default_advanced_tests_configuration):
    ot = default_advanced_tests_configuration
    ot.add_class(
        "trajectory_modifiers",
        name="SurfaceFloat",
        class_name="SurfaceFloat",
    )
    case_info_file = ot.run()
    assert case_info_file is not None


def test_split_particle(default_advanced_tests_configuration):
    ot = default_advanced_tests_configuration
    ot.add_class(
        "trajectory_modifiers",
        name="SplitParticles",
        class_name="SplitParticles",
        interval=3600,
        probability=0.1,
        statuses=["moving"],
    )
    case_info_file = ot.run()
    assert case_info_file is not None


def test_cull_particles(default_advanced_tests_configuration):
    ot = default_advanced_tests_configuration
    ot.add_class(
        "trajectory_modifiers",
        class_name="CullParticles",
        probability=1.0,
        interval=3600,
        statuses=["stranded_by_tide", "on_bottom"],
    )
    case_info_file = ot.run()
    assert case_info_file is not None


def test_dont_block_dry_cells(default_advanced_tests_configuration):
    ot = default_advanced_tests_configuration
    # Override settings with block_dry_cells option
    ot.settings(block_dry_cells=False)
    case_info_file = ot.run()
    assert case_info_file is not None