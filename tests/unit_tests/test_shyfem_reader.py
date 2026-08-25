"""Tests for the SHYFEM reader, oceantracker/reader/SHYFEM_reader.py

The test hindcasts under data/hindcasts/shyfem3D* are built by
tests/build_shyfem_unit_test_hindcasts.py from the ISMAR-CNR EMERGE Adriatic sample.
They come in two variants which hold the *same* grid and fields:

    shyfem3D        keeps "element_index", the reader gets its triangulation from the files
    shyfem3D_grd    "element_index" removed and the file nodes shuffled into a different
                    order, with a companion ".grd", so the reader has to recover the
                    triangulation by matching grd nodes to file nodes on coordinates

so a run over one must reproduce a run over the other.
"""

from os import path

import numpy as np
import pytest
import xarray as xr

from oceantracker.main import OceanTracker
from oceantracker.reader import SHYFEM_reader

from tests.unit_tests.conftest import unittest_hindast_dir

SHYFEM_DIR = path.join(unittest_hindast_dir, 'shyfem3D')
SHYFEM_GRD_DIR = path.join(unittest_hindast_dir, 'shyfem3D_grd')
GRD_FILE = path.join(SHYFEM_GRD_DIR, 'shyfem_test_grid.grd')

# a point over the deeper part of the test grid, and depths near the surface and near the bed
RELEASE_POINTS = [[12.90, 45.10, -2.0], [12.90, 45.10, -25.0]]


@pytest.fixture
def reader_shyfem3D():
    return dict(input_dir=SHYFEM_DIR, file_mask='*.nc')


@pytest.fixture
def reader_shyfem3D_grd():
    return dict(input_dir=SHYFEM_GRD_DIR, file_mask='*.nc', grd_file_name=GRD_FILE)


def _run(settings, reader_params, output_file_base, points=RELEASE_POINTS, **extra):
    ot = OceanTracker()
    ot.settings(**{**settings, 'output_file_base': output_file_base,
                   'write_tracks': True, 'use_dispersion': False,
                   'time_step': 600, 'max_run_duration': 2 * 3600, **extra})
    ot.add_class('reader', **reader_params)
    ot.add_class('release_groups', name='p', class_name='PointRelease',
                 points=points, release_interval=0, pulse_size=4)
    ot.add_class('tracks_writer',
                 turn_on_write_particle_properties_list=['water_velocity', 'nz_cell', 'n_cell'])
    return ot.run()


def _tracks(case_info_file):
    run_dir = path.dirname(case_info_file)
    return xr.open_dataset(path.join(run_dir, 'tracks_rectangular_000.nc'), decode_timedelta=False)


# ".grd" file reading
# ------------------------------------------------------------------
def test_grd_file_reads_nodes_and_elements():
    grd = SHYFEM_reader.read_grd_file(GRD_FILE)

    assert grd['x'].shape[1] == 2
    assert grd['triangles'].shape[1] == 3
    assert grd['triangles'].shape[0] > 0
    assert grd['n_non_triangular_elements'] == 0

    # node numbers in the file are sparse, triangles must hold zero based *indices*
    assert grd['node_numbers'].max() > grd['x'].shape[0]
    assert grd['triangles'].min() == 0
    assert grd['triangles'].max() == grd['x'].shape[0] - 1


def test_grd_triangles_are_anticlockwise():
    grd = SHYFEM_reader.read_grd_file(GRD_FILE)
    p = grd['x'][grd['triangles']]
    area = 0.5 * ((p[:, 1, 0] - p[:, 0, 0]) * (p[:, 2, 1] - p[:, 0, 1])
                  - (p[:, 2, 0] - p[:, 0, 0]) * (p[:, 1, 1] - p[:, 0, 1]))
    assert np.all(area > 0.0)


def test_node_map_identical_grids_is_positional():
    grd = SHYFEM_reader.read_grd_file(GRD_FILE)
    node_map, method, n_unmapped = SHYFEM_reader.map_grd_nodes_to_dataset_nodes(grd['x'], grd['x'])

    assert method == 'positional'
    assert n_unmapped == 0
    assert np.array_equal(node_map, np.arange(grd['x'].shape[0]))


def test_node_map_reordered_grid_matches_on_coordinates():
    grd = SHYFEM_reader.read_grd_file(GRD_FILE)
    order = np.random.default_rng(0).permutation(grd['x'].shape[0])

    node_map, method, n_unmapped = SHYFEM_reader.map_grd_nodes_to_dataset_nodes(grd['x'], grd['x'][order, :])

    assert method == 'coordinate'
    assert n_unmapped == 0
    # node_map[i] is where grd node i ended up, so mapping back must recover the grd coords
    assert np.allclose(grd['x'][order, :][node_map, :], grd['x'])


def test_node_map_survives_float32_rounding():
    """The ".grd" holds 6 decimal text while the files hold float32, so an exact match fails."""
    grd = SHYFEM_reader.read_grd_file(GRD_FILE)
    as_float32 = grd['x'].astype(np.float32).astype(np.float64)
    order = np.random.default_rng(1).permutation(grd['x'].shape[0])

    node_map, method, n_unmapped = SHYFEM_reader.map_grd_nodes_to_dataset_nodes(grd['x'], as_float32[order, :])

    assert method == 'coordinate'
    assert n_unmapped == 0


