# demo50_SCHISM_basic.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo50_SCHISM_basic.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo50_SCHISM_basic

# below only required for plotting

output_file= "output\demo50_SCHISM_basic"
