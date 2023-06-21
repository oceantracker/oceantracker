# demo03_heatmaps.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo03_heatmaps.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo03_heatmaps

# below only required for plotting
from oceantracker.post_processing.read_output_files.load_output_files import load_stats_data
from oceantracker.post_processing.plotting.plot_statistics import plot_heat_map, animate_heat_map

output_file= "output\demo03_heatmaps"


stats_data = load_stats_data(case_info_file_name)
axis_lims = [1591000, 1601500, 5478500, 5491000]
animate_heat_map(stats_data,'myP1', axis_lims=axis_lims,
                                heading='Particle count heatmaps built on the fly, no tracks recorded, log scale',
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=7)
plot_heat_map(stats_data,'myP1', axis_lims=axis_lims, var='water_depth', heading='Water depth built on the fly, no tracks recorded',
                             plot_file_name=output_file + '_water_depth.jpeg' if output_file is not None else None)
