# %% [markdown]
# ## Preparation

# %%
from oceantracker.main import run
from oceantracker.post_processing.read_output_files import load_output_files
from oceantracker.post_processing.plotting import plot_tracks
from oceantracker.post_processing.plotting import plot_statistics

import os
import numpy as np
import matplotlib.pyplot as plt

# %% [markdown]
# ### Model

# %%
model_name = "shit_predictor_2000_debug"

# I/O
input_dir = "/hpcfreenas/hindcast/OceanNumNZ-2022-06-20/final_version/2019/"
output_dir = "/hpcfreenas/laurin/malcolms_marvelous_shit_predictor_output"

# time parameters
model_duration = 60*24*3600
data_time_step = 3600
model_time_step = 60
model_steps = int(model_duration/model_time_step)

# particle release
pulse_size = 10
release_interval = 3600

# output
# i think there is no good reason to have the output step size
# smaller then the model step size though.
output_time_step = model_time_step
output_steps = int(model_duration/output_time_step)
grid_size = 100


# %% [markdown]
# ### Flux

# %%
# feed
feed_input_per_year_per_pen = 2.214e3

feed_sinking_velocity = 0.095
feed_decay_rate = 0.086/(24*3600) # per day
feed_critical_friction_velocity = 0.015

feed_water_ratio = 0.09
feed_digestion_ratio = 0.85
feed_waste_ratio = 0.03

# shit

shit_sinking_velocity = 0.032
shit_decay_rate = 0.086/(24*3600) # per day
shit_critical_friction_velocity = 0.009

# fluxes
feed_mass_dry = (1-feed_water_ratio)*feed_input_per_year_per_pen
feed_consumed = (1-feed_waste_ratio)*feed_mass_dry
feed_wasted = feed_waste_ratio*feed_mass_dry

shit_produced = (1-feed_digestion_ratio)*feed_consumed

flux_feed = feed_wasted
flux_shit = shit_produced

#
pulses_per_year = int(3600*24*365/release_interval)
inital_mass_per_pertical = 1/(pulse_size*pulses_per_year)

initial_feed_particle_mass = flux_feed*inital_mass_per_pertical
initial_shit_particle_mass = flux_shit*inital_mass_per_pertical



# %% [markdown]
def create_case_dict_for_pen(pen_position,depth_range,
                             pulse_size=pulse_size,
                             release_interval=release_interval,
                             feed_sinking_velocity=feed_sinking_velocity,
                             feed_decay_rate=feed_decay_rate,
                             shit_sinking_velocity=shit_sinking_velocity,
                             shit_decay_rate=shit_decay_rate):
    """
    Takes a list of [x_min,x_max,y_min,y_max] for the pen_position
    and a list of [z_top,z_bottom] for the depth_range and returns a
    dict
    """
    x_min,x_max,y_min,y_max = pen_position
    z_top,z_bottom = depth_range

    case = [
        # food pellets
        {
            "particle_release_groups": [
                {
                    "class_name": "oceantracker.release_groups.polygon_release.PolygonRelease",
                    "points": [
                        [
                            x_min,
                            y_min
                        ],
                        [
                            x_max,
                            y_min
                        ],
                        [
                            x_max,
                            y_max
                        ],
                        [
                            x_min,
                            y_max
                        ]
                    ],
                    "pulse_size": pulse_size,
                    "release_interval": release_interval,
                    "z_range": [z_top, z_bottom]
                }
            ],
            "velocity_modifiers": [
                {
                    "class_name": "oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity",
                    "mean": feed_sinking_velocity
                }
            ],
            "particle_properties": [
                {
                    "class_name": "oceantracker.particle_properties.age_decay.AgeDecay",
                    "decay_time_scale": 1/feed_decay_rate
                }
            ],
            "trajectory_modifiers": [
                {
                    "class_name": "oceantracker.resuspension.BasicResuspension",
                    "critical_friction_velocity": feed_critical_friction_velocity
                }
            ],
        },
        # shit pellets
        {
            "particle_release_groups": [
                {
                    "class_name": "oceantracker.release_groups.polygon_release.PolygonRelease",
                    "points": [
                        [
                            x_min,
                            y_min
                        ],
                        [
                            x_max,
                            y_min
                        ],
                        [
                            x_max,
                            y_max
                        ],
                        [
                            x_min,
                            y_max
                        ]
                    ],
                    "pulse_size": pulse_size,
                    "release_interval": release_interval,
                    "z_range": [z_top, z_bottom]
                }
            ],
            "velocity_modifiers": [
                {
                    "class_name": "oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity",
                    "mean": shit_sinking_velocity
                }
            ],
            "particle_properties": [
                {
                    "class_name": "oceantracker.particle_properties.age_decay.AgeDecay",
                    "decay_time_scale": 1/shit_decay_rate
                }
            ],
            "trajectory_modifiers": [
                {
                    "class_name": "oceantracker.resuspension.BasicResuspension",
                    "critical_friction_velocity": shit_critical_friction_velocity
                }
            ],
        }
    ]

    return case

# %%
list_of_pens = [
    {
        "name": "pen_1",
        "pen_position": [
            1689853, # x_min
            1697645, # x_max
            5476738, # y_min
            5491327  # y_max
        ],
        "depth_range": [0, -30]
    }
]

