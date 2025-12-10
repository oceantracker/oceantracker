from oceantracker.main import OceanTracker
import pytest

from tests.unit_tests.conftest import reader_schism3D, schism3D_release_locations



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


def test_GLORYS3D(
    base_settings,
    reader_GLORYS3D,
    basic_point_release,
    GLORYS3D_release_locations,
):

    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_GLORYS3D)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": GLORYS3D_release_locations["point"]},
    )
    case_info_file = ot.run()

    assert case_info_file is not None


@pytest.mark.skip(reason="Not yet implemented")
def test_FVCOM_3D():
    pass


def test_schism3D(
    base_settings,
    reader_schism3D,
    basic_point_release,
    schism3D_release_locations,
):
    """Test ROMS 3D grid tracking with multiple release types"""

    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_schism3D)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": schism3D_release_locations["point"]},
    )
    case_info_file = ot.run()

    assert case_info_file is not None


def test_schism3D_v5(
    base_settings,
    reader_schism3D_v5,
    basic_point_release,
    schism3Dv5_release_locations,
):
    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_schism3D_v5)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": schism3Dv5_release_locations["point"]},
    )
    case_info_file = ot.run()

    assert case_info_file is not None


def test_schism2D(
    base_settings,
    reader_schism2D,
    basic_point_release,
    schism2D_release_locations,
):
    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_schism2D)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": schism2D_release_locations["point"]},
    )
    case_info_file = ot.run()

    assert case_info_file is not None

def test_roms_3D(
    base_settings,
    reader_demo_roms,
    basic_point_release,
    roms_release_locations,
):
    ot = OceanTracker()
    ot.settings(**base_settings)
    ot.add_class("reader", **reader_demo_roms)
    ot.add_class(
        "release_groups",
        **{**basic_point_release, "points": roms_release_locations["point"]},
    )
    case_info_file = ot.run()

    assert case_info_file is not None



