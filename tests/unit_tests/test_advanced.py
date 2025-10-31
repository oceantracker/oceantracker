from oceantracker.main import OceanTracker
import pytest


def test_regridding(
    base_settings,
    reader_schism3D,
    basic_point_release,
    schism_release_locations,
):

    ot = OceanTracker()
    ot.settings(**(base_settings | {"regrid_z_to_uniform_sigma_levels": True}))
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": schism_release_locations["deep_point"]},
    )
    # ot.add_class("particle_properties", **a_pollutant)
    # ot.add_class("particle_statistics", **my_heat_map_time)
    case_info_file = ot.run()

    assert case_info_file is not None


@pytest.mark.skip(reason="Not implemented yet")
def test_resuspension():
    assert True

@pytest.mark.skip(reason="Not implemented yet")
def test_stranding():
    assert True

@pytest.mark.skip(reason="Not implemented yet")
def test_backtracking():
    assert True

@pytest.mark.skip(reason="Not implemented yet")
def test_terminal_velocity():
    assert True

@pytest.mark.skip(reason="Not implemented yet")
def test_track_writer():
    assert True

@pytest.mark.skip(reason="Not implemented yet")
def test_settle_in_polygon():
    assert True

@pytest.mark.skip(reason="Not implemented yet")
def test_surface_float():
    assert True

@pytest.mark.skip(reason="Not implemented yet")
def test_split_particle():
    assert True

@pytest.mark.skip(reason="Not implemented yet")
def test_cull_particles():
    assert True

    
    # from oceantracker.read_output.python import load_output_files
    # tracks = load_output_files.load_track_data(case_info_file)
    # assert "a_pollutant" in tracks
    # assert tracks["a_pollutant"].max() <= 1000  # Should decay from initial value