# %%
params = {
    "shared_params": {
        "compact_mode": True,
        "output_file_base": model_name,
        "root_output_dir": output_dir,
        "processors": 1,
    },
    "reader": {
        "class_name": "oceantracker.reader.schism_reader.SCHISMreaderNCDF",
        "depth_average": False,
        "file_mask": "NZfinite*.nc",
        "input_dir": input_dir,
        "search_sub_dirs": True,
        # "hgrid_file_name": "/hpcfreenas/hindcast/OceanNumNZ-2022-06-20/final_version/hgridNZ_run.gr3",
    },
    "base_case_params": {
        "dispersion": {
            "A_H": 0.1,
            "A_V": 0.001
        },
        "fields": [
            {
                "class_name": "oceantracker.fields.friction_velocity.FrictionVelocityFromNearSeaBedVelocity"
            }
        ],
        "run_params": {
            "block_dry_cells": True,
            "open_boundary_type": 1,
            "write_tracks": True,
            "duration": model_duration,
        },
        "solver": {
            "n_sub_steps": int(data_time_step/model_time_step),
            "screen_output_step_count": int(data_time_step/model_time_step)
        },
        "tracks_writer": {
            "class_name": "oceantracker.tracks_writer.track_writer_compact.FlatTrackWriter",
            "output_step_writer": 3600,
            "write_dry_cell_flag": True
        },
        "particle_statistics": [
            {
                "class_name": "oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased",
                "calculation_interval": output_time_step,
                "count_status_in_range": ["on_bottom", "on_bottom"],
                "particle_property_list": [
                    "age_decay"
                ],
                "grid_size": [
                    grid_size,
                    grid_size
                ]

            }
        ],
    },
}

cases = []
for pen in list_of_pens:
    case = create_case_dict_for_pen(pen["pen_position"],
                                    pen["depth_range"])
    cases.append(case[0])
    cases.append(case[1])

params["case_list"] = cases

# %% [markdown]
# ## Run Model

# %%
print('Estimated output data size per case')
print('-----------------------------------')

print(f'\t{output_steps*grid_size**2*8*3/1024**3:.1f} GB')



time_per_particle_per_time_step = 2e-5
releases = model_duration/release_interval
time_steps_between_releases = release_interval/model_time_step

active_particles_per_time_step = np.array([0])
for ii in range(int(releases)):
    active_particles_per_time_step= np.append(active_particles_per_time_step,
               [active_particles_per_time_step[-1] + pulse_size]*int(time_steps_between_releases))

estimated_run_time = np.sum(active_particles_per_time_step*time_per_particle_per_time_step) #\wo io

print('Estimated compute time per case')
print('-----------------------------------')
print(f'\t{estimated_run_time/60/60:.0f}h')




# %%
path_to_output = os.path.join(
    os.path.abspath(os.path.curdir),
    params['shared_params']['root_output_dir'],
    params['shared_params']['output_file_base'],
    params['shared_params']['output_file_base']+'_runInfo.json')

# %%
try:
    load_output_files.get_case_info_file_from_run_file(path_to_output)
except:
    path_to_output = run(params)[0]

# %% [markdown]
# ## Post-Processing

# %% [markdown]
# ### Checking decay

# %%
decay = 0.087

t = np.arange(0, 3600*24*60, 3600*24)

x = np.exp(-t*feed_decay_rate)

plt.figure()
plt.plot(t/3600/24,x)
plt.grid(True, which="both")
plt.hlines(0.01, 0, 60, linestyles='dashed')


# %% [markdown]
# ### Feed

# %%
# loading feed case
case = load_output_files.get_case_info_file_from_run_file(path_to_output, ncase = 1)

# deposition in the model duration
stats_data = load_output_files.load_stats_data(case,nsequence=0)

# %%
# shit unit masses present at time step at cell on bottom
feed_unit_masses_present = stats_data['sum_age_decay']#['time', 'pen', 'x', 'y']
feed_unit_masses_present[np.isnan(feed_unit_masses_present)] = 0

# scale this with the gauge mass per particle
feed_present = feed_unit_masses_present * initial_shit_particle_mass

# calculate how much of this has decayed in this time step on bottom
feed_decayed = feed_present * feed_decay_rate * model_time_step

# %%
print(f"Total feed input into system: {feed_mass_dry:.2f} kg/a")
print(f"Total feed not consumed: {flux_feed:.2f} kg/a")
print(f"Total feed decayed on bottom (\wo equilibrium adjustment): {np.sum(feed_decayed):.2f} kg/a")
print(f"Total feed decayed on bottom (\w  equilibrium adjustment): {np.sum(np.sum(feed_decayed[-1,0]*feed_decayed.shape[0])):.2f} kg/a")

# %%
plt.imshow(np.max(stats_data['sum_age_decay'][:,0,:,:],axis=(0)))
plt.colorbar()

# %% [markdown]
# ### Shit

# %%
# load shit case
case = load_output_files.get_case_info_file_from_run_file(path_to_output, ncase = 2)

# deposition in the model duration
stats_data = load_output_files.load_stats_data(case, var_list=['age_decay'], nsequence=0)

# %%
# shit unit masses present at time step at cell on bottom
shit_unit_masses_present = stats_data['count']#['time', 'pen', 'x', 'y']
shit_unit_masses_present[np.isnan(shit_unit_masses_present)] = 0

# scale this with the gauge mass per particle
shit_present = shit_unit_masses_present * initial_shit_particle_mass

# calculate how much of this has decayed in this time step on bottom
shit_decayed = shit_present * shit_decay_rate * model_time_step

# %%
print(f"Total feed input into system: {feed_mass_dry:.2f} kg/a")
print(f"Total shit input into system: {flux_shit:.2f} kg/a")
print(f"Total shit decayed on bottom (\wo equilibrium adjustment): {np.sum(shit_decayed):.2f} kg/a")
print(f"Total shit decayed on bottom (\w  equilibrium adjustment): {np.sum(np.sum(shit_decayed[-1,0]*shit_decayed.shape[0])):.2f} kg/a")


# %%
plt.imshow(np.sum(shit_decayed[:,0,:,:],axis=0))
plt.colorbar(label="Shit decayed on bottom (kg/a)")