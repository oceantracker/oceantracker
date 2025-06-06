# demo01_plot_tracks.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo01_plot_tracks.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo01_plot_tracks

# below only required for plotting
from oceantracker.read_output.python import load_track_data
from oceantracker.plot_output.plot_tracks import plot_tracks

output_file= "output\demo01_plot_tracks"

track_data = load_track_data(case_info_file_name)
plot_tracks(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
             heading='Tracks, point release',
             plot_file_name=output_file + '.jpeg' if output_file is not None else None)
