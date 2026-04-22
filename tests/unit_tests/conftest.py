import pytest
from os import path
from oceantracker import definitions
import numpy as np
import json
from pathlib import Path
from datetime import datetime

# Constants can stay as module-level
package_dir = path.dirname(definitions.package_dir)
demo_hindcast_dir = path.join(package_dir, "tutorials_how_to", "demo_hindcast")
unittest_hindast_dir = path.join(package_dir, "tests","unit_tests","data","hindcasts")

def pytest_collection_modifyitems(config, items):
    """Auto-skip performance/extended tests unless explicitly selected."""
    markexpr = getattr(config.option, 'markexpr', '')
    if 'performance_basic' not in markexpr and 'performance_extended' not in markexpr:
        skip = pytest.mark.skip(reason="run with: pytest -n0 -m performance_basic  (or -m performance_extended)")
        for item in items:
            if item.get_closest_marker('performance_basic') or item.get_closest_marker('performance_extended'):
                item.add_marker(skip)


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--create-reference",
        action="store_true",
        default=False,
        help="Create reference data for validation tests",
    )
    parser.addoption(
        "--create-plots",
        action="store_true",
        default=False,
        help="Create and save plots from test runs",
    )


@pytest.fixture
def create_reference_data_flag(request):
    """Flag to create reference data - set via command line or environment"""
    return request.config.getoption("--create-reference", default=False)


@pytest.fixture
def show_plots_flag(request):
    """Flag to create and save plots - set via command line"""
    return request.config.getoption("--create-plots", default=False)


@pytest.fixture
def default_run_output_dir(request):
    """Root directory for test outputs"""
    test_name = request.node.name
    return path.join(path.dirname(package_dir), "oceantracker_output", "unit_tests",test_name)


@pytest.fixture
def reference_data_dir():
    """Directory for storing reference/validation data"""
    return path.join(path.dirname(__file__), "data", "output_data")


@pytest.fixture
def reader_demo_schism3D():
    return dict(
        input_dir=path.join(demo_hindcast_dir, "schsim3D"),
        file_mask="demo_hindcast_schisim3D*.nc",
    )

@pytest.fixture
def reader_schism3D():
    return dict(
        input_dir=path.join(unittest_hindast_dir, "schism3D"),
        file_mask="*.nc",
    )


@pytest.fixture
def reader_schism3D_v5():
    return dict(
        input_dir=path.join(unittest_hindast_dir, "schism3D_v5"),
        file_mask="*.nc",
    )


@pytest.fixture
def reader_schism2D():
    return dict(
        input_dir=path.join(unittest_hindast_dir, "schism2D"),
        file_mask="*.nc",
    )


@pytest.fixture
def reader_GLORYS3D():
    return dict(
        input_dir=path.join(unittest_hindast_dir, "Glorys3DfixedZ"),
        file_mask="*.nc",
    )


@pytest.fixture
def reader_ROMS3Dsigma():
    return dict(
        input_dir=path.join(unittest_hindast_dir, "ROMS3Dsigma"),
        file_mask="*.nc",
    )


@pytest.fixture
def reader_demo_roms():
    return dict(
        input_dir=path.join(demo_hindcast_dir, "ROMS"), file_mask="ROMS3D_00*.nc"
    )


@pytest.fixture
def base_settings(request, default_run_output_dir):
    """Base settings for OceanTracker tests"""
    # Get the test function name
    return dict(
        run_output_dir=default_run_output_dir,
        time_step=1800,
        use_dispersion=False,
        write_tracks=False,
        debug=True,
    )


@pytest.fixture
def basic_point_release():
    return dict(
        name="basic",
        class_name="PointRelease",
        release_interval=1800,
        pulse_size=5,
    )


# @pytest.fixture
# def datetime_start_release_configuration():
#     """Release configuration with datetime start"""
#     return dict(
#         name="start_in_datetime1",
#         class_name="PointRelease",
#         start="2017-01-01T03:30:00",
#         release_interval=3600,
#         pulse_size=5,
#     )


@pytest.fixture
def downstream_point_release_configuration():
    return dict(
        name="downstream",
        class_name="DownstreamPointRelease",
        release_interval=1800,
        pulse_size=5,
        downstream_distance=10,
    )


@pytest.fixture
def polygon_release_configuration():
    return dict(
        name="my_polygon_release",
        class_name="PolygonRelease",
        release_interval=1800,
        pulse_size=2,
    )


@pytest.fixture
def grid_release_degrees():
    """Grid release for lat/lon in degrees"""
    return dict(
        name="my_grid_release",
        class_name="GridRelease",
        release_interval=1800,
        pulse_size=2,
        grid_span=[0.2, 0.2],
        grid_size=[3, 4],
    )


@pytest.fixture
def grid_release_meters():
    """Grid release for coordinates in meters"""
    return dict(
        name="my_grid_release",
        class_name="GridRelease",
        release_interval=1800,
        pulse_size=2,
        grid_span=[100, 100],
        grid_size=[3, 4],
    )


