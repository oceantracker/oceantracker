"""
Tests for connectivity statistics — age-based and time-based.

Age-based:
  count_all_released_age_bins mirrors count_all_alive_particles: both accumulate
  the instantaneous demographic (particles currently in each age bin) across all
  update steps. count_all_released uses release-group pulse history so dead
  particles are included; count_all_alive uses the live particle buffer.

Time-based:
  Each written timestep is a snapshot. count_all_alive_particles is reset at each
  update; num_released is cumulative. Mathematical invariants:
    count ≤ count_all_alive_particles ≤ num_released (so connectivity_matrix ∈ [0,1])
    num_released is monotonically non-decreasing over time.
"""
import numpy as np
import pytest
from os import path, makedirs
from oceantracker.main import OceanTracker
from oceantracker.read_output.python import load_output_files


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def _run_age_polygon_stats(base_settings, reader, release_group, polygon_list,
                            stats_params):
    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader)
    ot.add_class("release_groups", **release_group)
    ot.add_class("particle_statistics",
                 **{**stats_params, "polygon_list": polygon_list})
    return ot.run()


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------

def test_demographic_geq_alive_count(
    base_settings, reader_demo_schism3D, basic_point_release,
    schism3D_release_locations, polygon_stats_2D_ageBased_all_released,
):
    """count_all_released_age_bins >= count_all_alive_particles for every bin/group.

    Both arrays accumulate the instantaneous demographic across update steps.
    Released includes dead particles; alive is a strict subset — so released
    must be >= alive at every element.
    """
    case_info_file = _run_age_polygon_stats(
        base_settings, reader_demo_schism3D,
        {**basic_point_release, "points": schism3D_release_locations["deep_point"]},
        schism3D_release_locations["polygons"],
        polygon_stats_2D_ageBased_all_released,
    )
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(
        case_info_file, name=polygon_stats_2D_ageBased_all_released["name"])
    demo = stats["count_all_released_age_bins"]   # (n_age_bins, n_groups)
    alive = stats["count_all_alive_particles"]    # (n_age_bins, n_groups)

    assert np.all(demo >= alive), (
        "count_all_released_age_bins < count_all_alive_particles in some bins — "
        "alive particles cannot exceed the released demographic"
    )


def test_connectivity_matrix_in_unit_interval(
    base_settings, reader_demo_schism3D, basic_point_release,
    schism3D_release_locations, polygon_stats_2D_ageBased_all_released,
):
    """With all_released denominator, connectivity_matrix values must be in [0, 1].

    counts_inside_age_bins (numerator) and count_all_released_age_bins (denominator)
    are both accumulated the same way. Particles inside a polygon are a subset of
    all released, so the ratio is bounded by 1.
    """
    case_info_file = _run_age_polygon_stats(
        base_settings, reader_demo_schism3D,
        {**basic_point_release, "points": schism3D_release_locations["deep_point"]},
        schism3D_release_locations["polygons"],
        polygon_stats_2D_ageBased_all_released,
    )
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(
        case_info_file, name=polygon_stats_2D_ageBased_all_released["name"])
    cm = stats["connectivity_matrix"]
    finite = cm[np.isfinite(cm)]

    assert np.all(finite >= 0.0), "connectivity_matrix has negative finite values"
    assert np.all(finite <= 1.0), (
        f"connectivity_matrix exceeds 1.0 (max={finite.max():.6f}) — "
        "counts inside bins exceed the released demographic"
    )


def test_demographic_monotonically_non_increasing_single_pulse(
    base_settings, reader_demo_schism3D, single_pulse_point_release,
    schism3D_release_locations, polygon_stats_2D_ageBased_all_released,
):
    """With a single pulse, count_all_released_age_bins is non-increasing along age bins.

    A single pulse ages through bins sequentially. Each update step adds pulse_size
    to whichever bin the pulse is currently in. Fully vacated bins retain their
    accumulated total; the currently-occupied bin accumulates fewer steps (it hasn't
    finished yet); unvisited bins have zero. So the profile is [N, N, ..., M, 0, 0]
    with M <= N — monotonically non-increasing.
    """
    case_info_file = _run_age_polygon_stats(
        base_settings, reader_demo_schism3D,
        {**single_pulse_point_release,
         "points": schism3D_release_locations["deep_point"]},
        schism3D_release_locations["polygons"],
        polygon_stats_2D_ageBased_all_released,
    )
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(
        case_info_file, name=polygon_stats_2D_ageBased_all_released["name"])
    demo = stats["count_all_released_age_bins"]  # (n_age_bins, n_groups)

    for nrg in range(demo.shape[1]):
        diff = np.diff(demo[:, nrg])  # demo[na+1] - demo[na], must be <= 0
        assert np.all(diff <= 0), (
            f"Release group {nrg}: count_all_released_age_bins not monotonically "
            f"non-increasing. First violation at bin {np.argmax(diff > 0)}: "
            f"{demo[np.argmax(diff > 0), nrg]} -> {demo[np.argmax(diff > 0)+1, nrg]}"
        )


