# demo91_free_running_gaps.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("F:\H_Local_drive\ParticleTracking\oceantracker\dev\demos\build_and_test_demos.py\demo_param_files\demo91_free_running_gaps.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo91_free_running_gaps

# below only required for plotting

output_file= "output\demo91_free_running_gaps"