@pytest.fixture
def radius_release_meters():
    """Radius release for coordinates in meters"""
    return dict(
        name="my_radius_release",
        class_name="RadiusRelease",
        release_interval=1800,
        pulse_size=2,
        radius=100,
    )


@pytest.fixture
def schism3D_release_locations():
    return dict(
        point=[1594000, 5484200],
        multi_point=[
            [1594000, 5484200, -2],
            [1594100, 5485200, -2],
            [1593900, 5483200, -2],
            [1594000, 5484300, -2],
            [1593900, 5484100, -2],
        ],
        deep_point=[1594000, 5484200, -2],
        polygons=[
            {
                "points": [
                    [1597682, 5486972],
                    [1598604, 5487275],
                    [1598886, 5486464],
                    [1597917, 5484000],
                    [1597300, 5484000],
                    [1597682, 5486972],
                ]
            },
        ],
    )


@pytest.fixture
def schism2D_release_locations():
    return dict(
        point=[144.0824,-38.5238],
        deep_point=[144.0824,-38.5238,-2]
    )


@pytest.fixture
def schism3Dv5_release_locations():
    return dict(
        coastal_point=[175.05,-36.225],
        point=[175.1,-36.3],
        deep_point=[175.1,-36.3,-2],
        polygons=[
            {
                "points": [
                    [175.100000, -36.295508],
                    [175.105300, -36.298612],
                    [175.103276, -36.303634],
                    [175.096724, -36.303634],
                    [175.094700, -36.298612],
                ],
            },
        ],
    )


@pytest.fixture
def roms_demo_release_locations():
    """ROMS demo release locations (US East Coast, lat/lon order)"""
    return dict(
        point=[-69.5, 43.5],
        multi_point=[
            [-69.5, 43.5],
            [-68.96, 44.1],
        ],
        
        polygons=[
            {
                "points": [
                    [-69.0, 43.5],
                    [-69.2, 43.5],
                    [-69.2, 43.7],
                    [-69.1, 43.7],
                    [-69.0, 43.5]
                ]
            }
        ]
        )


@pytest.fixture
def roms_release_locations():
    """ROMS demo release locations (US East Coast, lat/lon order)"""
    return dict(
        point=[-66.00,44.91]
    )

@pytest.fixture
def GLORYS3D_release_locations():
    return dict(
        point=[20.5,59.9,-2],
        deep_point=[20.5,59.9,-2],
    )


@pytest.fixture
def a_pollutant():
    """Pollutant particle property configuration"""
    return dict(
        name="a_pollutant",
        class_name="oceantracker.particle_properties.age_decay.AgeDecay",
        initial_value=1000,
        decay_time_scale=7200,
    )


