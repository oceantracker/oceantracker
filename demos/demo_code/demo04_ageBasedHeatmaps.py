# demo04_ageBasedHeatmaps.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo04_ageBasedHeatmaps.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo04_ageBasedHeatmaps

# below only required for plotting
from read_oceantracker.python.load_output_files import load_stats_data, get_case_info_file_from_run_file
from plot_oceantracker.plot_statistics import plot_heat_map, animate_heat_map

output_file= "output\demo04_ageBasedHeatmaps"



stats_data = load_stats_data(case_info_file_name,name='age_grid')
axis_lims = [1591000, 1601500, 5478500, 5491000]
animate_heat_map(stats_data,'myP1', axis_lims=axis_lims,
                                heading='Particle count heatmaps built on the fly, no tracks recorded, log scale',
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=7)
