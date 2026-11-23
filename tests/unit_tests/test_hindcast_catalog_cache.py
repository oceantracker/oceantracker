"""Hindcast catalog cache, reader parameter "hindcast_catalog_cache_file".

The first run catalogs the hindcast files and writes the catalog to the cache file,
later runs read the cache instead of opening every file. A run using the cache must
set up the reader and track particles exactly as a run that cataloged the files itself.
"""
import json
from glob import glob, escape
from os import path

import numpy as np
import pytest
import xarray as xr

from oceantracker.main import OceanTracker
from oceantracker.field_group_manager import get_file_info

# (reader fixture, release locations fixture, key of the release point in it)
READERS = [
    ("reader_schism3D", "schism3D_release_locations", "deep_point"),
    ("reader_schism2D", "schism2D_release_locations", "point"),
    ("reader_schism3D_v5", "schism3Dv5_release_locations", "deep_point"),
    ("reader_GLORYS3D", "GLORYS3D_release_locations", "deep_point"),
    ("reader_ROMS3Dsigma", "roms_release_locations", "point"),
]

# keys only the cached catalog has, used to rebuild the file times as xarray on reading the cache
CACHE_ONLY_FILE_INFO_KEYS = ("time_dim", "time_attr")


def _run(base_settings, reader, release, run_output_dir, cache_file):
    ot = OceanTracker()
    ot.settings(**{**base_settings,
                   "run_output_dir": run_output_dir,
                   "write_tracks": True,
                   "max_run_duration": 6 * 3600,
                   })
    ot.add_class("reader", **reader, hindcast_catalog_cache_file=cache_file)
    ot.add_class("release_groups", **release)
    case_info_file = ot.run()
    assert case_info_file is not None, f"run failed, see {run_output_dir}"


def _read_reader_info(run_output_dir):
    with open(path.join(run_output_dir, "reader_info_000.json")) as f:
        info = json.load(f)
    for fi in info["file_info"]:
        for key in CACHE_ONLY_FILE_INFO_KEYS:
            fi.pop(key, None)
    return info


def _read_tracks(run_output_dir):
    # escape, as parametrized test names in the output dir have "[...]"
    track_files = glob(path.join(escape(run_output_dir), "tracks*.nc"))
    assert len(track_files) == 1, f"expected one tracks file in {run_output_dir}, found {track_files}"
    with xr.open_dataset(track_files[0]) as ds:
        return {name: ds[name].values for name in ds.data_vars}


@pytest.mark.parametrize("reader_fixture, locations_fixture, location_key", READERS)
def test_cached_catalog_reproduces_run(request, monkeypatch, tmp_path, base_settings, basic_point_release,
                                       default_run_output_dir, reader_fixture, locations_fixture, location_key):
    reader = request.getfixturevalue(reader_fixture)
    release = {**basic_point_release, "points": request.getfixturevalue(locations_fixture)[location_key]}

    # cache file in a dir that does not exist yet, which writing the cache must create
    cache_file = str(tmp_path / "catalog_cache" / "hindcast_catalog.json")

    # count how often the hindcast files are cataloged
    n_catalogs_built = []
    build_hindcast_info = get_file_info.build_hindcast_info

    def counting_build_hindcast_info(*args, **kwargs):
        n_catalogs_built.append(1)
        return build_hindcast_info(*args, **kwargs)

    monkeypatch.setattr(get_file_info, "build_hindcast_info", counting_build_hindcast_info)

    # first run, no cache yet, so catalogs the files and writes the cache
    built_dir = path.join(default_run_output_dir, "catalog_built")
    _run(base_settings, reader, release, built_dir, cache_file)
    assert len(n_catalogs_built) == 1
    assert path.isfile(cache_file), "cache file was not written"
    cache_modified = path.getmtime(cache_file)

    # second run reads the cache, without cataloging the files or rewriting the cache
    cached_dir = path.join(default_run_output_dir, "catalog_cached")
    _run(base_settings, reader, release, cached_dir, cache_file)
    assert len(n_catalogs_built) == 1, "files were cataloged again although the cache file exists"
    assert path.getmtime(cache_file) == cache_modified, "existing cache file was rewritten"

    # same reader setup
    assert _read_reader_info(cached_dir) == _read_reader_info(built_dir)

    # same particle tracks
    built_tracks = _read_tracks(built_dir)
    cached_tracks = _read_tracks(cached_dir)
    assert built_tracks.keys() == cached_tracks.keys()
    for name in built_tracks:
        np.testing.assert_array_equal(cached_tracks[name], built_tracks[name], err_msg=f'track variable "{name}"')
