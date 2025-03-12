
import subprocess
import os
from oceantracker import  definitions
def main(args):


    python_file= os.path.join(definitions.package_dir,'run_ot_cmd_line.py')
    json_file= os.path.join(os.path.dirname(definitions.package_dir),'tests/unit_tests/test_param_files/params_unit_test_90_schism56_plots.json')

    os.system(f"python  {python_file}  {json_file}")