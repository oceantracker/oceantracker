import pytest
from oceantracker.main import OceanTracker

# Shared settings for all performance tests
_PERF_SETTINGS = {"time_step": 30, "use_dispersion": True}
_FIXED_PARTICLES = 1_000_000  # shared across non-scaling tests


# ---------------------------------------------------------------------------
# Default benchmark — run with: pytest -n0 -m performance
# ---------------------------------------------------------------------------

@pytest.mark.performance_basic
def test_run_3D_model_performance(
    base_settings,
    reader_schism3D,
    schism3D_release_locations,
    record_performance,
):
    """Standard single-point benchmark (RK4, 1M particles, 1 processor).

    This is also the processors=1 baseline for the parallelization chart
    and the RK4 baseline for the RK-order chart.
    """
    ot = OceanTracker()
    ot.settings(**{**(base_settings | _PERF_SETTINGS)}, processors=1)
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        name="default_perf",
        class_name="PointRelease",
        points=schism3D_release_locations["deep_point"],
        release_interval=0,
        pulse_size=_FIXED_PARTICLES,
    )
    case_info_file = ot.run()
    record_performance(case_info_file)
    assert case_info_file is not None


# ---------------------------------------------------------------------------
# Extended benchmarks — run with: pytest -n0 -m extended
# ---------------------------------------------------------------------------

@pytest.mark.performance_extended
@pytest.mark.parametrize("particle_count", [100_000, 10_000_000])
def test_run_3D_model_scaling(
    base_settings,
    reader_schism3D,
    schism3D_release_locations,
    particle_count,
    record_performance,
):
    """Throughput vs particle count (RK4, 1 processor).

    1M particle case is omitted — covered by test_run_3D_model_performance.
    """
    ot = OceanTracker()
    ot.settings(**{**(base_settings | _PERF_SETTINGS)}, processors=1)
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        name=f"scaling_test_{particle_count}",
        class_name="PointRelease",
        points=schism3D_release_locations["deep_point"],
        release_interval=0,
        pulse_size=particle_count,
    )
    case_info_file = ot.run()
    record_performance(case_info_file)
    assert case_info_file is not None


@pytest.mark.performance_extended
@pytest.mark.parametrize("RK_order", [1, 2])
def test_scaling_with_RK_order(
    base_settings,
    reader_schism3D,
    schism3D_release_locations,
    RK_order,
    record_performance,
):
    """Wall time vs RK integration order.

    RK4 baseline is sourced from test_run_3D_model_performance.
    """
    ot = OceanTracker()
    ot.settings(**{**(base_settings | _PERF_SETTINGS)}, processors=1)
    ot.add_class("solver", RK_order=RK_order)
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        class_name="PointRelease",
        points=schism3D_release_locations["deep_point"],
        release_interval=0,
        pulse_size=_FIXED_PARTICLES,
    )
    case_info_file = ot.run()
    record_performance(case_info_file)
    assert case_info_file is not None


@pytest.mark.performance_extended
@pytest.mark.parametrize("processors", [4, 16])
def test_parallelization_scaling(
    base_settings,
    reader_schism3D,
    schism3D_release_locations,
    processors,
    record_performance,
):
    """Wall time vs processor count (RK4, 1M particles).

    processors=1 baseline is sourced from test_run_3D_model_performance.
    """
    ot = OceanTracker()
    ot.settings(**{**(base_settings | _PERF_SETTINGS)}, processors=processors)
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        class_name="PointRelease",
        points=schism3D_release_locations["deep_point"],
        release_interval=0,
        pulse_size=_FIXED_PARTICLES,
    )
    case_info_file = ot.run()
    record_performance(case_info_file)
    assert case_info_file is not None
