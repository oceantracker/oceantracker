'''Benchmarks used by dev_stats_performance_comparison.ipynb.

Runs one benchmark against one version of the oceantracker package and prints the result as json,
so each version is timed in its own fresh process, with its own numba compilation:

    python -I stats_performance_benchmarks.py <package_root> <benchmark> '<json params>'

<package_root> is a folder holding an "oceantracker" package folder, eg. one extracted from a git commit.
Numba threads are set by the caller with the environment variables
NUMBA_NUM_THREADS and OCEANTRACKER_USE_PARALLEL_THREADS (0 = serial compile, as with processors=1),
or for model runs by the "processors" param.
The result is the last line of stdout, starting with RESULT_JSON:
'''
import sys, json

package_root, bench_name, params = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
sys.path.insert(0, package_root)  # before any oceantracker import, so this version is used

import glob, hashlib, inspect
from os import path, makedirs
from time import perf_counter
import numpy as np


# ---------------------------------------------------------------- helpers

def time_call(f, reps):
    # first call includes numba compilation, then median of reps
    t0 = perf_counter(); f(); first = perf_counter() - t0
    ts = []
    for _ in range(reps):
        t0 = perf_counter(); f(); ts.append(perf_counter() - t0)
    return first, float(np.median(ts))


def digest(*arrays):
    # short hash of array values, to check versions give identical results
    h = hashlib.sha1()
    for a in arrays: h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()[:16]


def coastline_polygon(n_vertices, seed=0, roughness=0.35, center=(0., 0.), radius=1.):
    # coastline like polygon around a circle, by repeated midpoint displacement until it has n_vertices
    rng = np.random.default_rng(seed)
    th = np.linspace(0, 2 * np.pi, 16, endpoint=False)
    v = np.stack((np.cos(th), np.sin(th)), 1) * (1 + .15 * rng.standard_normal(16))[:, None]
    while v.shape[0] < n_vertices:
        nxt = np.roll(v, -1, 0)
        mid = (v + nxt) / 2
        d = nxt - v
        mid += np.stack((-d[:, 1], d[:, 0]), 1) * roughness * rng.standard_normal((v.shape[0], 1))
        v = np.stack((v, mid), 1).reshape(-1, 2)
    v = v[np.linspace(0, v.shape[0] - 1, n_vertices).astype(int)]
    return v * radius + np.asarray(center)


