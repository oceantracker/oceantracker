# shyfem3D_grd — SHYFEM test hindcast, connectivity only in a ".grd" file

Holds the **same** grid and fields as `../shyfem3D` — same 793 nodes, 1436 elements,
14 fixed z levels and 8 hourly time steps, cut from the same box off the Venice lagoon
out of the ISMAR-CNR EMERGE sample `shyfem_unstructured_adriatic.nc`. Only the way the
reader can obtain the triangulation differs.

This variant reproduces what the real EMERGE 2018/2019 hindcasts look like, with three
deliberate obstacles:

1. **`element_index` is removed.** The real files were post processed with
   `ncks -C -x -v ... element_index`, visible in their `history` attribute, so the
   triangulation is simply not in them.
2. **The file nodes are shuffled** into a different order from the `.grd` (seeded
   permutation, so it is reproducible). The 2019 hindcast is a `cdo sellonlatbox`
   subset, which reorders and renumbers nodes. This defeats any positional shortcut
   and forces `map_grd_nodes_to_dataset_nodes` down its coordinate matching branch.
   Note an exact match cannot be used there: the `.grd` holds 6 decimal text while the
   files hold float32, so the two disagree in the last digit for many nodes.
3. **`shyfem_test_grid.grd` uses sparse node numbers** (7, 10, 13, ...), so elements
   refer to node *numbers* rather than indices and a lookup table is needed. Real SHYFEM
   grids do this too — `adri_lags_175776.grd` numbers 96389 nodes up to 141241.

Point the reader at it with the `grd_file_name` parameter

    ot.add_class('reader', input_dir=..., file_mask='*.nc',
                 grd_file_name='.../shyfem_test_grid.grd')

Leaving `grd_file_name` out is also a test case: the run must fail with a message naming
`element_index`, see `test_missing_triangulation_is_a_clear_error`.

Rebuild both with

    python tests/build_shyfem_unit_test_hindcasts.py --source <shyfem_unstructured_adriatic.nc>
