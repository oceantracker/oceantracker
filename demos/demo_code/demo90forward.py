# demo90forward.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_json\demo90forward.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo90forward

# below only required for plotting

output_file= "output\demo90forward"
