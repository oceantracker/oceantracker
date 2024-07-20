from netCDF4 import Dataset as DatasetNCDF
import  xarray as xr
from oceantracker.util.ncdf_util import NetCDFhandler
from time import  perf_counter
from os import  path, listdir
from glob import glob
mask=r'G:\Hindcasts_large\2020_MalbroughSounds_10year_benPhD\\2008\schism_marl2008010*.nc'


files= glob(mask,recursive=True)
print('numfiles=',len(files))

t0= perf_counter()
nc= xr.open_mfdataset(mask,coords =['time'])
t = nc['time'][:].compute()
t = nc['hvel'][:].compute()
#nc.to_zarr(path.join(r'F:\temp\zarr_test',path.basename(fn).rsplit('.',)[0]))
nc.close()
print('open_mfdataset', perf_counter()-t0)

t0= perf_counter()
for fn in files:
    nc= xr.open_dataset(fn,coords=['time'] )
    t = nc['time'][:].compute()
    t = nc['hvel'][:].compute()
    #nc.to_zarr(path.join(r'F:\temp\zarr_test',path.basename(fn).rsplit('.',)[0]))
    nc.close()
print('DatasetX', perf_counter()-t0)

t0= perf_counter()
for fn in files:
    nc= NetCDFhandler(fn)
    t = nc.read_a_variable('time').copy()
    t = nc.read_a_variable('hvel')[:].copy()
    nc.close()
print('NetCDFhandler', perf_counter()-t0)

t0= perf_counter()
for fn in files:
    nc= DatasetNCDF(fn)
    t = nc['time'][:].copy()
    t = nc['hvel'][:].copy()
    nc.close()
print('DatasetNCDF', perf_counter()-t0)

