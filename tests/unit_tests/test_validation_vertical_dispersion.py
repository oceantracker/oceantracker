"""
Validation of the vertical random walk with an A_Z profile: particles in a well-mixed water column must stay well-mixed.

A uniform vertical particle distribution stays uniform only if the drift the particle gets is the exact vertical
derivative of the A_Z it gets (Visser 1997). Three levels of tests, from the root cause to the full model:
    1. the vertical gradient a particle reads is the slope of the A_Z it reads (deterministic, no particles)
    2. a uniform column stays uniform, stepping particles with the production gradient, interpolator and random walk kernels,
       with a negative control showing the test fails for a vertically interpolated gradient
    3. a uniform column stays uniform in a full OceanTracker run on a synthetic still-water SCHISM hindcast

Ported from tests/dev_runs/dev_vertical_gradient_comparison.ipynb
"""
from functools import cache
from os import path

import numpy as np
import pytest
import xarray as xr

from oceantracker import definitions
from oceantracker.main import OceanTracker
from oceantracker.read_output.python import load_output_files
from oceantracker.fields import field_vertical_gradient
from oceantracker.interpolator.util import triangle_eval_interp
from oceantracker.dispersion.random_walk import RandomWalk

DEMO_HINDCAST = path.join(path.dirname(definitions.package_dir), 'tutorials_how_to', 'demo_hindcast',
                          'schsim3D', 'demo_hindcast_schisim3D_00.nc')
Z0 = 0.0003  # default si.settings.z0, thin layer tolerance of the gradient kernels
KAPPA = 0.41
N_BINS = 20  # equal thickness depth bins for the uniformity check

# max share of particles that would have to move to make the column uniform,
# sampling noise is ~1%, failing versions of the gradient give 6-60%
MAX_MISPLACED = 0.03


# ---------------------------------------------------------------------------------------------------------------
# vertical profiles, z interfaces from bed to free surface at z=0, and A_Z at the interfaces
# ---------------------------------------------------------------------------------------------------------------
def _K_parabolic(z, H, u_star, K_bg=1e-5):
    h = z + H
    return K_bg + KAPPA * u_star * h * (1. - h / H)


def _K_visser_like(z):
    # smooth profile with a surface and a bed maximum, similar to Visser (1997) fig 1
    def f(u): return u * np.exp(0.5 * (1. - u * u))
    s = -z
    return 1e-3 + 0.012 * f((s + 0.5) / 3.) + 0.02 * f((40. - s) / 5.)


@cache
def _profile(name):
    """returns z interfaces, A_Z at the interfaces and the vertical grid type the gradient is calculated for"""
    if name == 'parabolic_20m':
        zi = np.linspace(-20., 0., 11)
        return zi, _K_parabolic(zi, 20., 0.05), 'z_interfaces'
    if name == 'visser_like_40m':
        zi = np.linspace(-40., 0., 21)
        return zi, _K_visser_like(zi), 'z_interfaces'
    if name == 'demo_schism_node667':
        # real profile, 8 uneven levels, A_Z jumps by orders of magnitude between levels
        with xr.open_dataset(DEMO_HINDCAST, decode_times=False) as ds:
            zi = ds['zcor'].values[0, 667].astype(np.float64)
            K = ds['diffusivity'].values[0, 667].astype(np.float64)
        return zi - zi[-1], K, 'z_interfaces'
    if name == 'shallow_1m':
        zi = np.linspace(-1., 0., 21)
        return zi, _K_parabolic(zi, 1., 0.02), 'sigma_levels'
    raise ValueError(name)


PROFILES = ['parabolic_20m', 'visser_like_40m', 'demo_schism_node667', 'shallow_1m']


# ---------------------------------------------------------------------------------------------------------------
# a single triangle whose 3 nodes have the same vertical grid, in the production [time, node, z, component] layout
# ---------------------------------------------------------------------------------------------------------------
TRIANGLES = np.array([[0, 1, 2]], dtype=np.int32)
N_BUFFER = np.array([0, 1], dtype=np.int32)


