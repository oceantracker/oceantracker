# demo100_LCS.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo100_LCS.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo100_LCS

# below only required for plotting

output_file= "output\demo100_LCS"