def test_single_pulse_demographic_multiple_of_pulse_size(
    base_settings, reader_demo_schism3D, single_pulse_point_release,
    schism3D_release_locations, polygon_stats_2D_ageBased_all_released,
):
    """Core correctness: single pulse → every non-zero bin count is a multiple of pulse_size.

    At each update step, exactly pulse_size particles are placed into the pulse's
    current age bin. Accumulating over many steps, each bin's count is
    pulse_size × (steps spent in that bin). Dead particles are included because
    the count comes from pulse history, not the particle buffer — this is the
    key property the rework is designed to guarantee.
    """
    pulse_size = single_pulse_point_release["pulse_size"]

    case_info_file = _run_age_polygon_stats(
        base_settings, reader_demo_schism3D,
        {**single_pulse_point_release,
         "points": schism3D_release_locations["deep_point"]},
        schism3D_release_locations["polygons"],
        polygon_stats_2D_ageBased_all_released,
    )
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(
        case_info_file, name=polygon_stats_2D_ageBased_all_released["name"])
    demo = stats["count_all_released_age_bins"]  # (n_age_bins, n_groups)
    age_bin_edges = stats["age_bin_edges"]

    non_zero = demo[:, 0][demo[:, 0] > 0]
    assert non_zero.size > 0, "No non-zero bins — demographic produced no output"

    remainders = non_zero % pulse_size
    assert np.all(remainders == 0), (
        f"Non-zero bin counts are not all multiples of pulse_size={pulse_size}. "
        f"Counts: {non_zero}, remainders: {remainders}. "
        f"Age bin edges: {age_bin_edges}. "
        "Suggests demographic is reading from particle buffer rather than pulse history."
    )


# ---------------------------------------------------------------------------
# Time-based property tests
# ---------------------------------------------------------------------------

def _run_time_polygon_stats(base_settings, reader, release_group, polygon_list,
                             stats_params):
    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader)
    ot.add_class("release_groups", **release_group)
    ot.add_class("particle_statistics",
                 **{**stats_params, "polygon_list": polygon_list})
    return ot.run()


def test_time_count_leq_alive(
    base_settings, reader_demo_schism3D, basic_point_release,
    schism3D_release_locations, polygon_stats_2D_timeBased_all_released,
):
    """count[t, nrg, ...] ≤ count_all_alive_particles[t, nrg] at every timestep.

    Polygon counts use a filtered sel (status_list + spatial location).
    count_all_alive_particles counts the full alive buffer.
    Polygon count is a strict subset so it can never exceed alive count.
    """
    case_info_file = _run_time_polygon_stats(
        base_settings, reader_demo_schism3D,
        {**basic_point_release, "points": schism3D_release_locations["deep_point"]},
        schism3D_release_locations["polygons"],
        polygon_stats_2D_timeBased_all_released,
    )
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(
        case_info_file, name=polygon_stats_2D_timeBased_all_released["name"])
    count = stats["count"]                         # (time, release_group, polygon)
    alive = stats["count_all_alive_particles"]     # (time, release_group)

    # sum polygon axis so shapes align: count.sum(axis=-1) → (time, release_group)
    count_per_rg = count.sum(axis=-1)
    assert np.all(count_per_rg <= alive), (
        "count (summed over polygons) exceeds count_all_alive_particles at some timestep — "
        "polygon count cannot exceed total alive"
    )


