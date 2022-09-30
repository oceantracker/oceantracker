# demo05_parallel.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_json\demo05_parallel.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo05_parallel

# below only required for plotting
from oceantracker.post_processing.read_output_files.load_output_files import load_stats_file, get_case_info_file_from_run_file
from oceantracker.post_processing.plotting.plot_statistics import plot_heat_map, animate_heat_map

output_file= "output\demo05_parallel"
# parallel run no plot