def test_subset_triangles_drops_elements_with_missing_nodes():
    grd = SHYFEM_reader.read_grd_file(GRD_FILE)
    node_map = np.arange(grd['x'].shape[0], dtype=np.int64)
    dropped_node = int(grd['triangles'][0, 0])
    node_map[dropped_node] = -1

    triangles, n_dropped = SHYFEM_reader.subset_triangles(grd['triangles'], node_map)

    assert n_dropped == int(np.count_nonzero(np.any(grd['triangles'] == dropped_node, axis=1)))
    assert n_dropped > 0
    assert triangles.shape[0] == grd['triangles'].shape[0] - n_dropped
    assert not np.any(triangles == dropped_node)


# reader end to end
# ------------------------------------------------------------------
def test_shyfem3D_runs_with_element_index(base_settings, reader_shyfem3D):
    case_info_file = _run(base_settings, reader_shyfem3D, 'shyfem3D')
    assert case_info_file is not None

    with _tracks(case_info_file) as d:
        assert np.all(np.isfinite(d['x'].values[..., :2]))


def test_shyfem3D_runs_with_grd_file(base_settings, reader_shyfem3D_grd):
    case_info_file = _run(base_settings, reader_shyfem3D_grd, 'shyfem3D_grd')
    assert case_info_file is not None

    with _tracks(case_info_file) as d:
        assert np.all(np.isfinite(d['x'].values[..., :2]))


def test_grd_and_element_index_give_the_same_tracks(base_settings, reader_shyfem3D, reader_shyfem3D_grd):
    """Recovering the triangulation from the ".grd" must reproduce the in-file connectivity,
    even though the two hindcasts hold their nodes in a different order."""
    from_files = _tracks(_run(base_settings, reader_shyfem3D, 'shyfem3D_a'))
    from_grd = _tracks(_run(base_settings, reader_shyfem3D_grd, 'shyfem3D_b'))

    with from_files, from_grd:
        assert np.allclose(from_files['x'].values, from_grd['x'].values, atol=1.0e-9, equal_nan=True)
        assert np.allclose(from_files['water_velocity'].values, from_grd['water_velocity'].values,
                           atol=1.0e-9, equal_nan=True)


def test_missing_triangulation_is_a_clear_error(base_settings, reader_shyfem3D_grd):
    """Without "element_index" in the files and without a ".grd" there is no triangulation."""
    params = dict(reader_shyfem3D_grd)
    params.pop('grd_file_name')

    # OceanTracker traps setup errors and reports them, returning no case info file
    assert _run(base_settings, params, 'shyfem3D_no_grd') is None


# vertical grid
# ------------------------------------------------------------------
def test_vertical_grid_is_the_right_way_up(base_settings, reader_shyfem3D):
    """SHYFEM stores layers surface first and OceanTracker works bottom up, so the reader
    flips them.  Check a near surface particle really does see the file's surface layer."""
    case_info_file = _run(base_settings, reader_shyfem3D, 'shyfem3D_vertical',
                          points=[[12.90, 45.10, -0.5]])

    ds = xr.open_dataset(path.join(SHYFEM_DIR, 'shyfem_test_00.nc'), decode_times=False)
    with ds, _tracks(case_info_file) as d:
        n_levels = ds.sizes['level']
        # a particle just below the surface must sit in the topmost layer
        assert np.all(d['nz_cell'].values == n_levels - 1)

        # and its velocity must match the file's surface layer over the cell it is in
        triangles = ds.element_index.values - 1
        nodes = triangles[int(d['n_cell'].values[0, 0]), :]
        u_surface = ds.u_velocity.values[0, nodes, 0]
        v_surface = ds.v_velocity.values[0, nodes, 0]

        u, v = d['water_velocity'].values[0, 0, 0], d['water_velocity'].values[0, 0, 1]
        assert u_surface.min() - 1.0e-6 <= u <= u_surface.max() + 1.0e-6
        assert v_surface.min() - 1.0e-6 <= v <= v_surface.max() + 1.0e-6


def test_particles_below_the_bed_are_not_given_fill_values(base_settings, reader_shyfem3D):
    """Values below the sea bed are _FillValue = -999, none of that may reach a particle."""
    case_info_file = _run(base_settings, reader_shyfem3D, 'shyfem3D_bed',
                          points=[[12.90, 45.10, -2.0], [12.90, 45.10, -30.0]])

    with _tracks(case_info_file) as d:
        velocity = d['water_velocity'].values
        assert np.all(np.isfinite(velocity))
        assert np.all(np.abs(velocity) < 10.0)


def test_water_depth_and_tide_match_the_files(base_settings, reader_shyfem3D):
    case_info_file = _run(base_settings, reader_shyfem3D, 'shyfem3D_depth')

    ds = xr.open_dataset(path.join(SHYFEM_DIR, 'shyfem_test_00.nc'), decode_times=False)
    with ds, _tracks(case_info_file) as d:
        depth = d['water_depth'].values
        assert np.all(depth > 0.0)
        # "total_depth" is positive down, and OceanTracker's water_depth follows it
        assert depth.max() <= ds.total_depth.values.max() + 1.0e-3
        assert np.all(np.abs(d['tide'].values) < 5.0)