def square_tiles(n_side, vertices_per_tile, x0=0., y0=0., dx=1., dy=1.):
    # n_side x n_side touching, non-overlapping square polygons, edges subdivided to give vertices_per_tile vertices
    # shared edges have identical vertices in both tiles
    tiles = []
    n_edge = max(vertices_per_tile // 4, 1)
    for i in range(n_side):
        for j in range(n_side):
            c = np.array([[i, j], [i + 1, j], [i + 1, j + 1], [i, j + 1], [i, j]], float)
            v = np.concatenate([np.linspace(c[s], c[s + 1], n_edge, endpoint=False) for s in range(4)])
            tiles.append(v * [dx, dy] + [x0, y0])
    return tiles


def thread_info():
    import numba
    from oceantracker.util import numba_util
    return dict(numba_threads=numba.get_num_threads(), parallel_compile=bool(numba_util.compile_options['parallel']))


# ---------------------------------------------------------------- polygon benchmarks

def bench_inside_polygon(p):
    # InsidePolygon.inside_indices for one polygon, vertices x particles
    from oceantracker.util.polygon_util import InsidePolygon
    rows = []
    rng = np.random.default_rng(1)
    InsidePolygon(coastline_polygon(10))  # compile set up code, so setup_ms excludes it
    for nv in p['vertices']:
        v = coastline_polygon(nv)
        t0 = perf_counter(); P = InsidePolygon(v); setup = perf_counter() - t0
        b = P.polygon_bounds
        x_all = rng.uniform([b[0] - .15 * (b[1] - b[0]), b[2] - .15 * (b[3] - b[2])],
                            [b[1] + .15 * (b[1] - b[0]), b[3] + .15 * (b[3] - b[2])], (max(p['particles']), 2))
        out = np.zeros(x_all.shape[0], np.int32)
        for n in p['particles']:
            if n * nv > p.get('max_work', np.inf): continue  # skip cases too slow for the old version
            xq = x_all[:n]
            reps = p['reps'] if n * nv <= 10 ** 9 else 1  # slow cases of old version, one repeat
            first, t = time_call(lambda: P.inside_indices(xq, out=out), reps)
            inside = P.inside_indices(xq, out=out)
            rows.append(dict(vertices=nv, particles=n, ms=1e3 * t, first_call_s=first, setup_ms=1e3 * setup,
                             n_inside=int(inside.size), digest=digest(inside)))
    return dict(rows=rows)


def bench_which_polygon(p):
    # which of several non-overlapping polygons each particle is inside, as done by InsidePolygonsNonOverlapping2D.update()
    from oceantracker.util import polygon_util
    from oceantracker.util.polygon_util import InsidePolygon
    from oceantracker.particle_properties.util import particle_operations_util
    rows = []
    for n_poly in p['n_polygons']:
        n_side = int(round(np.sqrt(n_poly)))
        for nv in p['vertices_per_polygon']:
            polys = [InsidePolygon(v) for v in square_tiles(n_side, nv)]
            n = p['particles']
            xq = np.random.default_rng(2).uniform(-.1 * n_side, 1.1 * n_side, (n, 2))
            active = np.arange(n, dtype=np.int32)
            data = np.full(n, -99, np.int32)

            if hasattr(polygon_util, 'InsideWhichPolygon'):
                method = 'one parallel pass over particles (InsideWhichPolygon)'
                W = polygon_util.InsideWhichPolygon(polys)
                find = lambda: W.find(xq, active, data)
            else:
                method = 'one pass per polygon (inside_indices + set_value)'
                out = np.zeros(n, np.int32)
                def find():
                    # body of InsidePolygonsNonOverlapping2D.update() before 0d275a90
                    particle_operations_util.set_value(data, -1, active)
                    for k, P in enumerate(polys):
                        particle_operations_util.set_value(data, k, P.inside_indices(xq, active=active, out=out))

            first, t = time_call(find, p['reps'])
            rows.append(dict(n_polygons=n_side ** 2, vertices_per_polygon=nv, particles=n, ms=1e3 * t, first_call_s=first,
                             method=method, fraction_inside=float(np.mean(data >= 0)), digest=digest(data)))
    return dict(rows=rows)


def bench_overlap_check(p):
    # cost and results of the overlap check done when polygon stats are set up
    from oceantracker.util.polygon_util import InsidePolygon, find_overlapping_polygons, polygon_overlap_fraction
    rows = []
    for n_poly in p['n_polygons']:
        n_side = int(round(np.sqrt(n_poly)))
        polys = [InsidePolygon(v) for v in square_tiles(n_side, p['vertices_per_polygon'])]
        first, t = time_call(lambda: find_overlapping_polygons(polys, list(range(len(polys)))), 1)
        rows.append(dict(n_polygons=n_side ** 2, vertices_per_polygon=p['vertices_per_polygon'], ms=1e3 * t,
                         overlaps_found=len(find_overlapping_polygons(polys, list(range(len(polys)))))))

    sq = lambda x0, y0, w, h: np.array([[x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h]], float)
    cases = {'disjoint': (sq(0, 0, 1, 1), sq(2, 0, 1, 1), 0.),
             'shared edge': (sq(0, 0, 1, 1), sq(1, 0, 1, 1), 0.),
             'shared corner': (sq(0, 0, 1, 1), sq(1, 1, 1, 1), 0.),
             'half overlap': (sq(0, 0, 1, 1), sq(.5, 0, 1, 1), .5),
             'contained': (sq(0, 0, 2, 2), sq(0, 0, 1, 1), 1.),
             'identical': (sq(0, 0, 1, 1), sq(0, 0, 1, 1), 1.),
             'sliver 0.05% (below tolerance)': (sq(0, 0, 1, 1), sq(.9995, 0, 1, 1), .0005),
             'sliver 0.5% (above tolerance)': (sq(0, 0, 1, 1), sq(.995, 0, 1, 1), .005)}
    demo = [dict(case=k, true_fraction=f, estimated_fraction=float(polygon_overlap_fraction(InsidePolygon(a), InsidePolygon(b))),
                 reported_as_overlap=len(find_overlapping_polygons([InsidePolygon(a), InsidePolygon(b)], ['a', 'b'])) > 0)
            for k, (a, b, f) in cases.items()]
    return dict(rows=rows, demo=demo)


# ---------------------------------------------------------------- stats counting kernels

def _kernel_inputs(n, g, seed=0):
    rng = np.random.default_rng(seed)
    d = dict(
        x=np.stack((rng.uniform(-.05, 1.05, n), rng.uniform(-.05, 1.05, n), rng.uniform(-42, 2, n)), 1),
        group_ID=rng.integers(0, g['n_groups'], n).astype(np.int32),
        age=rng.uniform(-100, (g['age_bins'] + 1) * 3600., n),
        inside_polygons=rng.integers(-1, g['n_polygons'], n).astype(np.int32),
        status=rng.integers(-2, 3, n).astype(np.int8),
        props=[rng.random(n), rng.uniform(-5, 5, n), rng.random(n), rng.random(n)])
    d['sel'] = np.sort(rng.choice(n, int(.8 * n), replace=False)).astype(np.int32)  # those passing status etc. selection
    d['alive'] = np.sort(rng.choice(n, int(.9 * n), replace=False)).astype(np.int32)
    G, R, C = g['n_groups'], g['rows'], g['cols']
    d['x_edges'] = np.tile(np.linspace(0, 1, C + 1), (G, 1))
    d['y_edges'] = np.tile(np.linspace(0, 1, R + 1), (G, 1))
    d['spacings'] = np.array([1 / C, 1 / R])
    d['z_edges'] = np.linspace(-40, 0, g['layers'] + 1)
    d['age_edges'] = np.arange(0, (g['age_bins'] + 1) * 3600., 3600.)
    return d


def bench_stats_kernels(p):
    # the numba counting kernels of each stats class, plus the alive counts, on synthetic particles
    from numba.typed import List
    from oceantracker.particle_statistics.gridded_statistics2D import GriddedStats2D_timeBased, GriddedStats2D_ageBased
    from oceantracker.particle_statistics.gridded_statistics3D import GriddedStats3D_timeBased
    from oceantracker.particle_statistics.polygon_statistics import PolygonStats2D_timeBased, PolygonStats2D_ageBased
    from oceantracker.particle_statistics._base_stats_variants import _BaseTimeStats, _BaseAgeStats

    g = p['grid']
    G, R, C, L, A, NP = g['n_groups'], g['rows'], g['cols'], g['layers'], g['age_bins'], g['n_polygons']
    # kernel: (function, count array shape, args before the trailing particle ID buffers)
    kernels = {
        'gridded 2D time': (GriddedStats2D_timeBased._do_counts_and_summing_numba, (G, R, C),
                            lambda d, c, pl, sl: (d['group_ID'], d['x'], d['x_edges'], d['y_edges'], d['spacings'], c, pl, sl, d['sel'])),
        'gridded 2D age': (GriddedStats2D_ageBased._do_counts_and_summing_numba, (A, G, R, C),
                           lambda d, c, pl, sl: (d['group_ID'], d['x'], d['x_edges'], d['y_edges'], d['spacings'], c, pl, sl,
                                                 d['age_edges'], d['age'], d['sel'])),
        'gridded 3D time': (GriddedStats3D_timeBased._do_counts_and_summing_numba, (G, R, C, L),
                            lambda d, c, pl, sl: (d['group_ID'], d['x'], d['z_rel'], d['x_edges'], d['y_edges'], d['z_edges'], c, pl, sl, d['sel'])),
        'polygon time': (PolygonStats2D_timeBased._do_counts_and_summing_numba, (G, NP),
                         lambda d, c, pl, sl: (d['inside_polygons'], d['group_ID'], d['x'], c, pl, sl, d['sel'])),
        'polygon age': (PolygonStats2D_ageBased._do_counts_and_summing_numba, (A, G, NP),
                        lambda d, c, pl, sl: (d['inside_polygons'], d['group_ID'], d['x'], c, pl, sl, d['sel'], d['age_edges'], d['age'])),
        'alive count time': (_BaseTimeStats._count_all_alive_time, (G,),
                             lambda d, c, pl, sl: (d['status'], d['group_ID'], c, d['alive'])),
        'alive count age': (_BaseAgeStats._count_all_alive_age_bins, (A, G),
                            lambda d, c, pl, sl: (d['status'], d['group_ID'], d['age'], d['age_edges'], c, d['alive'])),
    }
    buffer_names = ('counted', 'counted_bins', 'alive_bins')  # trailing buffer args, some only in later versions

    rows, saved = [], {}
    for n in p['particles']:
        d = _kernel_inputs(n, g)
        d['z_rel'] = d['x'][:, 2].copy()
        for name in p['kernels']:
            f, shape, args = kernels[name]
            n_buffers = sum(a in buffer_names for a in inspect.signature(f.py_func).parameters)
            buffers = [np.zeros(n, np.int32) for _ in range(n_buffers)]
            for n_props in (p['props'] if not name.startswith('alive') else [0]):
                if n_props == 0:
                    pl = List([np.empty((1,))]); pl.pop(0)
                    sl = List([np.zeros((1,) * len(shape))]); sl.pop(0)
                    sums = []
                else:
                    sums = [np.zeros(shape) for _ in range(n_props)]
                    pl, sl = List(d['props'][:n_props]), List(sums)
                count = np.zeros(shape, np.int64)
                call = lambda: f(*args(d, count, pl, sl), *buffers)
                first, t = time_call(call, p['reps'])

                # results from one call from zero, as age based kernels accumulate over calls
                count[:] = 0
                for s in sums: s[:] = 0.
                counted = call()
                counted = np.asarray(counted) if counted is not None else np.zeros(0, np.int32)
                rows.append(dict(kernel=name, particles=n, props=n_props, ms=1e3 * t, first_call_s=first,
                                 n_counted=int(count.sum()), digest_counts=digest(count, counted),
                                 digest_sums=digest(*sums) if sums else None))
                if p.get('save_file') and n == max(p['particles']) and n_props == max(p['props']):
                    saved[f'{name}|count'] = count.copy()
                    for m, s in enumerate(sums): saved[f'{name}|sum{m}'] = s.copy()
    if saved: np.savez(p['save_file'], **saved)
    return dict(rows=rows)


# ---------------------------------------------------------------- model runs

# test hindcast in repo, SCHISM 3D, grid in meters (NZTM)
release_box = ([1593500, 5483500], [1598700, 5486800])
grid_center, span_x, span_y = [1596500, 5490000], 14000, 22000


def _scenario_stats(name, p):
    ui = p['update_interval']
    props = dict(particle_property_list=['water_depth', 'tide'])
    age = dict(max_age_to_bin=p['duration_h'] * 3600., age_bin_size=3600.)
    grid = dict(grid_center=grid_center, span_x=span_x, span_y=span_y, update_interval=ui)
    zones = [dict(name=f'zone{k:03d}', points=v.tolist()) for k, v in
             enumerate(square_tiles(5, 400, x0=1590000, y0=5480000, dx=2600, dy=4200))]
    connect = [dict(name=f'cell{k:03d}', points=v.tolist()) for k, v in
               enumerate(square_tiles(10, 200, x0=1590000, y0=5480000, dx=1300, dy=2100))]
    coast = [dict(name='coastline', points=coastline_polygon(p.get('coast_vertices', 20_000), center=grid_center, radius=6000).tolist())]

    g2t = lambda n, **kw: dict(name=n, class_name='GriddedStats2D_timeBased', rows=300, cols=200, **grid, **kw)
    g2a = lambda n, **kw: dict(name=n, class_name='GriddedStats2D_ageBased', rows=300, cols=200, **grid, **age, **kw)
    g3t = lambda n, **kw: dict(name=n, class_name='GriddedStats3D_timeBased', rows=100, cols=70, layers=20, z_min=-40., z_max=0., **grid, **kw)
    pt = lambda n, polys, **kw: dict(name=n, class_name='PolygonStats2D_timeBased', polygon_list=polys, update_interval=ui, **kw)
    pa = lambda n, polys, **kw: dict(name=n, class_name='PolygonStats2D_ageBased', polygon_list=polys, update_interval=ui, **age, **kw)

    scenarios = {
        'gridded 2D': [g2t('g2t')],
        'gridded 3D': [g3t('g3t')],
        'gridded + 2 props': [g2t('g2t', **props), g2a('g2a', **props), g3t('g3t', **props)],
        '25 polygon zones + 2 props': [pt('pt', zones, **props), pa('pa', zones, **props)],
        'connectivity, 100 polygons': [pt('pt', connect), pa('pa', connect)],
        'coastline polygon': [pt('pt', coast, **props)],
        'all stats types + 2 props': [g2t('g2t', **props), g2a('g2a', **props), g3t('g3t', **props),
                                      pt('pt', zones, **props), pa('pa', zones, **props)],
        'identical gridded instances': [dict(g2t(f'g2t_{k}'), rows=100, cols=100) for k in range(p.get('n_instances', 1))],
    }
    return scenarios[name]


def bench_model_run(p):
    # a short deterministic run of the test hindcast with the scenario's stats,
    # no dispersion, resuspension or random release locations, so versions can be compared exactly
    from oceantracker.main import OceanTracker
    from netCDF4 import Dataset

    stats = _scenario_stats(p['scenario'], p)
    (x0, y0), (x1, y1) = release_box
    points = [[x, y] for x in np.linspace(x0, x1, 40) for y in np.linspace(y0, y1, 40)]
    n_pulses = p['duration_h'] + 1  # hourly release, from start
    pulse_size = max(1, int(round(p['n_particles'] / (0.76 * len(points) * n_pulses))))  # ~76% of points are inside the domain

    ot = OceanTracker()
    ot.settings(run_output_dir=path.join(p['out_dir'], p['label']), output_file_base=p['label'], time_step=600,
                use_dispersion=False, use_resuspension=False, write_tracks=False,
                max_run_duration=p['duration_h'] * 3600., particle_buffer_initial_size=int(1.1 * p['n_particles']) + 10_000,
                processors=p.get('processors'))
    ot.add_class('reader', input_dir=p['hindcast_dir'], file_mask='*.nc')
    ot.add_class('release_groups', name='lattice', class_name='PointRelease', points=points,
                 pulse_size=pulse_size, release_interval=3600)
    for s in stats: ot.add_class('particle_statistics', **s)
    t0 = perf_counter(); case_info_file = ot.run(); wall = perf_counter() - t0
    if case_info_file is None: raise RuntimeError('model run failed, see log above')

    with open(case_info_file) as f: ci = json.load(f)
    timers = ci['update_timers']['particle_statistics']
    rows = []
    for s in stats:
        t = timers[s['name']]
        rows.append(dict(instance=s['name'], class_name=s['class_name'], update_calls=t['update_calls'],
                         total_s=t['time_spent_updating'], first_call_s=t['time_first_update_call'],
                         steady_s=t['time_spent_updating'] - t['time_first_update_call']))

    # stats output, for checking versions give the same results
    out = {}
    run_dir = path.dirname(case_info_file)
    for fn in sorted(glob.glob(path.join(run_dir, 'stats_*.nc'))):
        with Dataset(fn) as nc:
            for k, v in nc.variables.items():
                if k.startswith('count') or k.startswith('sum_'):
                    out[f'{path.basename(fn)}|{k}'] = np.ma.filled(v[:], -999)
    np.savez(path.join(run_dir, 'stats_outputs.npz'), **out)

    return dict(rows=rows, wall_s=wall, run_s=ci['run_info']['elapsed_time_sec'],
                particles_released=ci['run_info']['number_particles_released'],
                stats_outputs=path.join(run_dir, 'stats_outputs.npz'))


# ---------------------------------------------------------------- run

if __name__ == '__main__':
    t0 = perf_counter()
    result = dict(globals()[f'bench_{bench_name}'](params))
    import oceantracker
    result.update(thread_info(), package=path.dirname(oceantracker.__file__), bench_wall_s=perf_counter() - t0)
    print('RESULT_JSON: ' + json.dumps(result))
