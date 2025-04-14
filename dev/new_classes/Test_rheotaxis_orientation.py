# Code to test rheotaxis orientation
# Date: 16/12/2024

# Use the version 0.4 of Oceantracker

## Import packages ##
from oceantracker.main import OceanTracker
from datetime import datetime

## Model selection ##
ot = OceanTracker()
## Set basic settings ##
ot.settings(output_file_base ='test_rheotaxis',      # name used as base for output files
            root_output_dir = r'E:\OceanTracker_simulations_outputs_temp\Fish_larvae_orientation_tests',
            add_date_to_run_output_dir = False,
            # Run parameters
            backtracking = False,
            time_step = 200.0, # in seconds, time-step of interpolation
            # Parallel run
            processors=1, # Set up parallel run on x processors
            # Register outputs
            screen_output_time_interval = 3600*24, # Only print a line on screen once a day
            #write_output_files = True,
            write_tracks = True,
            max_run_duration = 3600*24*7,
            )

## Add reader for oceanographic data ##
if __name__ == '__main__':
    ot.add_class('reader',
                 input_dir ='//CCL-AKL-STORE01.cawthron.org.nz/Malcolm$/Romain_storage/HABS_modelling_experiment/nestfiles_HABs/April',  # folder to search for hindcast files
                 file_mask = 'Nydia*.nc', # hindcast netcdf file
                 #max_numb_files_to_load = 4,
                 time_buffer_size = 6,
                 )

    ## Development of new module
    ot.add_class('velocity_modifiers',
                 class_name = 'rheotaxis_orientation.RheotaxisOrientation',
                 horizontal_swimming_speed_hatch = 1.0,
                 horizontal_swimming_speed_settle = 50.0,
                 start_orientation = 1 * 3600,
                 PLD = 7 * 3600 * 24,
                 Lambda = 100,
                 station_holding = False,
                 )

    ot.add_class('release_groups',
                     class_name = 'oceantracker.release_groups.point_release.PointRelease',
                     points = [1669083.0, 5443558.5],  # must be an N by 2 or 3 or list, convertible to a numpy array
                     pulse_size = 100,                  # number of particles released each release_interval
                     start = datetime.strptime('02/04/2018', "%d/%m/%Y").isoformat(),
                     end = datetime.strptime('02/04/2018', "%d/%m/%Y").isoformat(),
                     max_age = 7 * 24 * 3600.,         # maximum tracking duration for connectivity (7 days)
                     #release_interval = 3600.*2,       # seconds between releasing particles
                     z_min = -1,                      # min depth of release
                     )

    ## Print parameters to check run ##
    print(ot.params)

    ## Run oceantracker ##
    # as helper "ot" has set params above, simply run it
    case_info_file_name = ot.run()
    print('case file name=', case_info_file_name)


# plot animation of results
from oceantracker.plot_output.plot_tracks import animate_particles
from oceantracker.read_output.python import load_output_files

# read particle track data into a dictionary using case_info_file_name
tracks = load_output_files.load_track_data(case_info_file_name)
#print('tracks data', tracks_plot.keys())

anim = animate_particles(tracks,show_dry_cells=True, show_grid=True, show=True) # use ipython to show video, rather than matplotlib plt.show()


# this is slow to build!
#HTML(anim.to_html5_video())