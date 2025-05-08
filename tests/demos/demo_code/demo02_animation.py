# demo02_animation.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo02_animation.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo02_animation

# below only required for plotting
from oceantracker.read_output.python import load_track_data
from oceantracker.plot_output.plot_tracks import animate_particles

output_file= "output\demo02_animation"

track_data = load_track_data(case_info_file_name, fraction_to_read=0.9)

animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],show_grid=True,
                            heading='3 hourly point and polygon releases with tidal stranding',
                            release_group=None,
                            movie_file=output_file + '.mp4' if output_file is not None else None,
                            fps=15, back_ground_depth=True, show_dry_cells=True, interval=20)