def test_time_alive_leq_released(
    base_settings, reader_demo_schism3D, basic_point_release,
    schism3D_release_locations, polygon_stats_2D_timeBased_all_released,
):
    """count_all_alive_particles[t, nrg] ≤ num_released[t, nrg] at every timestep.

    Alive particles are a subset of all ever-released particles.
    """
    case_info_file = _run_time_polygon_stats(
        base_settings, reader_demo_schism3D,
        {**basic_point_release, "points": schism3D_release_locations["deep_point"]},
        schism3D_release_locations["polygons"],
        polygon_stats_2D_timeBased_all_released,
    )
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(
        case_info_file, name=polygon_stats_2D_timeBased_all_released["name"])
    alive = stats["count_all_alive_particles"]   # (time, release_group)
    num_released = stats["num_released"]         # (time, release_group)

    assert np.all(alive <= num_released), (
        "count_all_alive_particles exceeds num_released at some timestep — "
        "alive can never exceed ever-released"
    )


def test_time_connectivity_matrix_in_unit_interval(
    base_settings, reader_demo_schism3D, basic_point_release,
    schism3D_release_locations, polygon_stats_2D_timeBased_all_released,
):
    """With all_released denominator, connectivity_matrix values must be in [0, 1].

    count ≤ num_released at every timestep, so count / num_released ∈ [0, 1].
    """
    case_info_file = _run_time_polygon_stats(
        base_settings, reader_demo_schism3D,
        {**basic_point_release, "points": schism3D_release_locations["deep_point"]},
        schism3D_release_locations["polygons"],
        polygon_stats_2D_timeBased_all_released,
    )
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(
        case_info_file, name=polygon_stats_2D_timeBased_all_released["name"])
    cm = stats["connectivity_matrix"]
    finite = cm[np.isfinite(cm)]

    assert np.all(finite >= 0.0), "time-based connectivity_matrix has negative finite values"
    assert np.all(finite <= 1.0), (
        f"time-based connectivity_matrix exceeds 1.0 (max={finite.max():.6f}) — "
        "polygon count exceeds num_released"
    )


def test_time_num_released_monotone(
    base_settings, reader_demo_schism3D, basic_point_release,
    schism3D_release_locations, polygon_stats_2D_timeBased_all_released,
):
    """num_released[t, nrg] is monotonically non-decreasing over time.

    Releases are irreversible; the cumulative count can only grow.
    """
    case_info_file = _run_time_polygon_stats(
        base_settings, reader_demo_schism3D,
        {**basic_point_release, "points": schism3D_release_locations["deep_point"]},
        schism3D_release_locations["polygons"],
        polygon_stats_2D_timeBased_all_released,
    )
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(
        case_info_file, name=polygon_stats_2D_timeBased_all_released["name"])
    num_released = stats["num_released"]   # (time, release_group)

    for nrg in range(num_released.shape[1]):
        diff = np.diff(num_released[:, nrg])
        assert np.all(diff >= 0), (
            f"Release group {nrg}: num_released decreased at timestep "
            f"{np.argmax(diff < 0)}"
        )


# ---------------------------------------------------------------------------
# Regression test (time-based)
# ---------------------------------------------------------------------------

def _compare_time_connectivity_stats_with_reference(
    case_info_file, reference_data_dir, test_name, stats_name, create_reference=False
):
    """Save or compare count, count_all_alive_particles, num_released."""
    stats = load_output_files.load_stats_data(case_info_file, name=stats_name)
    reference_file = path.join(reference_data_dir, f"{test_name}_stats.npz")

    if create_reference:
        makedirs(reference_data_dir, exist_ok=True)
        np.savez(
            reference_file,
            count=stats["count"],
            count_all_alive_particles=stats["count_all_alive_particles"],
            num_released=stats["num_released"],
        )
        print(f"Created time-based connectivity reference data: {reference_file}")
        return None

    if not path.exists(reference_file):
        raise FileNotFoundError(
            f"Reference file not found: {reference_file}\n"
            f"Run with --create-reference to create it."
        )

    ref = np.load(reference_file)
    results = {}
    for key in ("count", "count_all_alive_particles", "num_released"):
        diff = int(np.max(np.abs(stats[key].astype(np.int64) - ref[key].astype(np.int64))))
        results[f"{key}_max_diff"] = diff
        print(f"  {key}: ref_sum={ref[key].sum()}, new_sum={stats[key].sum()}, max_diff={diff}")
    return results


