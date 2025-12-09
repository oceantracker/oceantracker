import pytest
from oceantracker.main import OceanTracker


@pytest.mark.skip(reason='performance')
def test_run_3D_model_performance(
    base_settings,
    reader_demo_schism3D,
    schism3D_release_locations,
):
    """
    Performance test for SCHISM 3D native grid tracking.
    
    This test uses:
    - Small time step (30s vs default 120s) for more computation
    - Large particle release (1000 particles vs typical 5)
    - Frequent releases (300s vs 1800s) for sustained particle count
    
    Run only when explicitly requested:
        pytest -m performance tests/unit_tests/test_performance.py
    
    For profiling with Arm Forge on HPC via SLURM, use the companion 
    slurm script: run_performance_test_forge.sl
    """
    
    # Performance-oriented settings
    ot = OceanTracker()
    ot.settings(
        **{**(base_settings | {
            "time_step": 30,
            "use_dispersion": True
            })},
        processors=32
        ),  # Smaller timestep = more iterations
    
    ot.add_class("reader", **reader_demo_schism3D)
    
    # Large particle release for performance testing
    ot.add_class(
        "release_groups",
        name="performance_test",
        class_name="PointRelease",
        points=schism3D_release_locations["deep_point"],
        release_interval=0,  # Release all at model start
        pulse_size=1_000_000,  # Large number of particles
    )
    
    case_info_file = ot.run()
    
    assert case_info_file is not None


@pytest.mark.skip(reason='performance')
@pytest.mark.parametrize("RK_order", [1,2,4])
def test_scaling_with_RK_order(
    base_settings,
    reader_schism3D,
    schism3D_release_locations,
    RK_order,
):
    """
    Scaling test to measure performance with varying particle counts.
    
    Run with:
        pytest -m performance tests/unit_tests/test_performance.py::test_scaling_with_RK_order
    """
    ot = OceanTracker()
    ot.settings(
        **base_settings,
        processors=1
    )
    ot.add_class("solver", RK_order=RK_order)
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        class_name="PointRelease",
        points=schism3D_release_locations["deep_point"],
        release_interval=0,
        pulse_size=100_000_000,
    )
    case_info_file = ot.run()
    
    assert case_info_file is not None

@pytest.mark.skip(reason='performance')
@pytest.mark.parametrize("particle_count", [100_000, 1_000_000,10_000_000,100_000_000])
def test_run_3D_model_scaling(
    base_settings,
    reader_schism3D,
    schism3D_release_locations,
    particle_count,
):
    """
    Scaling test to measure performance with varying particle counts.
    
    Run with:
        pytest -m performance tests/unit_tests/test_performance.py::test_run_3D_model_scaling
    """
    ot = OceanTracker()
    ot.settings(
        **base_settings,
    )
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
    
    assert case_info_file is not None