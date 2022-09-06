# demo09_polygon_release_overlapping_land.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_json\demo09_polygon_release_overlapping_land.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo09_polygon_release_overlapping_land

# below only required for plotting
from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
from oceantracker.post_processing.plotting.plot_tracks import animate_particles

output_file= "output\demo09_polygon_release_overlapping_land"

case_info_file_name = get_case_info_file_from_run_file(runInfo_file_name)

track_data = load_particle_track_vars(case_info_file_name)

animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                            heading='Polygon release 1) overlaping land, and 2) min 30m,  water depth',
                            movie_file=output_file + '.mp4' if output_file is not None else None,
                            show_grid=False,
                            fps=15, back_ground_depth=True, show_dry_cells=True, interval=50)