@pytest.mark.validation
def test_connectivity_time_stats_regression(
    base_settings, reader_demo_schism3D, basic_point_release,
    schism3D_release_locations, polygon_stats_2D_timeBased_all_released,
    reference_data_dir, create_reference_data_flag,
    request,
):
    """Regression test: time-based polygon connectivity against pre-calculated reference.

    Checks count, count_all_alive_particles, and num_released are bit-exact vs saved reference.

    Create/update reference:
        pytest --create-reference -m validation tests/unit_tests/test_connectivity.py::test_connectivity_time_stats_regression

    Normal run:
        pytest -m validation tests/unit_tests/test_connectivity.py
    """
    test_name = request.node.name

    case_info_file = _run_time_polygon_stats(
        base_settings, reader_demo_schism3D,
        {**basic_point_release, "points": schism3D_release_locations["deep_point"]},
        schism3D_release_locations["polygons"],
        polygon_stats_2D_timeBased_all_released,
    )
    assert case_info_file is not None

    stats_name = polygon_stats_2D_timeBased_all_released["name"]

    if create_reference_data_flag:
        _compare_time_connectivity_stats_with_reference(
            case_info_file, reference_data_dir, test_name,
            stats_name, create_reference=True,
        )
    else:
        results = _compare_time_connectivity_stats_with_reference(
            case_info_file, reference_data_dir, test_name,
            stats_name, create_reference=False,
        )
        for key, diff in results.items():
            assert diff == 0, (
                f"{key}: max absolute difference = {diff} (expected 0). "
                "Integer count arrays must match the reference exactly."
            )


# ---------------------------------------------------------------------------
# Age-based regression test
# ---------------------------------------------------------------------------

def _compare_connectivity_stats_with_reference(
    case_info_file, reference_data_dir, test_name, stats_name, create_reference=False
):
    """Save or compare count_all_released_age_bins, count_all_alive_particles, count."""
    stats = load_output_files.load_stats_data(case_info_file, name=stats_name)
    reference_file = path.join(reference_data_dir, f"{test_name}_stats.npz")

    if create_reference:
        makedirs(reference_data_dir, exist_ok=True)
        np.savez(
            reference_file,
            count=stats["count"],
            count_all_alive_particles=stats["count_all_alive_particles"],
            count_all_released_age_bins=stats["count_all_released_age_bins"],
        )
        print(f"Created connectivity reference data: {reference_file}")
        return None

    if not path.exists(reference_file):
        raise FileNotFoundError(
            f"Reference file not found: {reference_file}\n"
            f"Run with --create-reference to create it."
        )

    ref = np.load(reference_file)
    results = {}
    for key in ("count", "count_all_alive_particles", "count_all_released_age_bins"):
        diff = int(np.max(np.abs(stats[key].astype(np.int64) - ref[key].astype(np.int64))))
        results[f"{key}_max_diff"] = diff
        print(f"  {key}: ref_sum={ref[key].sum()}, new_sum={stats[key].sum()}, max_diff={diff}")
    return results


@pytest.mark.validation
def test_connectivity_stats_regression(
    base_settings, reader_demo_schism3D, basic_point_release,
    schism3D_release_locations, polygon_stats_2D_ageBased_all_released,
    reference_data_dir, create_reference_data_flag,
    request,
):
    """Regression test: age-based polygon connectivity against pre-calculated reference.

    Checks count, count_all_alive_particles, and count_all_released_age_bins
    are bit-exact vs saved reference.

    Create/update reference:
        pytest --create-reference -m validation tests/unit_tests/test_connectivity.py

    Normal run:
        pytest -m validation tests/unit_tests/test_connectivity.py
    """
    test_name = request.node.name

    case_info_file = _run_age_polygon_stats(
        base_settings, reader_demo_schism3D,
        {**basic_point_release, "points": schism3D_release_locations["deep_point"]},
        schism3D_release_locations["polygons"],
        polygon_stats_2D_ageBased_all_released,
    )
    assert case_info_file is not None

    stats_name = polygon_stats_2D_ageBased_all_released["name"]

    if create_reference_data_flag:
        _compare_connectivity_stats_with_reference(
            case_info_file, reference_data_dir, test_name,
            stats_name, create_reference=True,
        )
    else:
        results = _compare_connectivity_stats_with_reference(
            case_info_file, reference_data_dir, test_name,
            stats_name, create_reference=False,
        )
        for key, diff in results.items():
            assert diff == 0, (
                f"{key}: max absolute difference = {diff} (expected 0). "
                "Integer count arrays must match the reference exactly."
            )
