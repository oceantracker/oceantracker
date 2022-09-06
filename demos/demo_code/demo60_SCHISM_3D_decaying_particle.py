# demo60_SCHISM_3D_decaying_particle.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_json\demo60_SCHISM_3D_decaying_particle.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo60_SCHISM_3D_decaying_particle

# below only required for plotting
from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
from oceantracker.post_processing.plotting.plot_tracks import animate_particles

output_file= "output\demo60_SCHISM_3D_decaying_particle"

case_info_file_name = get_case_info_file_from_run_file(runInfo_file_name)

track_data = load_particle_track_vars(case_info_file_name, var_list=['tide', 'water_depth', 'C'])

animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                            heading='SCHISIM reader, 3D, decaying particles, decay time 3.5 hrs',
                            colour_using_data=track_data['C'], part_color_map='hot_r',
                            size_using_data=track_data['C'],
                            vmax=1.0,
                            movie_file=output_file + '.mp4' if output_file is not None else None,
                            fps=24,
                            interval=20, show_dry_cells=True)
