# demo56_SCHISM_3D_resupend_crtitical_frictn_vel.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("../demo_param_files/demo56_SCHISM_3D_resupend_crtitical_frictn_vel.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo56_SCHISM_3D_resupend_crtitical_frictn_vel

# below only required for plotting

output_file= "output\demo56_SCHISM_3D_resupend_crtitical_frictn_vel"
