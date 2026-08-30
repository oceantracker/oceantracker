"""Temporary plotting helpers for checking the SHYFEM reader, oceantracker/reader/SHYFEM_reader.py

These draw straight from the hindcast files and the ".grd" grid file, so they can be used to
check the triangulation and the vertical grid *before* running OceanTracker, plus a wrapper
for plotting the tracks of a run.

    python tests/dev_runs/dev_shyfem_plots.py all        --hindcast <file.nc> --grd <file.grd>
    python tests/dev_runs/dev_shyfem_plots.py grid       --hindcast <file.nc> --grd <file.grd>
    python tests/dev_runs/dev_shyfem_plots.py vertical   --hindcast <file.nc>
    python tests/dev_runs/dev_shyfem_plots.py velocity   --hindcast <file.nc> --grd <file.grd>
    python tests/dev_runs/dev_shyfem_plots.py tracks     --case-info <caseInfo.json>
    python tests/dev_runs/dev_shyfem_plots.py animate    --case-info <caseInfo.json> --save <movie.mp4>

For the EMERGE Adriatic hindcasts, eg

    python tests/dev_runs/dev_shyfem_plots.py grid \
        --hindcast /data4/hindcasts/SHYFEM/venice_lagoon/2019/adriatic_hind_201901_emerge.nc \
        --grd      /data4/hindcasts/SHYFEM/venice_lagoon/adri_lags_175776.grd \
        --axis 12.15 12.65 45.15 45.60
"""

import argparse
from os import path, makedirs

import numpy as np
import xarray as xr
from matplotlib import pyplot as plt
from matplotlib.tri import Triangulation

from oceantracker.reader import SHYFEM_reader


# loading
# ------------------------------------------------------------------
def load_shyfem_grid(hindcast_file, grd_file=None):
    """Node coords, bathymetry and triangulation, the same way the reader builds them."""
    ds = xr.open_dataset(hindcast_file, decode_times=False)

    x = np.stack((ds.longitude.values, ds.latitude.values), axis=1).astype(np.float64)
    grid = dict(x=x, total_depth=ds.total_depth.values, level=ds.level.values, file=hindcast_file)

    if 'element_index' in ds.variables:
        grid['triangles'] = ds.element_index.values - 1
        grid['n_grd_elements'] = grid['triangles'].shape[0]
        grid['method'] = 'element_index in file'
    elif grd_file is not None:
        grd = SHYFEM_reader.read_grd_file(grd_file)
        node_map, method, _ = SHYFEM_reader.map_grd_nodes_to_dataset_nodes(grd['x'], x)
        triangles, n_dropped = SHYFEM_reader.subset_triangles(grd['triangles'], node_map)
        grid.update(triangles=triangles, n_grd_elements=grd['triangles'].shape[0],
                    n_dropped=n_dropped, method=f'grd file, matched by {method}')
    else:
        raise ValueError('hindcast has no "element_index", a ".grd" file is needed')

    grid['n_orphan_nodes'] = x.shape[0] - np.unique(grid['triangles']).size
    ds.close()
    return grid


def _triangulation(grid):
    return Triangulation(grid['x'][:, 0], grid['x'][:, 1], grid['triangles'])


def _set_axis(ax, grid, axis_lims):
    if axis_lims is not None:
        ax.set_xlim(axis_lims[0], axis_lims[1])
        ax.set_ylim(axis_lims[2], axis_lims[3])
    ax.set_xlabel('longitude')
    ax.set_ylabel('latitude')
    # rough aspect correction for lon/lat away from the equator
    ax.set_aspect(1.0 / np.cos(np.deg2rad(np.mean(ax.get_ylim()))))


def bottom_layer_index(grid):
    """Deepest layer holding data at each node, bottom up, as the reader computes it."""
    level = grid['level']
    layer_top = np.concatenate(([0.0], level[:-1]))
    is_wet = layer_top[np.newaxis, :] < grid['total_depth'][:, np.newaxis]
    index = np.full(grid['x'].shape[0], level.size - 1, dtype=np.int32)
    has_any = np.any(is_wet, axis=1)
    # flip to bottom up ordering
    index[has_any] = (level.size - is_wet.sum(axis=1))[has_any]
    return index


