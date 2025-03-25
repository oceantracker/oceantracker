
from    glob import glob
import xarray as xr
from os import path
import numpy as np

dir = f'/hpcfreenas/hindcast/SouthIsland/'
mask = 'R3*.nc'
new_dir= path.join(dir,'Stantech_hananui_delft3DFM_2025_03_14','Version1')
files= glob(path.join(dir,mask))
d =xr.open_dataset(files[0])

#print(d,d['time'][1], d['time'][0])

nn= 24
for n in range(0,d['time'].size,nn):
  sel = np.arange(n,min(n + nn,d['time'].size))
  d2 = d.isel(time=sel)
   
  t = str(d2['time'].data[0]).split('T')[0]
  
  fn = path.join(new_dir,f'hananui20025_{t}.nc')
  
 
  print(n,sel.size, t)
  d2.to_netcdf(fn)
  
  
#print('xxxx', d['time'].data[:4])
#print(np.diff(d['time']))