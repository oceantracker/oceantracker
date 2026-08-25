# shyfem3D — SHYFEM test hindcast, connectivity in the files

Small subset of the ISMAR-CNR EMERGE Adriatic sample `shyfem_unstructured_adriatic.nc`,
cut from a box off the Venice lagoon (12.30–12.95 E, 45.05–45.60 N):

    793 nodes, 1436 elements, 14 fixed z levels, 8 hourly time steps split over 2 files

This is the **easy path** for `SHYFEMreader`: the files keep `element_index`
(one based, `element` x `vertex`) and hold their nodes in natural order, so the reader
reads the triangulation straight out of the NetCDF. Some SHYFEM output really is like
this, eg the `shyfem_unstructured_adriatic*.nc` samples on the EMERGE THREDDS server.

Its companion `../shyfem3D_grd` holds the *same* grid and fields but forces the reader
to recover the triangulation from a `.grd` file instead, which is what the real EMERGE
hindcasts need. Because the two are physically identical, any difference in results is
down to the triangulation recovery alone — see `test_grd_and_element_index_give_the_same_tracks`
in `tests/unit_tests/test_shyfem_reader.py`.

Rebuild both with

    python tests/build_shyfem_unit_test_hindcasts.py --source <shyfem_unstructured_adriatic.nc>
