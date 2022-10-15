# demo10_polygon_residence.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_json\demo10_polygon_residence.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo10_polygon_residence

# below only required for plotting

output_file= "output\demo10_polygon_residence"
