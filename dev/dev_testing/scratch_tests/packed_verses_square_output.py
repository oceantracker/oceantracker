from oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from  time import  perf_counter


N=10**6
comp = 1
a= np.random.randn(N)

nc= NetCDFhandler(r'F:\H_Local_drive\ParticleTracking\oceantracker_output\scratch\packed_square.nc',mode='w')
nc. add_dimension('time',None)
nc. add_dimension('particle',None)
nc.create_a_variable('x',['time', 'particle'], np.float64, chunksizes=[24, 100_000], compressionLevel=comp)

time_steps = 24

t0 = perf_counter()
for nt  in range(time_steps):
    nn = int(nt*N/time_steps)
    nc.file_handle.variables['x'][nt,:nn] = a[:nn]

nc.close
print('compression', comp)
print('square time=', perf_counter()-t0)


nc= NetCDFhandler(r'F:\H_Local_drive\ParticleTracking\oceantracker_output\scratch\packed_compact.nc',mode='w')
nc. add_dimension('time_particle',None)

nc.create_a_variable('x',['time_particle'], np.float64, chunksizes=[24*100_000], compressionLevel=comp)
nc.create_a_variable('n_write',['time_particle'], np.int32, chunksizes=[24*100_000], compressionLevel=comp)

time_steps = 24

t0 = perf_counter()
n_writes= 0
for nt  in range(time_steps):
    nn = int(nt*N/time_steps)
    sel = n_writes + np.arange(nn)
    nc.file_handle.variables['x'][sel] = a[:nn]
    nc.file_handle.variables['n_write'][sel] = n_writes
    n_writes += sel.size
nc.close

print('compact time=', perf_counter()-t0)