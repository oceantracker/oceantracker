# demo56_SCHISM_3D_always_resupend.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_json\demo56_SCHISM_3D_always_resupend.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo56_SCHISM_3D_always_resupend

# below only required for plotting
from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
from oceantracker.post_processing.plotting.plot_tracks import animate_particles

output_file= "output\demo56_SCHISM_3D_always_resupend"

case_info_file_name = get_case_info_file_from_run_file(runInfo_file_name)

track_data = load_particle_track_vars(case_info_file_name, fraction_to_read=.9)
ax_lims= [1591000, 1601500, 5478500, 5491000]
animate_particles(track_data, axis_lims=ax_lims,
                  heading='SCHISIM 3D, fall velocity and always resuspend',
                  movie_file=output_file + '_status.mp4' if output_file is not None else None,
                  fps=15)

animate_particles(track_data, axis_lims=ax_lims,
                            colour_using_data=track_data['z'],
                            part_color_map='winter_r',
                            interval=200,
                            vmin=-20,
                            vmax=0,
                            heading='SCHISIM 3D, fall velocity and always resuspend, particles coloured by depth',
                            movie_file=output_file + '_depth.mp4' if output_file is not None else None,
                            fps=15, back_ground_depth=True)
