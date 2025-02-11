# demo05_parallel.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo05_parallel.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo05_parallel

# below only required for plotting
from read_oceantracker.python.load_output_files import load_stats_data, get_case_info_file_from_run_file
from plot_oceantracker.plot_statistics import plot_heat_map, animate_heat_map

output_file= "output\demo05_parallel"
# parallel run no plot
