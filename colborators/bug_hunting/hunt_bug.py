from oceantracker import main
from oceantracker.util import json_util
ncase=0
import multiprocessing
import numpy
import numba

if ncase ==0:
    fn = r'E:\OneDrive - Cawthron\H_Local_drive\ParticleTracking\bug_hunting\paramsBWDFY20120.json'
    params = json_util.read_JSON(fn)
    params['reader']['input_dir'] = r'G:\Hindcasts_large\OceanNumNZ-2022-06-20\final_version\2012'
    params['shared_params']['root_output_dir'] = r'F:\OceanTrackerOuput\bug_hunting'
    params['case_list'] =  params['case_list'][23:25]



def test(l):
    print(l)

def run() :
    with multiprocessing.Pool(processes=3) as pool:
        case_results = pool.map(test, l)

if __name__ == '__main__':

    main.run(params)
    l = list(range(4))
    #run()

