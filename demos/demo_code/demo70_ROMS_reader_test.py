# demo70_ROMS_reader_test.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo70_ROMS_reader_test.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo70_ROMS_reader_test

# below only required for plotting

output_file= "output\demo70_ROMS_reader_test"
