# demo58_bottomBounce.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo58_bottomBounce.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo58_bottomBounce

# below only required for plotting
from oceantracker.post_processing.read_output_files.load_output_files import load_track_data, get_case_info_file_from_run_file
from oceantracker.post_processing.plotting.plot_tracks import animate_particles
from oceantracker.post_processing.plotting.plot_vertical_tracks import plot_path_in_vertical_section, plot_relative_height

output_file= "output\demo58_bottomBounce"

track_data = load_track_data(case_info_file_name, var_list=['tide', 'water_depth'])

plot_path_in_vertical_section(track_data,  title= 'fall velocity and resuspension with critical friction velocity ',
                                      plot_file_name=output_file +  '_section.jpeg' if output_file is not None else None)

plot_relative_height(track_data, title='fall velocity, always resuspension_jump ')
plot_relative_height(track_data, title='fall velocity, always resuspension_jump ', bottom=False)

animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000], heading='vertical section tracks')
