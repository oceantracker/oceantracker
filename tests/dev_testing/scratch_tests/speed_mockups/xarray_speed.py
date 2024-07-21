from netCDF4 import Dataset as DatasetNCDF
import  xarray as xr
from oceantracker.util.ncdf_util import NetCDFhandler
from time import  perf_counter
from os import  path, listdir
from glob import glob
mask=r'G:\Hindcasts_large\2020_MalbroughSounds_10year_benPhD\\2008\schism_marl2008010*.nc'
#mask= r'F:\Hindcasts\2022_PortPhillipBay2020\HUY2020\schism\*.nc'
#mask=r'F:\Hindcasts\2017_PortPeg2017HincastFull\PortPegHindcastCurrents\*.nc'
#mask=r'G:\Hindcasts_large\2024_OceanNumNZ-2022-06-20\final_version\**\*.nc'
mask= r'G:\Hindcasts_large\2024_hauraki_gulf_auck_uni\2020\**\*.nc'
mask=r'E:\H_Local_drive\ParticleTracking\hindcast_formats_examples\nemo\NemoNorthSeaORCA025-N006_data\**\OR*.nc'
mask=r'F:\Hindcast_reader_tests\Schimsv5\WHOI_calvin\SCHISM_v2\**\*.nc'
def pre_process():
    pass

files= glob(mask,recursive=True)
print('numfiles=',len(files))
time_var='time_centered'
time_var='time'

t0= perf_counter()
for fn in files:
    nc= DatasetNCDF(fn)
    t = nc[time_var][:].copy()
    #t = nc['hvel'][:24].copy()
    nc.close()
print('DatasetNCDF', perf_counter()-t0)

t0= perf_counter()
nc= xr.open_mfdataset(files,coords =[time_var],combine='by_coords',compat='override')
t = nc[time_var].compute()
#t = nc['hvel'].compute()
#nc.to_zarr(path.join(r'F:\temp\zarr_test',path.basename(fn).rsplit('.',)[0]))
nc.close()
print('open_mfdataset', perf_counter()-t0)

t0= perf_counter()
for fn in files:
    nc= xr.open_dataset(fn)
    t = nc[time_var][:].compute()
    #t = nc['hvel'][:].compute()
    #nc.to_zarr(path.join(r'F:\temp\zarr_test',path.basename(fn).rsplit('.',)[0]))
    nc.close()
print('DatasetX', perf_counter()-t0)

t0= perf_counter()
for fn in files:
    nc= NetCDFhandler(fn)
    t = nc.read_a_variable(time_var).copy()
    #t = nc.read_a_variable('hvel')[:].copy()
    nc.close()
print('NetCDFhandler', perf_counter()-t0)



