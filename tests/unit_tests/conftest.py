import pytest
from os import path
from oceantracker import definitions
import numpy as np

# Constants can stay as module-level
package_dir = path.dirname(definitions.package_dir)
demo_hindcast_dir = path.join(package_dir, "tutorials_how_to", "demo_hindcast")
unittest_hindast_dir = path.join(package_dir, "tests","unit_tests","data","hindcasts")

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--create-reference",
        action="store_true",
        default=False,
        help="Create reference data for validation tests",
    )
    parser.addoption(
        "--create-plots",
        action="store_true",
        default=False,
        help="Create and save plots from test runs",
    )


@pytest.fixture
def create_reference_data_flag(request):
    """Flag to create reference data - set via command line or environment"""
    return request.config.getoption("--create-reference", default=False)


@pytest.fixture
def show_plots_flag(request):
    """Flag to create and save plots - set via command line"""
    return request.config.getoption("--create-plots", default=False)


@pytest.fixture
def default_root_output_dir():
    """Root directory for test outputs"""
    return path.join(path.dirname(package_dir), "oceantracker_output", "unit_tests")


@pytest.fixture
def reference_data_dir():
    """Directory for storing reference/validation data"""
    return path.join(path.dirname(__file__), "data", "output_data")


@pytest.fixture
def reader_demo_schism3D():
    return dict(
        input_dir=path.join(demo_hindcast_dir, "schsim3D"),
        file_mask="demo_hindcast_schisim3D*.nc",
    )

@pytest.fixture
def reader_schism3D():
    return dict(
        input_dir=path.join(unittest_hindast_dir, "schism3D"),
        file_mask="*.nc",
    )


@pytest.fixture
def reader_schism3D_v5():
    return dict(
        input_dir=path.join(unittest_hindast_dir, "schism3D_v5"),
        file_mask="*.nc",
    )


@pytest.fixture
def reader_schism2D():
    return dict(
        input_dir=path.join(unittest_hindast_dir, "schism2D"),
        file_mask="*.nc",
    )

@pytest.fixture
def reader_demo_roms():
    return dict(
        input_dir=path.join(demo_hindcast_dir, "ROMS"), file_mask="ROMS3D_00*.nc"
    )


@pytest.fixture
def base_settings(request, default_root_output_dir):
    """Base settings for OceanTracker tests"""
    # Get the test function name
    func_name = request.node.name
    return dict(
        output_file_base=func_name,
        root_output_dir=default_root_output_dir,
        time_step=1800,
        use_dispersion=False,
        write_tracks=False,
        regrid_z_to_uniform_sigma_levels=False,
    )


@pytest.fixture
def basic_point_release():
    return dict(
        name="basic",
        class_name="PointRelease",
        release_interval=1800,
        pulse_size=5,
    )


# @pytest.fixture
# def datetime_start_release_configuration():
#     """Release configuration with datetime start"""
#     return dict(
#         name="start_in_datetime1",
#         class_name="PointRelease",
#         start="2017-01-01T03:30:00",
#         release_interval=3600,
#         pulse_size=5,
#     )


@pytest.fixture
def downstream_point_release_configuration():
    return dict(
        name="downstream",
        class_name="DownstreamPointRelease",
        release_interval=1800,
        pulse_size=5,
        downstream_distance=10,
    )


@pytest.fixture
def polygon_release_configuration():
    return dict(
        name="my_polygon_release",
        class_name="PolygonRelease",
        release_interval=1800,
        pulse_size=2,
    )


@pytest.fixture
def grid_release_degrees():
    """Grid release for lat/lon in degrees"""
    return dict(
        name="my_grid_release",
        class_name="GridRelease",
        release_interval=1800,
        pulse_size=2,
        grid_span=[0.2, 0.2],
        grid_size=[3, 4],
    )


@pytest.fixture
def grid_release_meters():
    """Grid release for coordinates in meters"""
    return dict(
        name="my_grid_release",
        class_name="GridRelease",
        release_interval=1800,
        pulse_size=2,
        grid_span=[100, 100],
        grid_size=[3, 4],
    )


@pytest.fixture
def radius_release_meters():
    """Radius release for coordinates in meters"""
    return dict(
        name="my_radius_release",
        class_name="RadiusRelease",
        release_interval=1800,
        pulse_size=2,
        radius=100,
    )


@pytest.fixture
def schism3D_release_locations():
    return dict(
        point=[1594000, 5484200],
        multi_point=[
            [1594000, 5484200, -2],
            [1594100, 5485200, -2],
            [1593900, 5483200, -2],
            [1594000, 5484300, -2],
            [1593900, 5484100, -2],
        ],
        deep_point=[1594000, 5484200, -2],
        polygons=[
            {
                "points": [
                    [1597682, 5486972],
                    [1598604, 5487275],
                    [1598886, 5486464],
                    [1597917, 5484000],
                    [1597300, 5484000],
                    [1597682, 5486972],
                ]
            },
        ],
    )


