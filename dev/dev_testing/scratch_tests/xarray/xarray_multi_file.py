from netCDF4 import Dataset as DatasetNCDF
import  xarray as xr
from oceantracker.util.ncdf_util import NetCDFhandler
from time import  perf_counter
from os import  path, listdir
from glob import glob
import numpy as np

def pre_process(ds):
    #ds.time.attrs['units'] = "seconds since 1990-1-1 0:0:0"
    return  ds

mask=r'G:\Hindcasts_large\2020_MalbroughSounds_10year_benPhD\\2008\schism_marl2008010*.nc'
mask=r'G:\Hindcasts_large\2020_MalbroughSounds_10year_benPhD\\2008\schism_marl2008010*.nc'
mask=r'F:\Hindcasts\2017_PortPeg2017HincastFull\PortPegHindcastCurrents\*.nc'
mask=r'F:\Hindcast_reader_tests\Schimsv5\WHOI_calvin\SCHISM_v2\*.nc'
mask= r'G:\Hindcasts_large\2024_hauraki_gulf_auck_uni\2020\**\*.nc'
#mask= r'F:\Hindcasts\2022_PortPhillipBay2020\HUY2020\schism\*.nc'

files= glob(mask,recursive=True)
print('numfiles=',len(files))

t0= perf_counter()
nc= xr.open_mfdataset(mask,coords =['time'],preprocess=pre_process,combine='by_coords',parallel=True, chunks=dict(time=24))
print('setup open_mfdataset', perf_counter()-t0)
nc['time'] = nc['time'].astype('datetime64[s]')
t=nc['time'].compute()
#nc.to_zarr(path.join(r'F:\temp\zarr_test',path.basename(fn).rsplit('.',)[0]))
nc.close()
print('read +setup open_mfdataset', perf_counter()-t0)
#print(t)
print(np.diff(t)/1e9)
print(t.values[0],'--', t.values[1],'-- ', t.values[-1])
print(np.any(np.diff(t)) < 0)
print(t.values)

pass