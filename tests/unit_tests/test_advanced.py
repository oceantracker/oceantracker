from oceantracker.main import OceanTracker
import os
import pytest
import json


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


def test_regridding(default_advanced_tests_configuration, reader_demo_schism3D):
    ot = default_advanced_tests_configuration
    # Override settings with regrid option
    ot.add_class(
        "reader",
        **{**reader_demo_schism3D, "regrid_z_to_sigma_levels": True},
    )
    ot.settings()
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


def test_settle_in_polygon(
    default_advanced_tests_configuration, schism3D_release_locations
):
    ot = default_advanced_tests_configuration
    ot.add_class(
        "trajectory_modifiers",
        name="SurfaceFloat",
        class_name="SettleInPolygon",
        polygon=schism3D_release_locations["polygons"][0],
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


def test_continue_feature_full_hindcast_avail(default_advanced_tests_configuration):
    ot_part1 = default_advanced_tests_configuration
    # reduce runtime to half the base duration (i.e. hindcast time)
    ot_part1.settings(
        continuable=True,
        max_run_duration=12 * 3600,  # 12 hours
        run_output_dir=os.path.join(
            ot_part1.params["run_output_dir"], "test_continue_basic_part1"
        ),
    )
    case_info_file = ot_part1.run()

    # get path of previous run from json to point the next run to it
    with open(case_info_file, "r") as file:
        case_info = json.load(file)
    output_dir = case_info["output_files"]["run_output_dir"]

    ot_part2 = default_advanced_tests_configuration
    ot_part2.settings(
        continue_from=output_dir,
        max_run_duration=24 * 3600,
        run_output_dir=os.path.join(
            ot_part1.params["run_output_dir"], "test_continue_basic_part2"
        ),
    )
    case_info_file = ot_part2.run()
    assert case_info_file is not None


def test_continue_feature_partial_hindcast_avail(
    base_settings,
    default_run_output_dir,
    reader_schism3D,
    basic_point_release,
    schism3D_release_locations,
):
    ot_part1 = OceanTracker()
    ot_part1.settings(
        **{
            **base_settings,
            "continuable": True,
            "continue_from": None,
            "max_run_duration": 72 * 3600,
            "run_output_dir": os.path.join(
                default_run_output_dir, "test_continue_basic_part1"
            ),
        }
    )
    ot_part1.add_class(
        "reader", **{**reader_schism3D, "file_mask": "schism3D_00[01].nc"}
    )
    ot_part1.add_class(
        "release_groups",
        **{**basic_point_release, "points": schism3D_release_locations["deep_point"]},
    )
    case_info_file = ot_part1.run()

    # get path of previous run from json to point the next run to it
    with open(case_info_file, "r") as file:
        case_info = json.load(file)
    output_dir = case_info["output_files"]["run_output_dir"]

    ot_part2 = OceanTracker()
    ot_part2.settings(
        **{
            **base_settings,
            "continuable": True,
            "continue_from": output_dir,
            "max_run_duration": 72 * 3600,
            "run_output_dir": os.path.join(
                default_run_output_dir, "test_continue_basic_part2"
            ),
        }
    )
    ot_part2.add_class(
        "reader", **{**reader_schism3D, "file_mask": "schism3D_00[12].nc"}
    )
    ot_part2.add_class(
        "release_groups",
        **{**basic_point_release, "points": schism3D_release_locations["deep_point"]},
    )
    ot_part2.settings(
        continue_from=output_dir,
        max_run_duration=24 * 3600,
        run_output_dir=os.path.join(
            ot_part1.params["run_output_dir"], "test_continue_basic_part2"
        ),
    )
    case_info_file = ot_part2.run()
    assert case_info_file is not None
