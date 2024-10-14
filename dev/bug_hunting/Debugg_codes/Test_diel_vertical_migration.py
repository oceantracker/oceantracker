# Code to reproduce Ben's experiment in Nydia Bay to estimate propagation of the HABSs.
# Date: 14/11/2023
# HPC edition

# Protocol: release on scheduled sampling days (~5-7days) and track particles for 7 days to give connectivity at 7 days, then track at 14 days to get connectivity at 14 days.
# Particles released from every bay where HABs have been detected
# Concentrations from Phyto-mon A.pac countsonly.RV01.xslx
# Constant release of particles
# Use the version 0.4 of Oceantracker

## Import packages ##
from oceantracker.main import OceanTracker
from oceantracker.util import yaml_util, cord_transforms
from os import path
import numpy as np
import argparse
import shapely.vectorized
from shapely.geometry import Point
import geopandas as gpd # Need to be installed with pip command


## Create a loop to extract all Mondays of the year 2018
# Connectivity matrix to be plotted every week of a year
from datetime import date, timedelta, datetime
def allmondays(year):
    d = datetime(year, 1, 1)                              # January 1st
    d += timedelta(days = (0 - d.weekday() + 7) % 7)  # First Monday (Monday = 0 and Sunday = 6)
    while d.year == year:
        yield d
        d += timedelta(days = 7)
# Create list of Mondays
list_dates = list()
for d in allmondays(2018):
    list_dates.append(d)

## Model selection ##
ot = OceanTracker()
## Set basic settings ##
ot.settings(output_file_base ='test_OVM', #+ i.isoformat("_", "hours"),       # name used as base for output files
            #root_output_dir ='//CCL-AKL-STORE01.cawthron.org.nz/Malcolm$/Romain_storage/HABS_modelling_experiment/Oceantracker_outputs',  # Root directory to store outputs
            add_date_to_run_output_dir = False,
            # Run parameters
            backtracking = False,
            time_step = 200.0, # in seconds, time-step of interpolation
            # Parallel run
            processors=1, # Set up parallel run on x processors
            # Register outputs
            #case_output_file_tag = "date",
            screen_output_time_interval = 3600*24, # Only print a line on screen once a day
            #write_output_files = True,
            write_tracks = False,
            max_run_duration = 3600*24*3, # max runtime is 7 days (easier for output processing)
            )

## Add reader for oceanographic data ##
if __name__ == '__main__':
    ot.add_class('reader',
                 input_dir ='//CCL-AKL-STORE01.cawthron.org.nz/Malcolm$/Romain_storage/HABS_modelling_experiment/nestfiles_HABs/April',  # folder to search for hindcast files
                 file_mask = 'Nydia*.nc', # hindcast netcdf file
                 #max_numb_files_to_load = 4,
                 time_buffer_size = 6,
                 )

    ot.add_class('velocity_modifiers',
                 class_name = 'diel_vertical_migration.DielVerticalMigration',
                 vertical_swimming_speed = 1.0,
                 vertical_position_daytime = -10.0,
                 vertical_position_nighttime = -0.1,
                 start = 1.0,
                 )

    # Create parallel runs on dates
    for idx, i in enumerate(list_dates[13:14], start=13):  # Only April to June for 2018
        ## Add release groups ##
        # Set release times
        release_start_date = i
        release_end_date = list_dates[idx] + timedelta(days = 1)
        end_run_date = list_dates[idx] + timedelta(days = 2)

        # Import polygons in Marlborough Sounds
        import json
        with open('Entire_marlb_polygons.geojson') as f:
            Marlb_polygons = json.load(f)
        polygon_list= list()
        for feature in Marlb_polygons['features']:
            polygon_coords = feature['geometry']['coordinates'][0][0]
            new_poly = dict(points= polygon_coords, user_polygonID=feature['properties']['CLUSTER_ID'])
            polygon_list.append(new_poly)

        for s_idx, s in enumerate(polygon_list[0:10], start=0):
            # Isolate i polygon
            release_polygon =  polygon_list[s_idx]["points"]
            ot.add_class('release_groups',
                     name = str(s_idx+1),
                     class_name = 'oceantracker.release_groups.polygon_release.PolygonRelease',  # use a polygon release
                     points = release_polygon,         # must be an N by 2 or 3 or list, convertible to a numpy array
                     pulse_size = 1,                   # number of particles released each release_interval
                     start = release_start_date.isoformat(),
                     end = release_end_date.isoformat(),
                     max_age = 2 * 24 * 3600.,         # maximum tracking duration for connectivity (7 days)
                     release_interval = 3600.*1,       # seconds between releasing particles
                     z_min = -15,                      # min depth of release
                     case = s_idx,                       # necessary to run cases in parallel!
                     )

        ## Add physical properties ##
        ot.add_class('resuspension', critical_friction_velocity = 0.001) # only re-suspend particles if friction vel. exceeds this value
        ot.add_class('dispersion',
                     class_name= 'oceantracker.dispersion.random_walk.RandomWalk',
                     A_H = 0.2, # Horizontal diffusion coeff
                     A_V = 0.001, # Vertical diffusion coeff
                     )

    ## Add output properties ##
    #ot.add_class('tracks_writer',
    #             update_interval = 24 * 3600., # Time in seconds between output writes (will be rounded to model time step)
    #             turn_on_write_particle_properties_list =["n_cell"], # Write index of cell at each time step (used for plotting concentration fields)
    #             )

    ## Print parameters to check run ##
    print(ot.params)
    #import json
    #print(json.dumps(ot.params, indent=4))

    ## Run oceantracker ##
    # as helper "ot" has set params above, simply run it
    case_info_file_name = ot.run()
    print('case file name=', case_info_file_name)