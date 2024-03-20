# demo62_polygon_release_overlapping_land.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo62_polygon_release_overlapping_land.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo62_polygon_release_overlapping_land

# below only required for plotting
from read_oceantracker.python.load_output_files import load_track_data, get_case_info_file_from_run_file
from plot_oceantracker.plot_tracks import animate_particles

output_file= "output\demo62_polygon_release_overlapping_land"


track_data = load_track_data(case_info_file_name)

animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                            heading='Polygon release 1) overlaping land, and 2) min 30m,  water depth',
                            movie_file=output_file + '.mp4' if output_file is not None else None,
                            show_grid=False,
                            fps=15, back_ground_depth=True, show_dry_cells=True, interval=50)
