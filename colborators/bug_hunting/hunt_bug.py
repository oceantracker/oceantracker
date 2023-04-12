from oceantracker import main
from oceantracker.util import json_util
ncase=0

if ncase ==0:
    fn = r'F:\OceanTrackerOuput\bug_hunting\bwdFY2012\paramsBWDFY20120.json'
    params = json_util.read_JSON(fn)
    params['reader']['input_dir'] = r'G:\Hindcasts_large\OceanNumNZ-2022-06-20\final_version\2010'
    params['shared_params']['root_output_dir'] = r'F:\OceanTrackerOuput\bug_hunting'
    params['case_list'] =  params['case_list'][23:25]

main.run(params)
