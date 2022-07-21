from oceantracker.main import run_oceantracker
from oceantracker.user_post_processing import particle_plot
from oceantracker.user_post_processing import load_output_files
import oceantracker.util.basic_util  as basic_util
from os import path
from oceantracker.main import run_oceantracker
from oceantracker.user_post_processing import particle_plot
from oceantracker.user_post_processing import load_output_files
import oceantracker.util.basic_util  as basic_util
from os import path
import argparse


params={
    'shared_params' :{
                    "input_dir": "F:\\Hindcasts\\LaurinGermany",
                    "output_file_base": "debug",
                    "root_output_dir": "F:\\OceanTrackerOuput\\Laurin",
                    "debug": True,
                    "write_to_screen": True,
                    },
    "reader": {
        "class_name": "oceantracker.reader.schism_reader.SCHSIMreaderNCDF",
        "file_mask": "schout_*.nc",
        "depth_average": False,
        "load_depth_aver_vel": False
    },
    "base_case_params": {
        "run_params": {
            "duration": 3600*24*1,
            "particle_buffer_size": 1100,
        },
        "particle_release_groups": [
            {
                "class_name": "oceantracker.particle_release_groups.polygon_release.PolygonRelease",
                "points": [
                    [
                        593043,
                        5919010
                    ],
                    [
                        592988,
                        5919053
                    ],
                    [
                        592924,
                        5918944
                    ],
                    [
                        592981,
                        5918899
                    ]
                ],
                "pulse_size": 1000,
                "z_min": -1,
                "z_max": 1,
                "release_interval": 0
            }
        ]
    }
}

runInfo_file_name = run_oceantracker(params)

