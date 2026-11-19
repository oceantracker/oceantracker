"""
Tests for connectivity statistics — age-based and time-based.

Age-based:
  count_all_released_age_bins mirrors count_all_alive_particles: both accumulate
  the instantaneous demographic (particles currently in each age bin) across all
  update steps. count_all_released uses release-group pulse history so dead
  particles are included; count_all_alive uses the live particle buffer.
  count_unique_released_age_bins / count_unique_alive_age_bins count each particle at
  most once per age bin; they are the connectivity denominators when
  max_count_per_particle is set, as count then counts each particle a limited number of times.

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


# ---------------------------------------------------------------------------
# max_count_per_particle with age-based stats: denominators must count each
# particle at most once per age bin (count_unique_*_age_bins) 
# ---------------------------------------------------------------------------
from oceantracker.particle_statistics._base_stats_variants import _BaseAgeStats


def _brute_force_unique_entries(entry_times, weights, update_times, age_bin_edges):
    """Reference: each entry adds its weight once to every age bin it is seen in at an update."""
    n_bins = age_bin_edges.size - 1
    da = age_bin_edges[1] - age_bin_edges[0]
    expected = np.zeros((n_bins,), np.int64)
    for t0, w in zip(entry_times, weights):
        bins_seen = set()
        for t in update_times:
            na = int(np.floor((t - t0 - age_bin_edges[0]) / da))
            if 0 <= na < n_bins:
                bins_seen.add(na)
        for na in bins_seen:
            expected[na] += w
    return expected


_kernel_cases = dict(
    # name: (direction, age_bin_size, min_age, max_age, update_interval)
    forward=(1, 4 * 3600., 0., 12 * 3600., 3600.),
    backtracking=(-1, 4 * 3600., 0., 12 * 3600., 3600.),
    bins_seen_once_or_twice=(1, 5400., 0., 6 * 5400., 3600.),
    min_age_gt_0=(1, 3 * 3600., 3 * 3600., 12 * 3600., 3600.),
    bin_smaller_than_update=(1, 1800., 0., 12 * 3600., 3600.),
)


@pytest.mark.parametrize("case", list(_kernel_cases.keys()))
def test_unique_age_bin_entry_kernels(case):
    """The released-pulse and alive-particle unique kernels count each pulse/particle
    exactly once in every age bin it is observed in at an update, for forward and
    backtracking runs, irregular bin/update ratios, min_age_to_bin > 0, pulses released
    between updates and zero-filled (not yet released) pulse slots."""
    direction, dage, min_age, max_age, dt_update = _kernel_cases[case]
    T0 = 1.48e9
    edges = direction * np.arange(min_age, max_age + dage, dage)
    n_bins = edges.size - 1
    update_times = T0 + direction * dt_update * np.arange(0, 25)
    rel_offsets = np.asarray([0., 1800., 5400., 7200., 9000., 30000.])

    # --- pulses: last two slots mimic pre-allocated, not yet released pulses (time 0, count 0)
    pulse_times = np.concatenate((T0 + direction * rel_offsets, [0., 0.]))
    pulse_counts = np.asarray([5, 7, 11, 13, 17, 19, 0, 0], dtype=np.int32)
    count_unique = np.zeros((n_bins, 1), np.int64)
    prev = None
    for t in update_times:
        released = pulse_counts.copy()
        released[:rel_offsets.size][direction * (pulse_times[:rel_offsets.size] - t) > 0] = 0  # not yet released
        times = pulse_times.copy()
        _BaseAgeStats._accumulate_unique_pulse_entries(times, released, t,
                                                       prev if prev is not None else 0., prev is not None,
                                                       edges, count_unique, 0)
        prev = t
    expected = _brute_force_unique_entries(pulse_times[:rel_offsets.size], pulse_counts[:rel_offsets.size],
                                           update_times, edges)
    assert np.array_equal(count_unique[:, 0], expected), (count_unique[:, 0], expected)

    # --- alive particles, one particle per release time, two release groups
    time_released = np.repeat(T0 + direction * rel_offsets, 2)
    release_group = np.tile(np.asarray([0, 1], np.int32), rel_offsets.size)
    status = np.full(time_released.shape, 1, np.int32)  # moving
    count_all = np.zeros((n_bins, 2), np.int64)
    count_unique_alive = np.zeros((n_bins, 2), np.int64)
    prev = None
    for t in update_times:
        age = t - time_released
        alive = np.flatnonzero(direction * age >= 0).astype(np.int32)
        _BaseAgeStats._count_all_alive_age_bins(status, release_group, age, time_released, edges,
                                                count_all, count_unique_alive, alive,
                                                prev if prev is not None else 0., prev is not None)
        prev = t
    expected = _brute_force_unique_entries(T0 + direction * rel_offsets, np.ones(rel_offsets.size, np.int64),
                                           update_times, edges)
    for rg in range(2):
        assert np.array_equal(count_unique_alive[:, rg], expected), (count_unique_alive[:, rg], expected)
    # with one update per bin the per-update counts equal the unique counts, otherwise they are larger
    assert np.all(count_all >= count_unique_alive)


def _max_count_stats_params(updates_per_bin=3):
    common = dict(update_interval=3600, age_bin_size=updates_per_bin * 3600, max_age_to_bin=12 * 3600,
                  max_count_per_particle=1, kill_when_max_counted=False,
                  status_list=["moving", "on_bottom", "stranded_by_tide", "stationary"])
    return common


@pytest.mark.parametrize("backtracking", [False, True])
def test_max_count_age_based_denominators_not_inflated(
    base_settings, reader_demo_schism3D, single_pulse_point_release, schism3D_release_locations,
    backtracking,
):
    """Regression for "more particles counted than released" with max_count_per_particle=1.

    Single pulse of N particles, 3 updates per age bin. The release point is outside the
    polygon, so particles are counted in a later age bin. Every particle must be counted in
    the unique denominators exactly once per age bin, and connectivity must sum to the
    fraction of particles counted (was 1/3 of that with the per-update denominators).
    """
    N = single_pulse_point_release["pulse_size"]
    release_point = schism3D_release_locations["deep_point"]
    common = _max_count_stats_params(3)

    ot = OceanTracker()
    ot.settings(**base_settings, backtracking=backtracking)
    ot.add_class("reader", **reader_demo_schism3D)
    ot.add_class("release_groups", **{**single_pulse_point_release, "points": release_point})
    stats_cfg = dict(
        poly_released=dict(class_name="PolygonStats2D_ageBased", polygon_list=schism3D_release_locations["polygons"],
                           connectivity_denominator="all_released"),
        poly_alive=dict(class_name="PolygonStats2D_ageBased", polygon_list=schism3D_release_locations["polygons"],
                        connectivity_denominator="all_alive"),
        # grid around release point always contains particles, so start binning at 3 h to count in a later bin
        grid_released=dict(class_name="GriddedStats2D_ageBased", grid_center=release_point[:2], rows=5, cols=5,
                           span_x=20000, span_y=20000, min_age_to_bin=3 * 3600, connectivity_denominator="all_released"),
        grid_alive=dict(class_name="GriddedStats2D_ageBased", grid_center=release_point[:2], rows=5, cols=5,
                        span_x=20000, span_y=20000, min_age_to_bin=3 * 3600, connectivity_denominator="all_alive"),
    )
    for name, cfg in stats_cfg.items():
        ot.add_class("particle_statistics", name=name, **common, **cfg)
    case_info_file = ot.run()
    assert case_info_file is not None

    for name, cfg in stats_cfg.items():
        stats = load_output_files.load_stats_data(case_info_file, name=name)
        count = stats["count"]  # (age, release group, polygon or row, col)
        n_bins = count.shape[0]
        unique_rel = stats["count_unique_released_age_bins"]
        unique_alive = stats["count_unique_alive_age_bins"]

        assert stats["number_released_each_release_group"][0] == N, name
        assert 0 < count.sum() <= N, f"{name}: each particle counted at most once, count.sum()={count.sum()}"

        # hindcast is 23 h > max_age_to_bin, so every bin is reached by the single pulse
        assert np.all(unique_rel[:, 0] == N), f"{name}: count_unique_released_age_bins={unique_rel[:, 0]}"
        # nothing dies in this hindcast/config, so all particles are alive in every bin
        assert np.all(unique_alive[:, 0] == N), f"{name}: count_unique_alive_age_bins={unique_alive[:, 0]}"

        # per-update (particle-update) variables keep their meaning: 3 updates per bin
        assert np.all(stats["count_all_released_age_bins"][:, 0] == 3 * N), name
        assert np.all(stats["count_all_alive_particles"][:, 0] == 3 * N), name

        expected_denom = ("count_unique_released_age_bins" if cfg["connectivity_denominator"] == "all_released"
                          else "count_unique_alive_age_bins")
        assert stats["global_attributes"]["connectivity_denominator_variable"] == expected_denom, name

        cm = stats["connectivity_matrix"]
        assert np.nanmax(cm) <= 1.0, name
        assert np.nansum(cm) == pytest.approx(count.sum() / N, rel=1e-6), (
            f"{name}: connectivity sums to {np.nansum(cm)}, expected fraction counted {count.sum() / N}")
        assert n_bins == (3 if "grid" in name else 4), name


def test_max_count_age_based_invariants_with_kill(
    base_settings, reader_demo_schism3D, basic_point_release, schism3D_release_locations,
):
    """Continuous release, max_count_per_particle=1 and kill_when_max_counted=True:
    counted particles die, so the alive denominator drops below the released one,
    and all connectivity values must be fractions of unique particles."""
    common = {**_max_count_stats_params(3), "kill_when_max_counted": True}

    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_demo_schism3D)
    ot.add_class("release_groups", **{**basic_point_release, "points": schism3D_release_locations["deep_point"]})
    # only one stats instance, as particles killed by one instance can not be counted by another
    ot.add_class("particle_statistics", name="kill_alive", class_name="PolygonStats2D_ageBased",
                 polygon_list=schism3D_release_locations["polygons"], connectivity_denominator="all_alive", **common)
    case_info_file = ot.run()
    assert case_info_file is not None

    for name in ["kill_alive"]:
        stats = load_output_files.load_stats_data(case_info_file, name=name)
        count = stats["count"]
        num_released = stats["number_released_each_release_group"]
        unique_rel = stats["count_unique_released_age_bins"]
        unique_alive = stats["count_unique_alive_age_bins"]

        assert count.sum() > 0, name
        assert np.all(count.sum(axis=(0, 2)) <= num_released), name
        # bins are 3 updates wide, so every pulse is seen in the first age bin
        assert np.all(unique_rel[0, :] == num_released), (name, unique_rel[0, :], num_released)
        assert np.all(unique_rel <= num_released[np.newaxis, :]), name
        # fewer pulses reach older bins before the run ends
        assert np.all(np.diff(unique_rel[:, 0]) <= 0), (name, unique_rel[:, 0])
        assert np.all(count.sum(axis=2) <= unique_alive), name
        assert np.all(unique_alive <= unique_rel), name
        assert np.any(unique_alive < unique_rel), f"{name}: killed particles should be missing from alive counts"
        cm = stats["connectivity_matrix"]
        assert np.nanmin(cm) >= 0. and np.nanmax(cm) <= 1.0, name
        with np.errstate(divide='ignore', invalid='ignore'):
            expected_cm = count / unique_alive[:, :, np.newaxis]
        assert np.allclose(cm, expected_cm, rtol=1e-6, equal_nan=True), f"{name}: connectivity is not count/count_unique_alive_age_bins"