def _stored_gradient(F, zi, grid):
    """run the production VerticalGradient kernel for field F[time, node, z, 1]"""
    G = np.zeros_like(F)
    n_time, n_nodes = F.shape[:2]
    bottom_interface_index = np.zeros(n_nodes, dtype=np.int32)
    if grid == 'sigma_levels':
        water_depth = np.full((1, n_nodes, 1, 1), -zi[0], dtype=np.float32)
        tide = np.zeros((n_time, n_nodes, 1, 1), dtype=np.float32)
        sigma = ((zi - zi[0]) / (zi[-1] - zi[0])).astype(np.float32)
        field_vertical_gradient._calc_field_vert_grad_from_sigma_levels(F, sigma, tide, water_depth,
                                                                       bottom_interface_index, Z0, G)
    else:
        z_interface = np.broadcast_to(zi, (n_time, n_nodes, zi.size)).astype(np.float32)
        field_vertical_gradient._calc_field_vert_grad_from_z_interfaces(F, z_interface, bottom_interface_index, Z0, G)
    return G


def _vertical_cell(z, zi):
    nz_cell = np.clip(np.searchsorted(zi, z, side='right') - 1, 0, zi.size - 2).astype(np.int32)
    z_fraction = ((z - zi[nz_cell]) / (zi[nz_cell + 1] - zi[nz_cell])).astype(np.float32)
    return nz_cell, z_fraction


def _interp(F, n_cell, bc_coords, nz_cell, z_fraction, weight_time_steps, active):
    """production interpolation of a field linear in the vertical"""
    out = np.zeros(active.size)
    triangle_eval_interp.time_dependent_3D_scalar_field_data_in_all_layers(
        N_BUFFER, weight_time_steps, F, TRIANGLES, n_cell, bc_coords, nz_cell, z_fraction, out, active)
    return out


def _interp_layer_value(G, n_cell, bc_coords, nz_cell, weight_time_steps, active, ragged_bottom=False):
    """production interpolation of a per layer field, as used for is_layer_value fields like the vertical gradient"""
    out = np.zeros(active.size)
    if ragged_bottom:
        bottom_interface_index = np.zeros(G.shape[1], dtype=np.int32)
        triangle_eval_interp.time_dependent_3D_scalar_layer_value_ragged_bottom(
            N_BUFFER, weight_time_steps, G, TRIANGLES, bottom_interface_index, n_cell, bc_coords, nz_cell, out, active)
    else:
        triangle_eval_interp.time_dependent_3D_scalar_layer_value_data_in_all_layers(
            N_BUFFER, weight_time_steps, G, TRIANGLES, n_cell, bc_coords, nz_cell, out, active)
    return out


def _misplaced(z, zi):
    """share of particles that would have to move to make the column uniform"""
    counts, _ = np.histogram(z, bins=np.linspace(zi[0], zi[-1], N_BINS + 1))
    c = counts / counts.mean()
    return 0.5 * np.mean(np.abs(c - 1.))


# ---------------------------------------------------------------------------------------------------------------
# 1. gradient the particle reads is the slope of the A_Z it reads
# ---------------------------------------------------------------------------------------------------------------
@pytest.mark.validation
@pytest.mark.parametrize('ragged_bottom', [False, True], ids=['data_in_all_layers', 'ragged_bottom'])
@pytest.mark.parametrize('grid', ['z_interfaces', 'sigma_levels'])
@pytest.mark.parametrize('profile', PROFILES)
def test_vertical_gradient_is_slope_of_interpolated_A_Z(profile, grid, ragged_bottom):
    """the drift a particle gets must be the exact vertical derivative of the linearly interpolated A_Z it gets,
    otherwise a well-mixed column does not stay well-mixed"""
    rng = np.random.default_rng(0)
    zi, K, _ = _profile(profile)

    # different A_Z at each node and time step, gradient is linear in A_Z, so the property still holds
    F = (K[np.newaxis, np.newaxis, :] * rng.uniform(0.5, 2., (2, 3, 1)))[..., np.newaxis].astype(np.float32)
    G = _stored_gradient(F, zi, grid)

    N = 20_000
    active = np.arange(N, dtype=np.int32)
    n_cell = np.zeros(N, dtype=np.int32)
    bc_coords = rng.dirichlet(np.ones(3), N)
    weight_time_steps = np.array([0.3, 0.7])
    nz_cell, z_fraction = _vertical_cell(rng.uniform(zi[0], zi[-1], N), zi)

    # slope of A_Z within the particle's layer, from the production interpolator at the layer's bottom and top
    K_bottom = _interp(F, n_cell, bc_coords, nz_cell, np.zeros(N, np.float32), weight_time_steps, active)
    K_top = _interp(F, n_cell, bc_coords, nz_cell, np.ones(N, np.float32), weight_time_steps, active)
    expected = (K_top - K_bottom) / (zi[nz_cell + 1] - zi[nz_cell])

    G_particle = _interp_layer_value(G, n_cell, bc_coords, nz_cell, weight_time_steps, active, ragged_bottom)

    np.testing.assert_allclose(G_particle, expected, rtol=1e-5, atol=1e-6 * np.abs(expected).max())


