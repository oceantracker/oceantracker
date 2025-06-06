# demo10_polygon_residence_demo.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo10_polygon_residence_demo.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo10_polygon_residence_demo

# below only required for plotting
from oceantracker.read_output.python import load_track_data,load_residence_file
from oceantracker.plot_output.plot_tracks import animate_particles
from oceantracker.plot_output.plot_statistics import plot_residence

output_file= "output\demo10_polygon_residence_demo"

residence_data = load_residence_file(case_info_file_name)
plot_residence(residence_data, heading='Number residence in release polygon demo',
               plot_file_name=output_file + '.jpeg' if output_file is not None else None)

track_data = load_track_data(case_info_file_name, fraction_to_read=0.9)
animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],show_grid=True,
                            heading='Residence in release polygon counts demo',
                            release_group=None,
                            movie_file=output_file + '.mp4' if output_file is not None else None,
                            fps=15, back_ground_depth=True, show_dry_cells=True, interval=20)

