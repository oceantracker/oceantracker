
import subprocess
import os
from oceantracker import  definitions
def main(args):


    python_file= os.path.join(definitions.package_dir,'run_ot_cmd_line.py')
    json_file= os.path.join(definitions.default_output_dir,'dev_runs/unit_test_90_schism56_plots_00/unit_test_90_schism56_plots_00_raw_user_params.json')

    os.system(f"python  {python_file}  {json_file}")