"""Build the small SHYFEM hindcasts used by tests/unit_tests/test_shyfem_reader.py

Cuts a small box out of the EMERGE Adriatic sample file and writes two variants

    shyfem3D/       keeps "element_index", so the reader gets its triangulation from the files
    shyfem3D_grd/   "element_index" removed and the nodes shuffled, with a companion ".grd"
                    file, so the reader has to match grd nodes to file nodes by coordinate,
                    which is what the EMERGE 2018/2019 hindcasts need

Run with
    python tests/build_shyfem_unit_test_hindcasts.py --source <shyfem_unstructured_adriatic.nc>
"""

import argparse
from os import path, makedirs

import numpy as np
import xarray as xr

FILL = -999.0
OUT_DIR = path.join(path.dirname(path.abspath(__file__)), 'unit_tests', 'data', 'hindcasts')

# a small box in the north Adriatic, off the Venice lagoon
BOX = dict(lon=(12.30, 12.95), lat=(45.05, 45.60))
N_TIME = 8
VARS_3D = ['u_velocity', 'v_velocity', 'temperature', 'salinity']


def subset(source, box, n_time):
    ds = xr.open_dataset(source, decode_times=False)
    lon, lat = ds.longitude.values, ds.latitude.values

    in_box = ((lon >= box['lon'][0]) & (lon <= box['lon'][1])
              & (lat >= box['lat'][0]) & (lat <= box['lat'][1]))

    tri = ds.element_index.values - 1  # file is one based
    keep_element = np.all(in_box[tri], axis=1)
    tri = tri[keep_element, :]
    if tri.shape[0] == 0:
        raise ValueError('box contains no complete elements')

    # keep only nodes actually used by the kept elements, so there are no orphans
    nodes = np.unique(tri)
    renumber = np.full(lon.size, -1, dtype=np.int64)
    renumber[nodes] = np.arange(nodes.size)
    tri = renumber[tri].astype(np.int32)

    # drop levels that are entirely below the sea bed, as "cdo sellonlatbox" does
    depth = ds.total_depth.values[nodes]
    level = ds.level.values
    n_levels = int(np.searchsorted(level, depth.max(), side='left') + 1)
    n_levels = min(n_levels, level.size)

    out = dict(nodes=nodes, triangles=tri, n_levels=n_levels, n_time=n_time,
               level=level[:n_levels], time=ds.time.values[:n_time],
               time_attrs=ds.time.attrs, longitude=lon[nodes], latitude=lat[nodes],
               total_depth=depth, attrs=ds.attrs,
               water_level=ds.water_level.values[:n_time, :][:, nodes])

    for name in VARS_3D:
        data = ds[name].values[:n_time, :, :n_levels][:, nodes, :]
        # mark below the sea bed with the fill value the EMERGE hindcasts use.
        # a layer holds data when its *top* is above the bed, so the layer the bed
        # falls inside is kept, which is what the SHYFEM output does
        layer_top = np.concatenate(([0.0], level[:n_levels - 1]))
        below_bed = layer_top[np.newaxis, :] >= depth[:, np.newaxis]
        data[:, below_bed] = FILL
        out[name] = data.astype(np.float32)

    ds.close()
    return out


def write_hindcast(sub, out_dir, with_element_index, shuffle_nodes, n_files=2):
    makedirs(out_dir, exist_ok=True)

    order = np.arange(sub['nodes'].size)
    if shuffle_nodes:
        order = np.random.default_rng(3).permutation(order)
    inverse = np.empty_like(order)
    inverse[order] = np.arange(order.size)  # old node index -> new node index

    n_per_file = int(np.ceil(sub['n_time'] / n_files))
    file_names = []
    for f in range(n_files):
        nt = slice(f * n_per_file, min((f + 1) * n_per_file, sub['n_time']))
        if nt.start >= sub['n_time']:
            break

        data_vars = dict(
            longitude=(('node',), sub['longitude'][order].astype(np.float32),
                       dict(standard_name='longitude', units='degrees_east')),
            latitude=(('node',), sub['latitude'][order].astype(np.float32),
                      dict(standard_name='latitude', units='degrees_north')),
            total_depth=(('node',), sub['total_depth'][order].astype(np.float32),
                         dict(standard_name='sea_floor_depth_below_sea_surface', units='m',
                              description='total depth at nodes')),
            water_level=(('time', 'node'), sub['water_level'][nt, :][:, order].astype(np.float32),
                         dict(standard_name='water_surface_height_above_reference_datum', units='m',
                              _FillValue=FILL, missing_value=FILL)),
        )
        for name in VARS_3D:
            data_vars[name] = (('time', 'node', 'level'), sub[name][nt, :, :][:, order, :],
                               dict(_FillValue=FILL, missing_value=FILL))
        if with_element_index:
            data_vars['element_index'] = (('element', 'vertex'),
                                          (inverse[sub['triangles']] + 1).astype(np.int32))

        ds = xr.Dataset(
            data_vars=data_vars,
            coords=dict(
                time=(('time',), sub['time'][nt], sub['time_attrs']),
                level=(('level',), sub['level'].astype(np.float32),
                       dict(standard_name='depth', long_name='depth_below_sea', units='m',
                            positive='down', axis='Z', description='bottom of vertical layers')),
            ),
            attrs=dict(sub['attrs'], title='SHYFEM unit test hindcast',
                       comment='small subset of the ISMAR-CNR EMERGE Adriatic sample, for testing only'),
        )
        name = path.join(out_dir, f'shyfem_test_{f:02d}.nc')
        ds.to_netcdf(name, encoding={k: dict(zlib=True, complevel=5) for k in data_vars})
        file_names.append(name)

    return file_names, inverse


def write_grd_file(sub, file_name):
    """Write a SHYFEM ".grd" for the subset, using sparse node numbers as real grid files do."""
    n_nodes = sub['nodes'].size
    node_numbers = (np.arange(n_nodes) * 3 + 7).astype(np.int64)  # deliberately not 1..n
    with open(file_name, 'w') as f:
        f.write('0 unit test grid, subset of the EMERGE Adriatic SHYFEM grid\n\n')
        for i in range(n_nodes):
            f.write(f'1 {node_numbers[i]} 0 {sub["longitude"][i]:.6f} {sub["latitude"][i]:.6f}\n')
        f.write('\n')
        for e, tri in enumerate(sub['triangles']):
            n = node_numbers[tri]
            f.write(f'2 {e + 1} 2 3 {n[0]} {n[1]} {n[2]} 1.000000\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, help='shyfem_unstructured_adriatic.nc')
    ap.add_argument('--out-dir', default=OUT_DIR)
    args = ap.parse_args()

    sub = subset(args.source, BOX, N_TIME)
    print(f'subset: {sub["nodes"].size} nodes, {sub["triangles"].shape[0]} elements, '
          f'{sub["n_levels"]} levels, {sub["n_time"]} time steps')

    files, _ = write_hindcast(sub, path.join(args.out_dir, 'shyfem3D'),
                              with_element_index=True, shuffle_nodes=False)
    print('wrote', files)

    grd_dir = path.join(args.out_dir, 'shyfem3D_grd')
    files, _ = write_hindcast(sub, grd_dir, with_element_index=False, shuffle_nodes=True)
    write_grd_file(sub, path.join(grd_dir, 'shyfem_test_grid.grd'))
    print('wrote', files, 'plus shyfem_test_grid.grd')


if __name__ == '__main__':
    main()
