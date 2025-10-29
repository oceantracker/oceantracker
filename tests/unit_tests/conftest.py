import pytest
from os import path
from oceantracker import definitions
import numpy as np

# Constants can stay as module-level
package_dir = path.dirname(definitions.package_dir)
demo_hindcast_dir = path.join(package_dir, "tutorials_how_to", "demo_hindcast")

@pytest.fixture
def default_root_output_dir():
    """Root directory for test outputs"""
    return path.join(
        path.dirname(package_dir), "oceantracker_output", "unit_tests"
    )

@pytest.fixture
def reader_demo_schisim3D():
    """Demo SCHISM 3D reader configuration"""
    return dict(
        input_dir=path.join(demo_hindcast_dir, "schsim3D"),
        file_mask="demo_hindcast_schisim3D*.nc",
    )

@pytest.fixture
def reader_demo_ROMS():
    """Demo ROMS reader configuration"""
    return dict(
        input_dir=path.join(demo_hindcast_dir, "ROMS"), 
        file_mask="ROMS3D_00*.nc"
    )

@pytest.fixture
def base_settings(request, default_root_output_dir):
    """Base settings for OceanTracker tests"""
    # Get the test function name
    func_name = request.node.name
    return dict(
        output_file_base=func_name,
        root_output_dir=default_root_output_dir,
    )

@pytest.fixture
def basic_point_release_configuration():
    return dict(
        name="basic",
        class_name="PointRelease",
        release_interval=1800,
        pulse_size=5,
    )

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
def schism_release_locations():
    return dict(
        multi_point=[
            [1594000, 5484200, -2], # center point
            # the following have a 100m offset 
            [1594100, 5485200, -2], # north point
            [1593900, 5483200, -2], # south point
            [1594000, 5484300, -2], # east point
            [1593900, 5484100, -2], # west point
        ],
        deep_point=[1594000, 5484200, -2],
        deep_polygon=[
            [1597682, 5486972],
            [1598604, 5487275],
            [1598886, 5486464],
            [1597917, 5484000],
            [1597300, 5484000],
            [1597682, 5486972],
        ],
    )

@pytest.fixture
def schism_poly_release_location():
    """SCHISM demo polygon release locations"""
    return dict(
    )

@pytest.fixture
def a_pollutant():
    """Pollutant particle property configuration"""
    return dict(
        name="a_pollutant",
        class_name="oceantracker.particle_properties.age_decay.AgeDecay",
        initial_value=1000,
        decay_time_scale=7200.0,
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
def gridded_2D_timeBased_runningMean():
    """Heat map statistics configuration"""
    return dict(
        name="my_heatmap_time",
        class_name="GriddedStats2D_timeBased_runningMean",
        grid_size=[120, 130],
        grid_span=[10000, 10000],
        write_interval=7200*3,
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