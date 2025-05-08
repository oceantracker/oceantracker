# demo00_helper_class_test.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo00_helper_class_test.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo00_helper_class_test

# below only required for plotting

output_file= "output\demo00_helper_class_test"