@pytest.fixture
def schism2D_release_locations():
    return dict(
        point=[144.0824,-38.5238],
        deep_point=[144.0824,-38.5238,-2]
    )


@pytest.fixture
def schism3Dv5_release_locations():
    return dict(
        coastal_point=[175.05,-36.225],
        point=[175.1,-36.3],
        deep_point=[175.1,-36.3,-2],
        polygons=[
            {
                "points": [
                    [175.100000, -36.295508],
                    [175.105300, -36.298612],
                    [175.103276, -36.303634],
                    [175.096724, -36.303634],
                    [175.094700, -36.298612],
                ],
            },
        ],
    )


@pytest.fixture
def roms_release_locations():
    """ROMS demo release locations (US East Coast, lat/lon order)"""
    return dict(
        point=[-69.5, 43.5],
        multi_point=[
            [-69.5, 43.5],
            [-68.96, 44.1],
        ],
        
        polygons=[
            {
                "points": [
                    [-69.0, 43.5],
                    [-69.2, 43.5],
                    [-69.2, 43.7],
                    [-69.1, 43.7],
                    [-69.0, 43.5]
                ]
            }
        ]
        )


@pytest.fixture
def a_pollutant():
    """Pollutant particle property configuration"""
    return dict(
        name="a_pollutant",
        class_name="oceantracker.particle_properties.age_decay.AgeDecay",
        initial_value=1000,
        decay_time_scale=7200,
    )


@pytest.fixture
def gridded_2D_timeBased():
    """Heat map statistics configuration"""
    return dict(
        name="my_heatmap_time",
        class_name="GriddedStats2D_timeBased",
        grid_size=[120, 130],
        grid_span=[10000, 10000],
        release_group_centered_grids=True,
        update_interval=7200,
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def gridded_2D_ageBased():
    """Heat map statistics configuration"""
    return dict(
        name="my_heatmap_time",
        class_name="GriddedStats2D_ageBased",
        grid_size=[120, 130],
        grid_span=[10000, 10000],
        release_group_centered_grids=True,
        max_age_to_bin=1 * 24 * 3600,
        age_bin_size=7200,
        update_interval=3600,
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def gridded_3D_timeBased():
    """Heat map statistics configuration"""
    return dict(
        name="my_heatmap_time",
        class_name="GriddedStats3D_timeBased",
        grid_size=[120, 130, 10],
        grid_span=[10000, 10000],
        release_group_centered_grids=True,
        update_interval=7200,
        status_list=["moving"],
        z_max=-5.0,
        z_min=-10.0,
    )


@pytest.fixture
def gridded_2D_timeBased_runningMean():
    """Heat map statistics configuration"""
    return dict(
        name="my_heatmap_time",
        class_name="GriddedStats2D_timeBased_runningMean",
        grid_size=[120, 130],
        grid_span=[10000, 10000],
        write_interval=7200 * 3,
        release_group_centered_grids=True,
        update_interval=7200,
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def gridded_2D_timeBased_with_PartProp():
    """Heat map statistics configuration"""
    return dict(
        name="my_heatmap_time",
        class_name="GriddedStats2D_timeBased",
        grid_size=[120, 130],
        grid_span=[10000, 10000],
        release_group_centered_grids=True,
        update_interval=7200,
        particle_property_list=["a_pollutant", "water_depth"],
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def roms_gridded_2D_timeBased():
    """ROMS-specific heat map statistics configuration (smaller grid spans for lat/lon)"""
    return dict(
        name="my_heatmap",
        class_name="GriddedStats2D_timeBased",
        grid_size=[60, 121],
        grid_span=[1, 1.5],
        release_group_centered_grids=True,
        update_interval=7200,
        particle_property_list=["water_speed"],
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def polygon_stats_2D_timeBased():
    return dict(
        name="my_poly_stats_time",
        class_name="PolygonStats2D_timeBased",
        update_interval=7200,
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def polygon_stats_2D_ageBased():
    return dict(
        name="my_poly_stats_age",
        class_name="PolygonStats2D_ageBased",
        update_interval=7200,
        max_age_to_bin=1 * 24 * 3600,
        age_bin_size=7200,
        status_list=["moving"],
        z_min=-10.0,
    )


@pytest.fixture
def polygon_stats_timeBased_waterDepth():
    """Polygon statistics time-based configuration"""
    return dict(
        name="my_poly_stats_time",
        class_name="PolygonStats2D_timeBased",
        update_interval=3600,
        particle_property_list=["water_depth"],
    )
