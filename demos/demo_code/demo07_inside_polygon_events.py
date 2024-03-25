# demo07_inside_polygon_events.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo07_inside_polygon_events.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo07_inside_polygon_events

# below only required for plotting
from read_oceantracker.python.load_output_files import load_track_data, get_case_info_file_from_run_file, read_case_info_file
from plot_oceantracker.plot_tracks import animate_particles
from matplotlib import colors

output_file= "output\demo07_inside_polygon_events"

caseInfo = read_case_info_file(case_info_file_name)
track_data = load_track_data(case_info_file_name, var_list=['event_polygon'])

cmap = colors.ListedColormap(['b', 'm', 'y'])
animate_particles(track_data, colour_using_data=track_data['event_polygon'],
                                part_color_map=cmap,
                                axis_lims=[1591000, 1601500, 5478500, 5491000],
                                heading='Event logger, polygon aware particles',
                                vmin=-1,
                                vmax=1,
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=15,
                                polygon_list_to_plot=caseInfo['full_case_params']['roles_dict']['event_loggers']['in_out_poly']['polygon_list'],
                                show_dry_cells=True, interval=30)
