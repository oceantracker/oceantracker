import numpy as np
import xarray as xr
from os import  path
from glob import glob
from netCDF4 import Dataset
from time import perf_counter
from numba import njit

@njit
def step(nt,xin,xout):
    for n in range(xout.shape[0]):
        xout[n] = xin[nt,-1,1]-xin[nt,-1,0]

if __name__ == "__main__":

    input_dir= '../../../demos/demo_hindcast'
    file_mask = 'demoHindcast2D*.nc'
    vars=['time_sec']
    #\\demoH*.hc
    input_dir ='G:\\hindcasts\\marl_hindcast_BenPhd_2019ver\\2008'
    file_mask = 'schism_marl2008*.nc'
    vars = ['time']

    files= glob(path.join(input_dir,file_mask))
    nc= Dataset(files[0])
    nc.close()
    d2 = xr.open_mfdataset(path.join(input_dir,file_mask), concat_dim='time', combine = 'by_coords',  cache =True,
                          data_vars=['hvel'], compat =  "override", coords='minimal')
    print('starting')

    N = d2['time'].shape[0]-1
    a=np.full((N,),0.)
    t0=perf_counter()
    for nt in range(N):
        #a[:,:]= d2['hvel'][nt,:,:,0] -d2['hvel'][nt,:,:,1]
        step(nt,np.asarray(d2['hvel']), a)
        if nt % 1000 : print(100.*nt/N, (perf_counter()-t0)/60)
    print( perf_counter()-t0)
    a=1
    a=1