# ---------------------------------------------------------------------------------------------------------------
# 2. well-mixed column stays well-mixed, stepping particles with the production kernels
# ---------------------------------------------------------------------------------------------------------------
def _simulate_well_mixed(profile, dt, duration, sample_interval, read_gradient='layer_value', N=20_000, seed=0):
    """random walk of particles starting uniform in a still column, reflecting at the bed and free surface,
    returns the misplaced share of the particles sampled over the second half of the run"""
    rng = np.random.default_rng(seed)
    zi, K, grid = _profile(profile)

    F = np.broadcast_to(K, (2, 3, zi.size))[..., np.newaxis].astype(np.float32)
    G = _stored_gradient(F, zi, grid)

    active = np.arange(N, dtype=np.int32)
    n_cell = np.zeros(N, dtype=np.int32)
    bc_coords = np.full((N, 3), 1. / 3.)
    weight_time_steps = np.array([1., 0.])
    random_walk_velocity = np.zeros(3)  # horizontal walk, not used
    velocity_modifier = np.zeros((N, 3))

    z = rng.uniform(zi[0], zi[-1], N)
    n_steps = int(round(duration / dt))
    sample_every = int(round(sample_interval / dt))
    samples = []
    for n in range(1, n_steps + 1):
        nz_cell, z_fraction = _vertical_cell(z, zi)
        A_Z = _interp(F, n_cell, bc_coords, nz_cell, z_fraction, weight_time_steps, active)
        if read_gradient == 'layer_value':
            A_Z_gradient = _interp_layer_value(G, n_cell, bc_coords, nz_cell, weight_time_steps, active)
        else:
            # negative control, interpolating the gradient vertically blends it with the layer above
            A_Z_gradient = _interp(G, n_cell, bc_coords, nz_cell, z_fraction, weight_time_steps, active)

        velocity_modifier[:] = 0.
        RandomWalk._add_random_walk_velocity_modifier_A_Z_profile(A_Z, A_Z_gradient, random_walk_velocity, dt,
                                                                  active, velocity_modifier)
        z = _reflect(z + velocity_modifier[:, 2] * dt, zi[0], zi[-1])

        if n > n_steps // 2 and n % sample_every == 0:
            samples.append(z.copy())

    return _misplaced(np.concatenate(samples), zi)


def _reflect(z, z_bottom, z_top):
    while True:
        above, below = z > z_top, z < z_bottom
        if not (above.any() or below.any()):
            return z
        z[above] = 2. * z_top - z[above]
        z[below] = 2. * z_bottom - z[below]


# time step, duration, sample interval
WELL_MIXED_RUNS = {
    'parabolic_20m': (10., 6 * 3600., 1800.),
    'visser_like_40m': (10., 12 * 3600., 1800.),
    'demo_schism_node667': (10., 6 * 3600., 1800.),
    'shallow_1m': (1., 3600., 60.),
}


@pytest.mark.validation
@pytest.mark.parametrize('profile', PROFILES)
def test_well_mixed_column_stays_well_mixed(profile):
    misplaced = _simulate_well_mixed(profile, *WELL_MIXED_RUNS[profile])
    print(f'{profile}: misplaced {100 * misplaced:.1f}%')
    assert misplaced < MAX_MISPLACED, \
        f'{100 * misplaced:.1f}% of particles misplaced, column did not stay well-mixed'


@pytest.mark.validation
@pytest.mark.parametrize('profile', ['visser_like_40m', 'demo_schism_node667'])
def test_well_mixed_negative_control(profile):
    """shows the well-mixed test can fail, by reading the gradient interpolated vertically"""
    misplaced = _simulate_well_mixed(profile, *WELL_MIXED_RUNS[profile], read_gradient='interpolated')
    print(f'{profile}, interpolated gradient: misplaced {100 * misplaced:.1f}%')
    assert misplaced > 2 * MAX_MISPLACED, \
        f'only {100 * misplaced:.1f}% misplaced with an interpolated gradient, well-mixed test is not sensitive enough'


