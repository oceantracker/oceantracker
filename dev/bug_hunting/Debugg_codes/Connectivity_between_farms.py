# Code to estimate connectivity between mussel farms and potential spat collection areas
# Date: 08/11/2024
# HPC edition

# Protocol: release particles everyday from mussel farms during the reproductive season and advect them for 35 days. Settlement occurs after 21 days.
# Use the version 0.4_1 of Oceantracker

## Import packages ##
from oceantracker.main import OceanTracker
from oceantracker.util import yaml_util, cord_transforms
from os import path
import numpy as np
import argparse
import shapely.vectorized
from shapely.geometry import Point
from datetime import datetime
import geopandas as gpd # Need to be installed with pip command

## Model selection ##
ot = OceanTracker()
## Set basic settings ##
ot.settings(output_file_base =r'Connectivity_farms_GLM_OT_outputs',   # name used as base for output files
            #root_output_dir = '/hpcfreenas/romain/GM_connectivity_MBS',
            root_output_dir = r'D:\OceanTrackerOutput\bug_hunting',
            add_date_to_run_output_dir = True,
            # Run parameters
            backtracking = False,
            time_step = 200.0, # in seconds, time-step of interpolation
            # Parallel run
            processors=6, # Set up parallel run on x processors
            # Register outputs
            screen_output_time_interval = 3600*24, # Only print a line on screen once a day
            write_tracks = True,
            )

## Add reader for oceanographic data ##
if __name__ == '__main__':
    ot.add_class('reader',
                 #input_dir ='/hpcfreenas/hindcast/UpperSouthIsland/HABs2018benk/nogrowth',  # folder to search for hindcast files
                 input_dir = r'D:\Hindcasts\UpperSouthIsland\2018_benHABS\nogrowth',
                 # folder to search for hindcast files
                 file_mask = 'Nydia*.nc', # hindcast netcdf file
                 time_buffer_size = 20,
                 )
    
        ## Add physical properties ##
    ot.add_class('resuspension', critical_friction_velocity = 0.001) # only re-suspend particles if friction vel. exceeds this value
    ot.add_class('dispersion',
                 A_H = 0.2, # Horizontal diffusion coeff
                 A_V = 0.001, # Vertical diffusion coeff
                 )

    # Import polygons in Marlborough Sounds
    import json
    with open('Farms_MBS_GB_TB.geojson') as f:
        Marlb_polygons = json.load(f)
    polygon_list = list()
    for feature in Marlb_polygons['features']:
        polygon_coords = feature['geometry']['coordinates'][0][0]
        new_poly = dict(points=polygon_coords, user_polygonID=feature['properties']['id'])
        polygon_list.append(new_poly)

    for s_idx, s in enumerate(polygon_list[0:3], start=0):
        ot.add_class('release_groups', name = str(s_idx),                         # user must provide a name for group first
                    class_name = 'oceantracker.release_groups.polygon_release.PolygonRelease',
                    points = polygon_list[s_idx].get("points"),                               # must be an N by 2 or 3 or list, convertible to a numpy array
                    release_interval = 3600,        # seconds between releasing particles - in weeks currently
                    pulse_size = 10,                    # number of particles released each release_interval
                    start = datetime.strptime('01/02/2018', "%d/%m/%Y").isoformat(),
                    end = datetime.strptime('01/06/2018', "%d/%m/%Y").isoformat(),
                    max_age = 24*3600*35,
                    case = s_idx,
                    )

    ot.add_class('particle_statistics', name='Connectivity_matrix',
            class_name='oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_timeBased',
            start=datetime.strptime('01/02/2018', "%d/%m/%Y").isoformat(),
            end=datetime.strptime('01/08/2018', "%d/%m/%Y").isoformat(),
            polygon_list=polygon_list,
            min_age_to_bin = 21*24*3600,
            update_interval= 24 * 3600,
            case = s_idx,
            )


    ## Print parameters to check run ##
    print(ot.params)
    #import json
    #print(json.dumps(ot.params, indent=4))
    ## Run oceantracker ##
    # as helper "ot" has set params above, simply run it
    case_info_file_name = ot.run()
    print('case file name=', case_info_file_name)