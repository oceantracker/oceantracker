# demo59_crit_shear_resupension.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo59_crit_shear_resupension.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo59_crit_shear_resupension

# below only required for plotting
from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
from oceantracker.post_processing.plotting.plot_vertical_tracks import plot_path_in_vertical_section

output_file= "output\demo59_crit_shear_resupension"

track_data = load_particle_track_vars(case_info_file_name, var_list=['tide', 'water_depth'])

plot_path_in_vertical_section(track_data, title='Fall velocity, critical friction velocity  resuspension ',
                                                   plot_file_name=output_file +  '_section.jpeg' if output_file is not None else None)
