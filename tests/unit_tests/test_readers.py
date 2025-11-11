from oceantracker.main import OceanTracker
import pytest



@pytest.mark.skip(reason="Not yet implemented")
def test_delft3D_2D():
    pass


@pytest.mark.skip(reason="Not yet implemented")
def test_delft3D_3D():
    pass


@pytest.mark.skip(reason="Not yet implemented")
def test_FVCOM_2D():
    pass


@pytest.mark.skip(reason="Not yet implemented")
def test_FVCOM_3D():
    pass


@pytest.mark.skip(reason="Not yet implemented")
def test_GLORYS_2D():
    """GLORYS/Nemo"""
    pass


@pytest.mark.skip(reason="Not yet implemented")
def test_GLORYS_3D():
    pass


@pytest.mark.skip(reason="Not yet implemented")
def test_FVCOM_3D():
    pass


def test_roms_3D(
    base_settings,
    reader_demo_ROMS,
    basic_point_release,
    roms_release_locations,
):
    """Test ROMS 3D grid tracking with multiple release types"""

    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_demo_ROMS)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": roms_release_locations["point"]},
    )
    # # Add polygon release
    # ot.add_class(
    #     "release_groups",
    #     **{
    #         **polygon_release_configuration,
    #         "points": roms_release_locations["polygon"],
    #     },
    # )

    # # Add grid release
    # ot.add_class(
    #     "release_groups",
    #     **{
    #         **grid_release_configuration,
    #         "grid_center": roms_release_locations["grid_center"],
    #     },
    # )

    # Add particle properties
    # ot.add_class("particle_properties", **a_pollutant)
    # ot.add_class(
    #     "particle_properties",
    #     name="water_speed",
    #     class_name="VectorMagnitude2D",
    #     vector_part_prop="water_velocity",
    # )
    # ot.add_class("particle_properties", class_name="DistanceTravelled")

    # # Add statistics
    # ot.add_class("particle_statistics", **roms_gridded_2D_timeBased)
    case_info_file = ot.run()

    assert case_info_file is not None