# ---------------------------------------------------------------------------------------------------------------
# 3. well-mixed column stays well-mixed in a full OceanTracker run
# ---------------------------------------------------------------------------------------------------------------
def _write_still_water_schism_hindcast(file_name, zi, K, hours, n=5, dx=2000.):
    """flat bottom SCHISM hindcast on a n by n node grid, zero velocity and tide, the same A_Z profile everywhere"""
    x, y = np.meshgrid(np.arange(n) * dx, np.arange(n) * dx)
    x, y = x.ravel(), y.ravel()
    triangles = []
    for j in range(n - 1):
        for i in range(n - 1):
            a = j * n + i
            triangles += [[a, a + 1, a + n + 1], [a, a + n + 1, a + n]]
    # one based, with zero 4th node for triangles
    face_nodes = np.zeros((len(triangles), 4), dtype=np.int32)
    face_nodes[:, :3] = np.asarray(triangles) + 1

    n_time, n_nodes, n_faces, n_z = hours + 1, x.size, face_nodes.shape[0], zi.size
    dims3D = ('time', 'nSCHISM_hgrid_node', 'nSCHISM_vgrid_layers')
    ds = xr.Dataset(
        dict(SCHISM_hgrid_node_x=('nSCHISM_hgrid_node', x.astype(np.float32)),
             SCHISM_hgrid_node_y=('nSCHISM_hgrid_node', y.astype(np.float32)),
             SCHISM_hgrid_face_nodes=(('nSCHISM_hgrid_face', 'nMaxSCHISM_hgrid_face_nodes'), face_nodes),
             node_bottom_index=('nSCHISM_hgrid_node', np.ones(n_nodes, dtype=np.int32)),
             depth=('nSCHISM_hgrid_node', np.full(n_nodes, -zi[0], dtype=np.float32)),
             zcor=(dims3D, np.broadcast_to(zi, (n_time, n_nodes, n_z)).astype(np.float32)),
             diffusivity=(dims3D, np.broadcast_to(K, (n_time, n_nodes, n_z)).astype(np.float32)),
             elev=(('time', 'nSCHISM_hgrid_node'), np.zeros((n_time, n_nodes), dtype=np.float32)),
             hvel=(dims3D + ('two',), np.zeros((n_time, n_nodes, n_z, 2), dtype=np.float32)),
             vertical_velocity=(dims3D, np.zeros((n_time, n_nodes, n_z), dtype=np.float32)),
             wetdry_elem=(('time', 'nSCHISM_hgrid_face'), np.zeros((n_time, n_faces), dtype=np.float32)),
             ),
        coords=dict(time=('time', np.arange(n_time) * 3600., dict(units='seconds since 2020-01-01 00:00:00'))))
    ds.to_netcdf(file_name)
    return x.mean(), y.mean()


@pytest.mark.validation
@pytest.mark.parametrize('regrid_z_to_sigma_levels', [True, False], ids=['sigma_levels', 'native_z'])
def test_well_mixed_column_stays_well_mixed_full_run(regrid_z_to_sigma_levels, tmp_path, default_run_output_dir):
    """the real profile with the strongest A_Z jumps, run through the solver, vertical cell finder, surface clipping
    and resuspension, which keep the column uniform to within a thin layer at the bed and free surface"""
    hours = 6
    zi, K, _ = _profile('demo_schism_node667')
    x_center, y_center = _write_still_water_schism_hindcast(path.join(tmp_path, 'still_water.nc'), zi, K, hours)

    ot = OceanTracker()
    ot.settings(run_output_dir=default_run_output_dir, time_step=10., debug=True,
                use_dispersion=True, use_A_Z_profile=True, write_tracks=True)
    ot.add_class('reader', input_dir=str(tmp_path), file_mask='still_water.nc',
                 regrid_z_to_sigma_levels=regrid_z_to_sigma_levels)
    ot.add_class('dispersion', A_H=0.)  # keep particles in the center of the grid
    ot.add_class('tracks_writer', update_interval=1800)
    ot.add_class('release_groups', name='column', points=[[x_center, y_center]], pulse_size=20_000,
                 release_interval=0, z_min=zi[0], z_max=zi[-1])
    case_info_file = ot.run()
    assert case_info_file is not None

    tracks = load_output_files.load_track_data(case_info_file)
    z = tracks['x'][:, :, 2]
    misplaced = _misplaced(z[z.shape[0] // 2:].ravel(), zi)
    print(f'full run, regrid_z_to_sigma_levels={regrid_z_to_sigma_levels}: misplaced {100 * misplaced:.1f}%')
    assert misplaced < MAX_MISPLACED, \
        f'{100 * misplaced:.1f}% of particles misplaced, column did not stay well-mixed'
