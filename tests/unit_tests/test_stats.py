from os import path, makedirs

import numpy as np
import pytest

from oceantracker.main import OceanTracker
from oceantracker.read_output.python import load_output_files


@pytest.fixture
def default_stats_configuration(
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


def test_gridded_statistics_2D_timeBased(
    default_stats_configuration, gridded_2D_timeBased
):
    ot = default_stats_configuration
    ot.add_class("particle_statistics", **gridded_2D_timeBased)
    case_info_file = ot.run()
    assert case_info_file is not None


def test_gridded_statistics_2D_timeBased_runningMean(
    default_stats_configuration,
    gridded_2D_timeBased_runningMean,
):
    ot = default_stats_configuration
    ot.add_class("particle_statistics", **gridded_2D_timeBased_runningMean)
    case_info_file = ot.run()
    assert case_info_file is not None


def test_gridded_statistics_2D_ageBased(
    default_stats_configuration, gridded_2D_ageBased
):
    ot = default_stats_configuration
    ot.add_class("particle_statistics", **gridded_2D_ageBased)
    case_info_file = ot.run()
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(case_info_file, name=gridded_2D_ageBased["name"])
    assert "count_all_released_age_bins" in stats, "count_all_released_age_bins missing from age-based stats output"
    assert stats["count_all_released_age_bins"].sum() > 0, "count_all_released_age_bins is all zeros — demographic computation produced no output"


def test_gridded_statistics_3D_timeBased(
    default_stats_configuration,
    gridded_3D_timeBased,
):
    ot = default_stats_configuration
    ot.add_class("particle_statistics", **gridded_3D_timeBased)
    case_info_file = ot.run()

    assert case_info_file is not None


def _relative_z(mode, x, tide, water_depth):
    """Vertical coordinate binned by 3D gridded stats, same conventions as
    GriddedStats3D_timeBased.do_counts()."""
    if mode == "geoid":
        return x[:, 2]  # m above mean water level, negative at depth
    if mode == "surface":
        return tide - x[:, 2]  # m below instantaneous surface, positive down
    return water_depth + x[:, 2]  # m above sea bed, positive up


def test_gridded_3D_kernel_sign_conventions():
    """Pin the sign conventions of the 3D counting kernel for all three
    vertical reference modes, using hand-computed cell indices."""
    from numba.typed import List as NumbaList
    from oceantracker.particle_statistics.gridded_statistics3D import GriddedStats3D_timeBased

    kernel = GriddedStats3D_timeBased._do_counts_and_summing_numba

    # one release group, 4x4 horizontal cells of 25 m, 4 vertical layers
    x_edges = np.linspace(0.0, 100.0, 5)[np.newaxis, :]
    y_edges = np.linspace(0.0, 100.0, 5)[np.newaxis, :]

    x = np.asarray(
        [
            [10.0, 10.0, -9.0],  # deep particle
            [60.0, 30.0, -1.0],  # near-surface particle
            [10.0, 10.0, 5.0],  # above all z bins in every mode
            [-10.0, 10.0, -5.0],  # outside grid in x
        ]
    )
    tide = np.asarray([0.5, 0.5, 0.5, 0.5])
    water_depth = np.asarray([20.0, 8.0, 20.0, 20.0])  # positive down
    group_ID = np.zeros(x.shape[0], dtype=np.int32)
    sel = np.arange(x.shape[0])

    # empty typed lists, as built in set_up_part_prop_lists() when no properties are binned
    prop_list = NumbaList([np.empty((1,))])
    prop_list.pop(0)
    sum_prop_list = NumbaList([np.empty((1, 1, 1, 1))])
    sum_prop_list.pop(0)

    def run_kernel(z_edges, z_rel):
        count = np.zeros((1, 4, 4, z_edges.size - 1), dtype=np.int64)
        kernel(group_ID, x, z_rel, x_edges, y_edges, z_edges, count,
               prop_list, sum_prop_list, sel)
        return count

    # geoid: fixed z bins, z=0 at mean water level, negative at depth
    count = run_kernel(np.linspace(-10.0, 0.0, 5), _relative_z("geoid", x, tide, water_depth))
    assert count.sum() == 2
    assert count[0, 0, 0, 0] == 1  # z=-9 in deepest bin [-10,-7.5]
    assert count[0, 1, 2, 3] == 1  # z=-1 in top bin [-2.5,0]

    # surface: bins are depth below instantaneous surface, positive down
    count = run_kernel(np.linspace(0.0, 10.0, 5), _relative_z("surface", x, tide, water_depth))
    assert count.sum() == 2
    assert count[0, 0, 0, 3] == 1  # 9.5 m below surface, deepest layer [7.5,10]
    assert count[0, 1, 2, 0] == 1  # 1.5 m below surface, top layer [0,2.5]

    # bottom: bins are height above sea bed, positive up
    count = run_kernel(np.linspace(0.0, 10.0, 5), _relative_z("bottom", x, tide, water_depth))
    assert count.sum() == 1  # deep particle is 11 m above bed, outside [0,10]
    assert count[0, 1, 2, 2] == 1  # 7 m above bed, layer [5,7.5]


def _edges_from_centers(centers, d):
    return np.append(centers - 0.5 * d, centers[-1] + 0.5 * d)


def _bin_tracked_particles(mode, tracks, itt, x_edges, y_edges, z_edges):
    """Reproduce the stats selection and binning for one tracks time step.
    Returns (r, c, k) cell indices, indices of selected particles and inside-grid mask."""
    moving = tracks["particle_status_flags"]["moving"]
    x = tracks["x"][itt]
    sel = np.flatnonzero((tracks["status"][itt] == moving) & np.isfinite(x).all(axis=1))
    z_rel = _relative_z(mode, x[sel], tracks["tide"][itt][sel], tracks["water_depth"][itt][sel])

    c = np.floor((x[sel, 0] - x_edges[0]) / (x_edges[1] - x_edges[0])).astype(np.int64)
    r = np.floor((x[sel, 1] - y_edges[0]) / (y_edges[1] - y_edges[0])).astype(np.int64)
    k = np.floor((z_rel - z_edges[0]) / (z_edges[1] - z_edges[0])).astype(np.int64)
    inside = ((0 <= r) & (r < y_edges.size - 1)
              & (0 <= c) & (c < x_edges.size - 1)
              & (0 <= k) & (k < z_edges.size - 1))
    return r, c, k, sel, inside


def _stats_grid_edges(stats):
    dx, dy, dz = stats["grid_spacings"]
    return (_edges_from_centers(stats["x"][0, :], dx),
            _edges_from_centers(stats["y"][0, :], dy),
            _edges_from_centers(stats["z"], dz))


def _bathymetry_transect(grid, x_edges, y_mid, n=200):
    """Sea bed z along a fixed constant-y transect spanning the stats grid,
    interpolated from the hindcast node bathymetry."""
    import matplotlib.tri as mtri

    tx = np.linspace(x_edges[0], x_edges[-1], n)
    ty = np.full(n, y_mid)
    tri = mtri.Triangulation(grid["x"][:, 0], grid["x"][:, 1], grid["triangles"])
    water_depth = np.asarray(mtri.LinearTriInterpolator(tri, grid["water_depth"])(tx, ty))
    return tx, -water_depth  # water_depth is positive down, so sea bed z = -water_depth


def _plot_relative_mode_slices(tracks, stats_by_mode, itt, plot_file):
    """x-z slice per mode along a fixed transect spanning the stats grid: water
    column, counting grid in true z-space and counted/uncounted particles, at
    one tracks/stats time step."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # fixed transect at the grid-centre y (release-point y), spanning the grid in x
    x_edges, y_edges, _ = _stats_grid_edges(next(iter(stats_by_mode.values())))
    y_mid = 0.5 * (y_edges[0] + y_edges[-1])
    tx, bed = _bathymetry_transect(tracks["grid"], x_edges, y_mid)

    # show only particles within one grid row of the transect, so they line up
    # with the grid drawn along it; tide is near-uniform in space, use its mean there
    x = tracks["x"][itt]
    dy = y_edges[1] - y_edges[0]
    band = np.isfinite(x).all(axis=1) & (np.abs(x[:, 1] - y_mid) <= dy)
    tide_level = np.nanmean(tracks["tide"][itt][band])

    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=True)
    for ax, (mode, stats) in zip(axes, stats_by_mode.items()):
        x_edges, y_edges, z_edges = _stats_grid_edges(stats)

        # water column: instantaneous surface (near-uniform) and interpolated sea bed
        ax.hlines(tide_level, x_edges[0], x_edges[-1], color="tab:blue", lw=1.5,
                  label="water surface (tide)")
        ax.plot(tx, bed, color="saddlebrown", lw=1.5, label="sea bed")

        # counting grid in true z-space, along the transect
        for e in x_edges:
            ax.axvline(e, color="0.85", lw=0.5, zorder=0)
        for e in z_edges:
            if mode == "geoid":
                ax.hlines(e, x_edges[0], x_edges[-1], color="0.6", lw=0.8, zorder=1)
            elif mode == "surface":
                ax.hlines(tide_level - e, x_edges[0], x_edges[-1], color="0.6", lw=0.8, zorder=1)
            else:  # bottom
                ax.plot(tx, bed + e, color="0.6", lw=0.8, zorder=1)

        # particles in the transect band, split into counted and uncounted
        r, c, k, sel, inside = _bin_tracked_particles(mode, tracks, itt, x_edges, y_edges, z_edges)
        counted = np.zeros(x.shape[0], dtype=bool)
        counted[sel[inside]] = True
        show = band & ~counted
        ax.plot(x[show, 0], x[show, 2], "x", color="0.4", ms=4, label="not counted")
        ax.plot(x[band & counted, 0], x[band & counted, 2], "o", color="tab:green",
                ms=4, label="counted")

        ax.set_xlim(x_edges[0] - 200, x_edges[-1] + 200)
        ax.set_title(f'relative to "{mode}"')
        ax.set_xlabel("x, m")

    axes[0].set_ylabel("z, m above mean water level")
    axes[0].legend(loc="lower left", fontsize=8)
    date = tracks["time"][itt].astype("datetime64[s]")
    fig.suptitle(f"3D gridded stats along transect, vertical grid and counted particles, t={date}")
    fig.tight_layout()
    fig.savefig(plot_file, dpi=150)
    plt.close(fig)
    print(f"Saved plot: {plot_file}")


def test_gridded_statistics_3D_relative_modes(
    base_settings,
    reader_demo_schism3D,
    basic_point_release,
    schism3D_release_locations,
    show_plots_flag,
    default_run_output_dir,
):
    """One run with the 3D counting grid referenced to the geoid, the moving
    water surface and the sea bed; counts cross-checked against an independent
    numpy re-binning of the written tracks."""
    ot = OceanTracker()
    ot.settings(**{**base_settings, "write_tracks": True})
    ot.add_class("reader", **reader_demo_schism3D)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": schism3D_release_locations["deep_point"]},
    )
    ot.add_class(
        "tracks_writer",
        update_interval=3600,
        turn_on_write_particle_properties_list=["tide", "water_depth"],
    )

    common = dict(
        class_name="GriddedStats3D_timeBased",
        rows=20,
        cols=20,
        layers=10,
        span_x=10000,
        span_y=10000,
        release_group_centered_grids=True,
        update_interval=3600,
        status_list=["moving"],
    )
    z_ranges = dict(
        geoid=dict(z_min=-10.0, z_max=0.0),
        surface=dict(z_min=0.0, z_max=10.0),
        bottom=dict(z_min=0.0, z_max=10.0),
    )
    for mode, z_range in z_ranges.items():
        ot.add_class(
            "particle_statistics",
            name=f"stats3D_{mode}",
            output_file_base=f"stats3D_{mode}",
            vertical_range_measured_relative_to=mode,
            **common,
            **z_range,
        )

    case_info_file = ot.run()
    assert case_info_file is not None

    tracks = load_output_files.load_track_data(case_info_file)
    stats_by_mode = {
        mode: load_output_files.load_stats_data(case_info_file, name=f"stats3D_{mode}")
        for mode in z_ranges
    }

    # geoid z bins are as configured
    assert np.allclose(stats_by_mode["geoid"]["z"], np.arange(-9.5, 0.0, 1.0))

    for mode, stats in stats_by_mode.items():
        counts = stats["count"]  # (time, release_group, rows, cols, layers)
        assert counts.sum() > 0, f'no particles counted in mode "{mode}"'

        # never count more than the alive particles
        assert np.all(
            counts.sum(axis=(1, 2, 3, 4)) <= stats["count_all_alive_particles"].sum(axis=1)
        )

        # exact cross-check against an independent numpy re-binning of the tracks
        x_edges, y_edges, z_edges = _stats_grid_edges(stats)
        n_times_checked = 0
        for it, t in enumerate(stats["time"]):
            itt = np.argmin(np.abs(tracks["time"] - t))
            if abs(tracks["time"][itt] - t) > 1.0:
                continue  # stats time not written to tracks file
            r, c, k, sel, inside = _bin_tracked_particles(mode, tracks, itt, x_edges, y_edges, z_edges)
            expected = np.zeros(counts.shape[2:], dtype=np.int64)
            np.add.at(expected, (r[inside], c[inside], k[inside]), 1)
            assert np.array_equal(counts[it, 0].astype(np.int64), expected), (
                f'counts differ from re-binned tracks, mode "{mode}", time step {it}'
            )
            n_times_checked += 1
        assert n_times_checked >= 3, "too few time steps aligned between stats and tracks"

    if show_plots_flag:
        makedirs(default_run_output_dir, exist_ok=True)
        # plot near high and low tide, so surface-following bins visibly move,
        # using only time steps late enough to have well spread particles
        n_particles = np.isfinite(tracks["x"][:, :, 0]).sum(axis=1)
        mean_tide = np.where(n_particles >= 0.5 * n_particles.max(),
                             np.nanmean(tracks["tide"], axis=1), np.nan)
        for label, itt in (("high_tide", int(np.nanargmax(mean_tide))),
                           ("low_tide", int(np.nanargmin(mean_tide)))):
            _plot_relative_mode_slices(
                tracks, stats_by_mode, itt,
                path.join(default_run_output_dir, f"relative_mode_slices_{label}.png"))


@pytest.mark.skip(reason="Not implemented yet")
def test_gridded_statistics_3D_ageBased():
    assert True


def test_gridded_statistics_2D_schism_with_particle_prop(
    default_stats_configuration,
    a_pollutant,
    gridded_2D_timeBased_with_PartProp,
):
    ot = default_stats_configuration
    ot.add_class("particle_properties", **a_pollutant)  # Required by heat map config
    ot.add_class("particle_statistics", **gridded_2D_timeBased_with_PartProp)

    case_info_file = ot.run()

    assert case_info_file is not None


def test_polygon_statistics_2D_timeBased(
    default_stats_configuration, polygon_stats_2D_timeBased, schism3D_release_locations
):
    ot = default_stats_configuration
    ot.add_class(
        "particle_statistics",
        **{
            **polygon_stats_2D_timeBased,
            "polygon_list": schism3D_release_locations["polygons"],
        },
    )
    case_info_file = ot.run()
    assert case_info_file is not None


def test_polygon_statistics_2D_ageBased(
    default_stats_configuration, polygon_stats_2D_ageBased, schism3D_release_locations
):
    ot = default_stats_configuration
    ot.add_class(
        "particle_statistics",
        **{
            **polygon_stats_2D_ageBased,
            "polygon_list": schism3D_release_locations["polygons"],
        },
    )
    case_info_file = ot.run()
    assert case_info_file is not None

    stats = load_output_files.load_stats_data(case_info_file, name=polygon_stats_2D_ageBased["name"])
    assert "count_all_released_age_bins" in stats, "count_all_released_age_bins missing from age-based stats output"
    assert stats["count_all_released_age_bins"].sum() > 0, "count_all_released_age_bins is all zeros — demographic computation produced no output"


def test_grid_center(
    default_stats_configuration,
    gridded_2D_timeBased,
    schism3D_release_locations,
):
    # **{**basic_point_release, "points": schism3D_release_locations["deep_point"]},
    ot = default_stats_configuration
    manually_centered_stats = {
        **(
            gridded_2D_timeBased
            | {
                "release_group_centered_grids": False,
                "grid_center": schism3D_release_locations["point"],

            }
        )
    }
    ot.add_class("particle_statistics", **manually_centered_stats)
    case_info_file = ot.run()
    assert case_info_file is not None
