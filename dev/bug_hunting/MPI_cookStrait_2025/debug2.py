# build parameters using helper class
from oceantracker.main import OceanTracker
import numpy as np
from oceantracker.util.json_util import write_JSON
import netCDF4 as nc
import pandas as pd
import math
import os
import shutil
import json


from pyproj import Transformer
EPSG_WGS84 = 4326
EPSG_NZTM  = 2193
_transformerNZTM_to_WGS84 = Transformer.from_crs(EPSG_NZTM , EPSG_WGS84, always_xy = True)
_transformerWGS84_to_NZTM = Transformer.from_crs(EPSG_WGS84, EPSG_NZTM , always_xy = True)

# Define the function to save the DataFrame back to the Excel file
def save_dataframe_to_excel(df, file_path):
    df.to_excel(file_path, index=False)
    print(f"DataFrame saved to {file_path}")

excelFile = r"C:\Users\malcolms\Cawthron\Cawthron Projects - Project Work\DepositionalModelling\oceantracker_penConfig1.xlsx"

excelFile = r"oceantracker_penConfig1.xlsx"

file_name = os.path.splitext(os.path.basename(excelFile))[0]

projectDir = r'E:\mpiSecretFishDeposition'
nProcessors = 30
outputDir = r'E:/mpiSecretFishDeposition/debug2/'
outputDir = r'D:\OceanTrackerOutput\bug_hunting'


# hindcast values
hindcastDir = r'U:\blueEndeavourNewModelNoDecay\outputs_non-decay'
hindcastMask = 'non-decay_*.nc'

hindcastDir = r'D:\Hindcast_parts\blueEndeavourHindcastForRV'
hindcastMask = 'non-*.nc'

# release and duration values
releaseStartDate = '2018-09-30T22:00:00' # '2018-09-01T00:30:00'

durationDays = 3 #*14 # this one shouldn't need changing but have put it here just in case.
timeStep = 60*20 #30 
releaseInterval = 3600 # once per hour
pulseSize = 10 #0 #100 # 10 particles per release interval per release point.

# grid specs
griddedStatsInterval = 24 * 3600 # once per day
gridDX = 50 # 50m was used for Blue Endeavour
gridLength = int(5000)
gridSize = int(gridLength / gridDX)

# dispersion
vertDispersionCoefficient = 0.001
horzDispersionCoefficient = 0.1

# decay rate calculation
halfLifeDays = 8 # 8 days
decayRateDays = -math.log(0.5)/halfLifeDays
decayRateSeconds = decayRateDays/(24*3600)
decayRateOceanTracker = 1/decayRateSeconds
maxAge = 7*halfLifeDays*(24*3600) # 7 half lives

# particle falling and resuspension properties
sinkRate_faeces = -0.032 
sinkRate_feed = -0.095 
resuspensionThreshold_faeces = 0.009 # taken from Law 2019
resuspensionThreshold_feed = 0.015 # taken from Law 2019
resuspensionThreshold_faeces_noResuspension = 10000000 # taken from Law 2019
resuspensionThreshold_feed_noResuspension = 10000000 # taken from Law 2019

pendf = pd.read_excel(excelFile)
nans_in_nztm_coords = pendf['lon_nztm'].isnull().any() + pendf['lon_nztm'].isnull().any()

if nans_in_nztm_coords > 0:
    print(f"Warning: NaNs found in 'lon_nztm' or 'lat_nztm' columns. Converting from wgs coordinates.")
    pendf.lon_nztm, pendf.lat_nztm = _transformerWGS84_to_NZTM.transform(pendf.lon_dd, pendf.lat_dd)
    still_nans_in_nztm_coords = pendf['lon_nztm'].isnull().any() + pendf['lon_nztm'].isnull().any()
    if still_nans_in_nztm_coords:
        print("Warning: NaNs still found in 'lon_nztm' or 'lat_nztm' columns. Check input data.")
        exit(1)
    else:
        print("Conversion successful.")
        # Save the DataFrame back to the Excel file
        save_dataframe_to_excel(pendf, excelFile)