# plots
# ------------------------------------------------------------------
def plot_grid(grid, axis_lims=None, show_mesh=None, plot_file_name=None):
    """Bathymetry on the triangulation, with the mesh drawn over it when zoomed in."""
    tri = _triangulation(grid)
    fig, ax = plt.subplots(figsize=(10, 8))

    depth = np.where(grid['total_depth'] > 0, grid['total_depth'], np.nan)
    patches = ax.tripcolor(tri, depth, shading='gouraud', cmap='viridis_r')
    fig.colorbar(patches, ax=ax, label='total_depth (m), positive down')

    if show_mesh is None:
        show_mesh = axis_lims is not None
    if show_mesh:
        ax.triplot(tri, color='k', linewidth=0.15, alpha=0.5)

    dropped = f', {grid["n_dropped"]} of {grid["n_grd_elements"]} elements dropped' if 'n_dropped' in grid else ''
    ax.set_title(f'SHYFEM grid, {grid["x"].shape[0]} nodes, {grid["triangles"].shape[0]} elements\n'
                 f'{grid["method"]}{dropped}, {grid["n_orphan_nodes"]} nodes in no element', fontsize=9)
    _set_axis(ax, grid, axis_lims)
    return _show(fig, plot_file_name)


def plot_dry_and_intertidal_nodes(grid, axis_lims=None, plot_file_name=None):
    """SHYFEM lagoon grids carry nodes whose bed is above the datum, ie total_depth <= 0."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.triplot(_triangulation(grid), color='0.8', linewidth=0.1)

    depth = grid['total_depth']
    for sel, colour, label in [(depth > 1.2, 'tab:blue', 'below first z level'),
                               ((depth > 0) & (depth <= 1.2), 'tab:orange', 'inside the top layer'),
                               (depth <= 0, 'tab:red', 'bed above datum')]:
        ax.plot(grid['x'][sel, 0], grid['x'][sel, 1], '.', color=colour, markersize=1,
                label=f'{label} ({int(np.count_nonzero(sel))})')

    ax.legend(markerscale=8, fontsize=8)
    ax.set_title('node bathymetry classes, nodes shallower than the first z level\n'
                 'have the sea bed cutting through the top layer', fontsize=9)
    _set_axis(ax, grid, axis_lims)
    return _show(fig, plot_file_name)


def plot_vertical_structure(grid, node=None, plot_file_name=None):
    """The fixed z grid, how many layers each node has, and one node's profile."""
    level = grid['level']
    n_bottom = bottom_layer_index(grid)
    n_layers = level.size - n_bottom  # number of layers holding data at each node

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # the fixed z levels
    z_interface = -np.concatenate(([0.0], level))[::-1]
    axes[0].hlines(z_interface, 0, 1, color='tab:blue', linewidth=0.8)
    axes[0].set_ylabel('z (m), positive up')
    axes[0].set_xticks([])
    axes[0].set_title(f'{level.size} fixed z layers\n{level.size + 1} interfaces, deepest {z_interface[0]:.0f} m',
                      fontsize=9)

    # how many layers each node has
    axes[1].hist(n_layers, bins=np.arange(level.size + 2) - 0.5, color='tab:blue')
    axes[1].set_xlabel('layers holding data')
    axes[1].set_ylabel('nodes')
    axes[1].set_yscale('log')
    axes[1].set_title('water column depth in layers', fontsize=9)

    # a profile at one node
    if node is None:
        node = int(np.argmax(grid['total_depth']))
    ds = xr.open_dataset(grid['file'], decode_times=False)
    u = ds.u_velocity.values[0, node, :]
    ds.close()

    z_layer = 0.5 * (z_interface[:-1] + z_interface[1:])
    nb = n_bottom[node]
    axes[2].plot(u[::-1], z_layer, '.-', color='0.7', label='all layers in file')
    axes[2].plot(u[::-1][nb:], z_layer[nb:], 'o-', color='tab:blue', label='layers above the bed')
    axes[2].axhline(-grid['total_depth'][node], color='tab:red', linestyle='--', label='sea bed')
    axes[2].set_xlabel('u_velocity (m/s)')
    axes[2].set_ylabel('z (m)')
    axes[2].legend(fontsize=7)
    axes[2].set_title(f'node {node}, total_depth {grid["total_depth"][node]:.1f} m\n'
                      f'bottom layer index {nb}', fontsize=9)

    fig.tight_layout()
    return _show(fig, plot_file_name)


