#!/usr/bin/env python3
"""
Plot OceanTracker performance history.

Reads tests/performance_results/history.json and regenerates all summary
figures into tests/performance_results/figures/.  Called automatically
after each performance test run via the record_performance pytest fixture,
but can also be run standalone:

    python tests/performance_results/plot_history.py
"""
import json
import re
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')  # non-interactive backend for headless runs
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np


PERF_DIR = Path(__file__).parent
HISTORY_FILE = PERF_DIR / "history.json"
FIGURES_DIR = PERF_DIR / "figures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_history():
    if not HISTORY_FILE.exists():
        return []
    with open(HISTORY_FILE) as f:
        return json.load(f)


def version_sort_key(v):
    """Numeric sort key for dotted version strings like '0.5.3.5'."""
    try:
        return tuple(int(x) for x in str(v).split('.'))
    except Exception:
        return (0,)


def machine_label(machine):
    name = machine.get("name", "unknown")
    cpus = machine.get("cpus_physical", "?")
    return f"{name} ({cpus} cores)"


def short_test_name(nodeid):
    """'tests/unit_tests/test_performance.py::test_foo[bar]' -> 'test_foo[bar]'"""
    return nodeid.split("::")[-1]


def _color_cycle(n):
    return cm.tab10(np.linspace(0, 1, max(n, 1)))


# ---------------------------------------------------------------------------
# Figure 1 – elapsed time and throughput vs version
# ---------------------------------------------------------------------------

def plot_performance_vs_version(history):
    """Three-panel chart: wall time, throughput, and time/particle/timestep per version."""
    records = [r for r in history if r.get("elapsed_sec") is not None]
    if not records:
        return

    # Group by (short test name, machine label)
    groups = defaultdict(list)
    for r in records:
        key = (short_test_name(r["test_name"]), machine_label(r["machine"]))
        groups[key].append(r)

    fig, (ax_t, ax_p, ax_u) = plt.subplots(3, 1, figsize=(12, 11))
    colors = _color_cycle(len(groups))

    for idx, ((tname, mach), recs) in enumerate(sorted(groups.items())):
        recs  = sorted(recs, key=lambda r: version_sort_key(r["version"]))
        versions = [r["version"] for r in recs]
        elapsed  = [r["elapsed_sec"] for r in recs]
        thru     = [r.get("particles_per_sec") for r in recs]
        unit     = [r.get("time_per_particle_per_timestep") for r in recs]
        label    = f"{tname}  @  {mach}"
        c        = colors[idx]
        ax_t.plot(versions, elapsed, marker='o', label=label, color=c)
        if any(v is not None for v in thru):
            ax_p.plot(versions, thru, marker='o', label=label, color=c)
        if any(v is not None for v in unit):
            ax_u.plot(versions, unit, marker='o', label=label, color=c)

    for ax, ylabel, title in [
        (ax_t, "Wall time (s)",                      "Elapsed time per version"),
        (ax_p, "Particles / second",                 "Throughput per version"),
        (ax_u, "sec / (particle × timestep)",        "Unit cost per version"),
    ]:
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(fontsize=7, loc='best')
        ax.tick_params(axis='x', rotation=30)
        ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "performance_vs_version.png", dpi=150)
    plt.close(fig)
    print(f"  saved performance_vs_version.png")


# ---------------------------------------------------------------------------
# Figure 2 – peak memory vs version
# ---------------------------------------------------------------------------

def plot_memory_vs_version(history):
    """Peak RAM usage per test across versions."""
    records = [r for r in history if r.get("memory_gb") is not None]
    if not records:
        return

    groups = defaultdict(list)
    for r in records:
        key = (short_test_name(r["test_name"]), machine_label(r["machine"]))
        groups[key].append(r)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = _color_cycle(len(groups))

    for idx, ((tname, mach), recs) in enumerate(sorted(groups.items())):
        recs = sorted(recs, key=lambda r: version_sort_key(r["version"]))
        ax.plot(
            [r["version"] for r in recs],
            [r["memory_gb"] for r in recs],
            marker='o', color=colors[idx],
            label=f"{tname}  @  {mach}",
        )

    ax.set_ylabel("Peak memory (GB)")
    ax.set_title("Peak memory usage per version")
    ax.legend(fontsize=7, loc='best')
    ax.tick_params(axis='x', rotation=30)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "memory_vs_version.png", dpi=150)
    plt.close(fig)
    print(f"  saved memory_vs_version.png")


# ---------------------------------------------------------------------------
# Figure 3 – scaling: throughput vs particle count (log/log)
# ---------------------------------------------------------------------------

def plot_scaling(history):
    """Log/log chart of particles/sec vs particle count for scaling tests."""
    records = [
        r for r in history
        if "scaling" in r.get("test_name", "")
        and r.get("particle_count")
        and r.get("particles_per_sec")
    ]
    if not records:
        return

    # Group by (version, machine)
    groups = defaultdict(list)
    for r in records:
        key = (r["version"], machine_label(r["machine"]))
        groups[key].append(r)

    fig, ax = plt.subplots(figsize=(9, 6))
    colors = _color_cycle(len(groups))

    for idx, ((ver, mach), recs) in enumerate(
        sorted(groups.items(), key=lambda x: version_sort_key(x[0][0]))
    ):
        recs = sorted(recs, key=lambda r: r["particle_count"])
        ax.loglog(
            [r["particle_count"] for r in recs],
            [r["particles_per_sec"] for r in recs],
            marker='o', color=colors[idx],
            label=f"v{ver}  @  {mach}",
        )

    ax.set_xlabel("Particle count")
    ax.set_ylabel("Particles / second")
    ax.set_title("Scaling: throughput vs particle count")
    ax.legend(fontsize=8, loc='best')
    ax.grid(True, which='both', alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "scaling.png", dpi=150)
    plt.close(fig)
    print(f"  saved scaling.png")