# Get unique farm_ids
unique_farm_ids = pendf['farm_id'].unique()

# Create a dictionary to store DataFrames
farm_dfs = {farm_id: pendf[pendf['farm_id'] == farm_id] for farm_id in unique_farm_ids} #dictionary

farm_centroids = {} #dictionary
for farm_id, farm_df in farm_dfs.items():
    print(f"Accessing DataFrame for {farm_id}:")
    # Calculate the mean of lon_nztm and lat_nztm
    centroid_lon = farm_df['lon_nztm'].mean()
    centroid_lat = farm_df['lat_nztm'].mean()
    farm_centroids[farm_id] = (centroid_lon, centroid_lat)

# Display the centroids
for farm_id, centroid in farm_centroids.items():
    print(f"Centroid for {farm_id}: {centroid}")

otFaecesNR = OceanTracker() # make an instance of the helper class

# one or more settings can be set by calls to os.settings
otFaecesNR.settings(output_file_base= f'faecesNR_debug',# name used as base for output files
            root_output_dir= outputDir, #  output is put in dir   
            processors = nProcessors, # number of processors to use
            max_run_duration = 3600*24*durationDays, # 90 days
            time_step = timeStep,
            screen_output_time_interval= timeStep,
            regrid_z_to_uniform_sigma_levels=False,
            debug=True,
            write_tracks = False) #  NB This might need decreasing

# add a compulsory reader class
otFaecesNR.add_class('reader',
            input_dir= hindcastDir,  # folder to search for hindcast files, sub-dirs will, by default, also be searched
            file_mask = hindcastMask,    # the file mask of the hindcast files
            )

# Iterate through the DataFrame rows
for index, row in pendf.iterrows():
    otFaecesNR.add_class('release_groups',
                 name=f'faecesNR_{row["unique_id"]}',
                 points=[row['lon_nztm'], row['lat_nztm']],
                 release_interval=releaseInterval,
                 pulse_size=pulseSize,
                 release_radius=row['pen_radius'],
                 z_min=-row['pen_depth'],
                 z_max=1000,
                 max_age=maxAge,
                 start=releaseStartDate,
                 #duration=durationDays*24*3600,
                 user_release_group_name=f'faecesNR_{row["unique_id"]}')
    
#otFaecesNR.add_class('interpolator',  max_search_steps=2000)

# fall velocity is a velocity modifier class
otFaecesNR.add_class('velocity_modifiers',
                name ='fall_velocity',
                class_name = 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity',
                value = sinkRate_faeces, # mean terminal vel < 0 for falling
                # optionally variance can also be use to give each particles its own fall velocity
            )


# otFaecesNR.add_class('particle_properties',
#                 name = 'mass',
#                 class_name= 'oceantracker.particle_properties.age_decay.AgeDecay',
#                 initial_value = 1, # initial value of the property
#                 # the below settings are optional                   
#                 )

## creating individual farm heat maps using farm centroids
for farm_id, farm_centroid in farm_centroids.items():
    otFaecesNR.add_class('particle_statistics',
                 name=f'heatMap_{farm_id}',
                 class_name='oceantracker.particle_statistics.gridded_statistics2D.GriddedStats2D_timeBased',
                 # Optional settings
                 update_interval=griddedStatsInterval,  # Time interval in sec, between doing particle statistics counts
                 #status_list = ['on bottom'],

                 # release_group_centered_grids=True,
                 grid_center=list(farm_centroid),  # The center of the heat map
                 grid_size=[gridSize, gridSize],
                 grid_span=[gridLength, gridLength])

# alter default re-suspension class's default settings
otFaecesNR.add_class('resuspension', critical_friction_velocity = resuspensionThreshold_faeces_noResuspension) # only re-suspend particles if friction vel. exceeds this value
otFaecesNR.add_class('dispersion', A_V = vertDispersionCoefficient , A_H = horzDispersionCoefficient)

# run oceantracker
otFaecesNR.run()