@pytest.fixture
def gridded_2D_timeBased():
    """Heat map statistics configuration"""
    return dict(
        name="my_heatmap_time",
        class_name="GriddedStats2D_timeBased",
        rows = 121,
        cols = 131,
        span_x = 10000,
        span_y = 10000,
        release_group_centered_grids=True,
        update_interval=7200,
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def gridded_2D_ageBased():
    """Heat map statistics configuration"""
    return dict(
        name="my_heatmap_time",
        class_name="GriddedStats2D_ageBased",
        rows = 121,
        cols = 131,
        span_x = 10000,
        span_y = 10000,
        release_group_centered_grids=True,
        max_age_to_bin=1 * 24 * 3600,
        age_bin_size=7200,
        update_interval=3600,
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def gridded_3D_timeBased():
    """Heat map statistics configuration"""
    return dict(
        name="my_heatmap_time",
        class_name="GriddedStats3D_timeBased",
        grid_size=[120, 130, 10],
        grid_span=[10000, 10000],
        release_group_centered_grids=True,
        update_interval=7200,
        status_list=["moving"],
        z_max=-5.0,
        z_min=-10.0,
    )


@pytest.fixture
def gridded_2D_timeBased_runningMean():
    """Heat map statistics configuration"""
    return dict(
        name="my_heatmap_time",
        class_name="GriddedStats2D_timeBased_runningMean",
        grid_size=[120, 130],
        grid_span=[10000, 10000],
        write_interval=7200 * 3,
        release_group_centered_grids=True,
        update_interval=7200,
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def gridded_2D_timeBased_with_PartProp():
    """Heat map statistics configuration"""
    return dict(
        name="my_heatmap_time",
        class_name="GriddedStats2D_timeBased",
        grid_size=[120, 130],
        grid_span=[10000, 10000],
        release_group_centered_grids=True,
        update_interval=7200,
        particle_property_list=["a_pollutant", "water_depth"],
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def roms_gridded_2D_timeBased():
    """ROMS-specific heat map statistics configuration (smaller grid spans for lat/lon)"""
    return dict(
        name="my_heatmap",
        class_name="GriddedStats2D_timeBased",
        grid_size=[60, 121],
        grid_span=[1, 1.5],
        release_group_centered_grids=True,
        update_interval=7200,
        particle_property_list=["water_speed"],
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def polygon_stats_2D_timeBased():
    return dict(
        name="my_poly_stats_time",
        class_name="PolygonStats2D_timeBased",
        update_interval=7200,
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def polygon_stats_2D_ageBased():
    return dict(
        name="my_poly_stats_age",
        class_name="PolygonStats2D_ageBased",
        update_interval=7200,
        max_age_to_bin=1 * 24 * 3600,
        age_bin_size=7200,
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def polygon_stats_timeBased_waterDepth():
    """Polygon statistics time-based configuration"""
    return dict(
        name="my_poly_stats_time",
        class_name="PolygonStats2D_timeBased",
        update_interval=3600,
        particle_property_list=["water_depth"],
    )


@pytest.fixture
def polygon_stats_2D_timeBased_all_released():
    """Time-based polygon stats using all_released denominator for connectivity tests"""
    return dict(
        name="my_poly_stats_time_allrel",
        class_name="PolygonStats2D_timeBased",
        update_interval=3600,
        status_list=["moving", "on_bottom", "stranded_by_tide", "stationary"],
        connectivity_denominator='all_released',
    )


@pytest.fixture
def polygon_stats_2D_ageBased_all_released():
    """Age-based polygon stats using all_released denominator for connectivity tests"""
    return dict(
        name="my_poly_stats_age_allrel",
        class_name="PolygonStats2D_ageBased",
        update_interval=3600,
        max_age_to_bin=24 * 3600,
        age_bin_size=3600,
        status_list=["moving", "on_bottom", "stranded_by_tide", "stationary"],
        connectivity_denominator='all_released',
    )


@pytest.fixture
def single_pulse_point_release():
    """Single-pulse release for controlled property tests"""
    return dict(
        name="single_pulse",
        class_name="PointRelease",
        release_interval=0,
        pulse_size=10,
    )


# ---------------------------------------------------------------------------
# Performance tracking
# ---------------------------------------------------------------------------

_PERF_RESULTS_DIR = Path(__file__).parent.parent / "performance_results"


@pytest.fixture
def record_performance(request):
    """Return a callable that persists timing from a case_info_file.

    Usage inside a performance test::

        def test_something(..., record_performance):
            case_info_file = ot.run()
            record_performance(case_info_file)
            assert case_info_file is not None

    The callable reads the OceanTracker JSON output, appends a compact record
    to ``tests/performance_results/history.json``, then regenerates all
    summary figures in ``tests/performance_results/figures/``.
    """
    _PERF_RESULTS_DIR.mkdir(exist_ok=True)
    (_PERF_RESULTS_DIR / "figures").mkdir(exist_ok=True)

    def _record(case_info_file):
        if case_info_file is None:
            return
        try:
            info = json.loads(Path(case_info_file).read_text())
        except Exception as e:
            print(f"record_performance: could not read case_info_file: {e}")
            return

        run_info     = info.get("run_info", {})
        computer     = info.get("computer_info", {})
        version_info = info.get("version_info", {})
        performance  = info.get("performance", {})

        n_particles  = run_info.get("number_particles_released")
        elapsed      = run_info.get("elapsed_time_sec")
        n_timesteps  = run_info.get("time_steps_completed")

        particles_per_sec = (
            n_particles / elapsed if n_particles and elapsed else None
        )
        time_per_particle_per_timestep = (
            elapsed / (n_particles * n_timesteps)
            if n_particles and elapsed and n_timesteps else None
        )

        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "version":   version_info.get("oceantracker_version", "unknown"),
            "git_hash":  (info.get("git_commit_hash") or "unknown")[:8],
            "test_name": request.node.nodeid,
            "machine": {
                "name":         computer.get("name", "unknown"),
                "processor":    computer.get("processor", "unknown"),
                "cpus_physical": computer.get("CPUs_hardware"),
                "cpus_logical":  computer.get("CPUs_logical"),
                "freq_mhz":     computer.get("Freq_Mhz"),
                "memory_gb":    computer.get("memory_GB"),
            },
            "particle_count":   n_particles,
            "n_timesteps":      n_timesteps,
            "elapsed_sec":      elapsed,
            "particles_per_sec": particles_per_sec,
            "time_per_particle_per_timestep": time_per_particle_per_timestep,
            "memory_gb":    performance.get("max_memory_usedGB"),
            "block_timings": performance.get("block_timings", []),
        }

        history_file = _PERF_RESULTS_DIR / "history.json"
        history = json.loads(history_file.read_text()) if history_file.exists() else []
        history.append(record)
        history_file.write_text(json.dumps(history, indent=2))

        # Regenerate all summary figures
        import subprocess, sys
        plot_script = _PERF_RESULTS_DIR / "plot_history.py"
        if plot_script.exists():
            subprocess.run([sys.executable, str(plot_script)], check=False)

    return _record