# ---------------------------------------------------------------------------
# Figure 4 – RK order: elapsed time vs integration order
# ---------------------------------------------------------------------------

def plot_rk_order(history):
    """Wall time vs RK integration order, grouped by (version, machine)."""
    def _rk(test_name):
        m = re.search(r'\[(\d+)\]', test_name)
        return int(m.group(1)) if m else None

    records = [
        r for r in history
        if "RK_order" in r.get("test_name", "")
        and r.get("elapsed_sec") is not None
        and _rk(r["test_name"]) is not None
    ]
    if not records:
        return

    groups = defaultdict(list)
    for r in records:
        key = (r["version"], machine_label(r["machine"]))
        groups[key].append((_rk(r["test_name"]), r["elapsed_sec"]))

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = _color_cycle(len(groups))

    for idx, ((ver, mach), points) in enumerate(
        sorted(groups.items(), key=lambda x: version_sort_key(x[0][0]))
    ):
        points = sorted(points, key=lambda p: p[0])
        ax.plot(
            [p[0] for p in points],
            [p[1] for p in points],
            marker='o', color=colors[idx],
            label=f"v{ver}  @  {mach}",
        )

    ax.set_xlabel("RK order")
    ax.set_ylabel("Elapsed time (s)")
    ax.set_title("Performance vs RK integration order")
    ax.set_xticks([1, 2, 4])
    ax.legend(fontsize=8, loc='best')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "rk_order.png", dpi=150)
    plt.close(fig)
    print(f"  saved rk_order.png")


# ---------------------------------------------------------------------------
# Figure 5 – parallelization: elapsed time and speedup vs processor count
# ---------------------------------------------------------------------------

def plot_parallelization(history):
    """Elapsed time and parallel speedup vs processor count.

    The processors=1 baseline is borrowed from test_run_3D_model_scaling[1000000],
    which shares the same config (RK4, 1M particles).
    """
    records = [
        r for r in history
        if "parallelization" in r.get("test_name", "")
        and r.get("elapsed_sec") is not None
    ]
    if not records:
        return

    def get_processors(test_name):
        m = re.search(r'\[(\d+)\]', test_name)
        return int(m.group(1)) if m else None

    # Build a lookup of serial baselines: (version, machine_label) -> elapsed_sec
    # sourced from the default benchmark (processors=1, RK4, 1M particles)
    serial_baseline = {
        (r["version"], machine_label(r["machine"])): r["elapsed_sec"]
        for r in history
        if "test_run_3D_model_performance" in r.get("test_name", "")
        and r.get("elapsed_sec") is not None
    }

    # Group parallelization records by (version, machine), prepend processors=1 baseline
    groups = defaultdict(list)
    for r in records:
        procs = get_processors(r["test_name"])
        if procs is None:
            continue
        key = (r["version"], machine_label(r["machine"]))
        groups[key].append((procs, r["elapsed_sec"]))

    for key, points in groups.items():
        if 1 not in {p for p, _ in points} and key in serial_baseline:
            points.append((1, serial_baseline[key]))

    if not groups:
        return

    fig, (ax_e, ax_s) = plt.subplots(1, 2, figsize=(12, 5))
    colors = _color_cycle(len(groups))

    for idx, ((ver, mach), points) in enumerate(
        sorted(groups.items(), key=lambda x: version_sort_key(x[0][0]))
    ):
        points = sorted(points, key=lambda p: p[0])
        procs   = [p[0] for p in points]
        elapsed = [p[1] for p in points]
        label   = f"v{ver}  @  {mach}"
        c       = colors[idx]

        ax_e.plot(procs, elapsed, marker='o', color=c, label=label)

        # Speedup relative to processors=1 (or the smallest processor count present)
        baseline = elapsed[0]
        if baseline and baseline > 0:
            speedup = [baseline / t if t else None for t in elapsed]
            ax_s.plot(procs, speedup, marker='o', color=c, label=label)

    # Ideal speedup reference line (relative to the smallest processor count tested)
    all_procs = sorted({p for pts in groups.values() for p, _ in pts})
    if all_procs:
        ideal = [p / all_procs[0] for p in all_procs]
        ax_s.plot(all_procs, ideal, 'k--', linewidth=0.8, label='ideal')

    ax_e.set_xlabel("Processor count")
    ax_e.set_ylabel("Elapsed time (s)")
    ax_e.set_title("Wall time vs processor count")
    ax_e.legend(fontsize=8, loc='best')
    ax_e.grid(True, alpha=0.3)

    ax_s.set_xlabel("Processor count")
    ax_s.set_ylabel("Speedup")
    ax_s.set_title("Parallel speedup (relative to 1 processor)")
    ax_s.legend(fontsize=8, loc='best')
    ax_s.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "parallelization.png", dpi=150)
    plt.close(fig)
    print(f"  saved parallelization.png")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    FIGURES_DIR.mkdir(exist_ok=True)
    history = load_history()
    if not history:
        print("No performance history found — nothing to plot.")
        return

    print(f"Plotting {len(history)} record(s) from {HISTORY_FILE}")
    plot_performance_vs_version(history)
    plot_memory_vs_version(history)
    plot_scaling(history)
    plot_rk_order(history)
    plot_parallelization(history)
    print(f"Done. Figures written to {FIGURES_DIR}/")


if __name__ == "__main__":
    main()
