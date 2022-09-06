# demo07_inside_polygon_events.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_json\demo07_inside_polygon_events.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo07_inside_polygon_events

# below only required for plotting
from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file, read_case_info_file
from oceantracker.post_processing.plotting.plot_tracks import animate_particles
from matplotlib import colors

output_file= "output\demo07_inside_polygon_events"

case_info_file_name = get_case_info_file_from_run_file(runInfo_file_name)
caseInfo = read_case_info_file(case_info_file_name)
track_data = load_particle_track_vars(case_info_file_name, var_list=['event_polygon'])

cmap = colors.ListedColormap(['b', 'm', 'y'])
animate_particles(track_data, colour_using_data=track_data['event_polygon'],
                                part_color_map=cmap,
                                axis_lims=[1591000, 1601500, 5478500, 5491000],
                                heading='Event logger, polygon aware particles',
                                vmin=-1,
                                vmax=1,
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=15,
                                polygon_list_to_plot=caseInfo['full_params']['event_loggers'][0]['polygon_list'],
                                show_dry_cells=True, interval=30)