def plot_surface_velocity(grid, time_step=0, stride=None, axis_lims=None, plot_file_name=None):
    """Surface layer currents, speed shaded with arrows over the top."""
    ds = xr.open_dataset(grid['file'], decode_times=False)
    u = ds.u_velocity.values[time_step, :, 0]
    v = ds.v_velocity.values[time_step, :, 0]
    ds.close()

    dry = grid['total_depth'] <= 0
    u, v = np.where(dry, np.nan, u), np.where(dry, np.nan, v)
    speed = np.hypot(u, v)

    fig, ax = plt.subplots(figsize=(10, 8))
    patches = ax.tripcolor(_triangulation(grid), speed, shading='gouraud', cmap='magma')
    fig.colorbar(patches, ax=ax, label='surface speed (m/s)')

    if stride is None:
        stride = max(1, grid['x'].shape[0] // 1500)
    s = slice(None, None, stride)
    ax.quiver(grid['x'][s, 0], grid['x'][s, 1], u[s], v[s], color='w', scale=12, width=0.0015)

    ax.set_title(f'surface velocity, time step {time_step}\n{path.basename(grid["file"])}', fontsize=9)
    _set_axis(ax, grid, axis_lims)
    return _show(fig, plot_file_name)


def plot_tracks(case_info_file, axis_lims=None, plot_file_name=None):
    """Particle tracks of a completed run over the bathymetry."""
    from oceantracker.read_output.python import load_output_files

    tracks = load_output_files.load_track_data(case_info_file)
    grid = load_output_files.load_grid(case_info_file)

    fig, ax = plt.subplots(figsize=(10, 8))
    tri = Triangulation(grid['x'][:, 0], grid['x'][:, 1], grid['triangles'])
    ax.tripcolor(tri, np.where(grid['water_depth'] > 0, grid['water_depth'], np.nan),
                 shading='gouraud', cmap='Blues', alpha=0.6)

    x = tracks['x']
    for group in np.unique(tracks['IDrelease_group']):
        sel = tracks['IDrelease_group'] == group
        ax.plot(x[:, sel, 0], x[:, sel, 1], linewidth=0.4, alpha=0.5)
        ax.plot(x[0, sel, 0], x[0, sel, 1], 'k.', markersize=3)

    ax.set_title(f'{x.shape[1]} particles, {x.shape[0]} time steps\n{path.basename(path.dirname(case_info_file))}',
                 fontsize=9)
    _set_axis(ax, dict(x=grid['x']), axis_lims)
    return _show(fig, plot_file_name)


def animate_tracks(case_info_file, axis_lims=None, movie_file=None, fps=10, dpi=150,
                   max_duration=None, colour_using_data=None, title=None):
    """Animate particle tracks moving over the grid, eg through the Venice lagoon channels.

    Thin wrapper around oceantracker.plot_output.plot_tracks.animate_particles.
    With "movie_file" given (eg "shyfem_animation.mp4") it saves a video, otherwise it
    calls plt.show() for an interactive window.
    """
    from oceantracker.plot_output.plot_tracks import animate_particles
    from oceantracker.read_output.python import load_output_files

    track_data = load_output_files.load_track_data(case_info_file)

    return animate_particles(track_data, axis_lims=axis_lims, movie_file=movie_file,
                             fps=fps, dpi=dpi, max_duration=max_duration,
                             colour_using_data=colour_using_data, title=title,
                             back_ground_depth=True)


def _show(fig, plot_file_name):
    if plot_file_name is not None:
        fig.savefig(plot_file_name, dpi=150, bbox_inches='tight')
        print('wrote', plot_file_name)
        plt.close(fig)
    else:
        plt.show()
    return fig


# do the lot
# ------------------------------------------------------------------
def plot_all(hindcast_file, grd_file=None, out_dir='.', case_info_file=None,
             axis_lims=None, zoom_axis_lims=None, time_step=0, node=None, prefix='shyfem'):
    """Draw and save every figure in one go, returns the list of files written.

        from tests.dev_runs.dev_shyfem_plots import plot_all
        plot_all('/data4/hindcasts/SHYFEM/venice_lagoon/2019/adriatic_hind_201901_emerge.nc',
                 grd_file='/data4/hindcasts/SHYFEM/venice_lagoon/adri_lags_175776.grd',
                 out_dir='shyfem_figs',
                 zoom_axis_lims=[12.15, 12.65, 45.15, 45.60])
    """
    makedirs(out_dir, exist_ok=True)
    grid = load_shyfem_grid(hindcast_file, grd_file)
    print(f'{grid["x"].shape[0]} nodes, {grid["triangles"].shape[0]} elements, via {grid["method"]}')

    def name(tag):
        return path.join(out_dir, f'{prefix}_{tag}.png')

    written = []
    for tag, draw in [
            ('grid', lambda f: plot_grid(grid, axis_lims=axis_lims, show_mesh=False, plot_file_name=f)),
            ('grid_zoom', lambda f: plot_grid(grid, axis_lims=zoom_axis_lims, show_mesh=True, plot_file_name=f)),
            ('nodes', lambda f: plot_dry_and_intertidal_nodes(grid, axis_lims=zoom_axis_lims or axis_lims,
                                                              plot_file_name=f)),
            ('vertical', lambda f: plot_vertical_structure(grid, node=node, plot_file_name=f)),
            ('velocity', lambda f: plot_surface_velocity(grid, time_step=time_step, axis_lims=axis_lims,
                                                         plot_file_name=f)),
            ('tracks', lambda f: plot_tracks(case_info_file, axis_lims=axis_lims, plot_file_name=f)),
            ]:
        if tag == 'grid_zoom' and zoom_axis_lims is None:
            continue
        if tag == 'tracks' and case_info_file is None:
            continue
        try:
            draw(name(tag))
            written.append(name(tag))
        except Exception as e:
            # one bad plot should not stop the rest
            print(f'  skipped "{tag}", {type(e).__name__}: {e}')

    return written


# command line
# ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('plot', choices=['all', 'grid', 'nodes', 'vertical', 'velocity', 'tracks', 'animate'])
    ap.add_argument('--hindcast')
    ap.add_argument('--grd', default=None)
    ap.add_argument('--case-info', default=None)
    ap.add_argument('--axis', nargs=4, type=float, default=None,
                    metavar=('LON0', 'LON1', 'LAT0', 'LAT1'))
    ap.add_argument('--time-step', type=int, default=0)
    ap.add_argument('--node', type=int, default=None)
    ap.add_argument('--save', default=None)
    ap.add_argument('--out-dir', default='shyfem_figs', help='where "all" writes its figures')
    ap.add_argument('--zoom', nargs=4, type=float, default=None,
                    metavar=('LON0', 'LON1', 'LAT0', 'LAT1'),
                    help='second, zoomed in extent for "all", drawn with the mesh over the top')
    args = ap.parse_args()

    if args.plot == 'all':
        for f in plot_all(args.hindcast, grd_file=args.grd, out_dir=args.out_dir,
                          case_info_file=args.case_info, axis_lims=args.axis,
                          zoom_axis_lims=args.zoom, time_step=args.time_step, node=args.node):
            print('  ', f)
        return

    if args.plot == 'tracks':
        plot_tracks(args.case_info, axis_lims=args.axis, plot_file_name=args.save)
        return

    if args.plot == 'animate':
        animate_tracks(args.case_info, axis_lims=args.axis, movie_file=args.save)
        return

    grid = load_shyfem_grid(args.hindcast, args.grd)
    print(f'{grid["x"].shape[0]} nodes, {grid["triangles"].shape[0]} elements, via {grid["method"]}')

    if args.plot == 'grid':
        plot_grid(grid, axis_lims=args.axis, plot_file_name=args.save)
    elif args.plot == 'nodes':
        plot_dry_and_intertidal_nodes(grid, axis_lims=args.axis, plot_file_name=args.save)
    elif args.plot == 'vertical':
        plot_vertical_structure(grid, node=args.node, plot_file_name=args.save)
    elif args.plot == 'velocity':
        plot_surface_velocity(grid, time_step=args.time_step, axis_lims=args.axis,
                              plot_file_name=args.save)


if __name__ == '__main__':
    main()
