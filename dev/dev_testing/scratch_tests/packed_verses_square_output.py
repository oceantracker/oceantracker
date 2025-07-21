from oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from  time import  perf_counter
from os import  path, stat

N=10**6# max released per time step
time_steps = 20
dtype = np.float64

mode =0 # 0= release more overtime, =1 release N evry time
kill =False #True #

part_chunks= int(N/10) # 1/10 max numb particles
M = 3
x = np.random.rand(N, M).astype(dtype)
comp = 0

out_dir =r'C:\Auck_work\oceantracker_output\scratch'
#out_dir =r'F:\H_Local_drive\ParticleTracking\oceantracker_output\scratch\'
fn1 =  path.join(out_dir,'square.nc')
nc= NetCDFhandler(fn1,mode='w')
nc. add_dimension('time',None)
nc. add_dimension('particle',None)
nc. add_dimension('threeD',M)
nc.create_a_variable('x',['time', 'particle','threeD'], dtype=dtype,
                     chunksizes=[1, int(part_chunks) ,M],
                     compression_level=comp, )
t0 = perf_counter()
t_steps= np.zeros((time_steps,))
for nt  in range(time_steps):
    n1 =  int(N*nt/2/time_steps)  if kill and nt > .5* time_steps else  0
    n2 = int(N*(nt+1)/time_steps) if mode == 0 else N

    t1 = perf_counter()
    nc.file_handle.variables['x'][nt,n1:n2,:] = x[n1:n2,:]
    t_steps[nt] = perf_counter()-t1

nc.close
print(f'per time step N= {N:,} total written {N/2*time_steps:,} \t  compression {comp}')
print('square time=', f'{1000*(perf_counter()-t0)/time_steps:3.2f} msec/step ' ,f'file _size {path.getsize(fn1):,} / {stat(fn1).st_size:,}')
print('\t max min all time steps',t_steps.min(), t_steps.max())


fn2 = path.join(out_dir,'compact.nc')
nc= NetCDFhandler(fn2,mode='w')
nc. add_dimension('time_particle',None)
nc. add_dimension('threeD',M)
nc.create_a_variable('x',['time_particle','threeD'], dtype=dtype,
                     chunksizes=[int(N/10), M], compression_level=comp)

t0 = perf_counter()
n_writes= 0
t_steps= np.zeros((time_steps,))
for nt  in range(time_steps):
    n1 = int(N * nt / 2 / time_steps) if kill and nt > .5 * time_steps else 0
    n2 = int(N*(nt+1)/time_steps) if mode == 0 else N
    t1 = perf_counter()

    nc.file_handle.variables['x'][n_writes : n_writes+n2-n1,:] = x[n1:n2,:]
    n_writes += n2
    t_steps[nt] = perf_counter() - t1
nc.close

print('compact time=', f'{1000*(perf_counter()-t0)/time_steps:3.2f} msec/step ', f'file _size {path.getsize(fn2):,}/ {stat(fn2).st_size:,}')
print('\t max min all time steps',t_steps.min(), t_steps.max())

f1 =NetCDFhandler(fn1,'r')
x1 = f1.read_a_variable('x')
f1.close()
f2 =NetCDFhandler(fn2,'r')
x2= f2.read_a_variable('x')
f2.close()

n2 = int(N /time_steps) # compare first time step
dx = x1[0,:n2,:] - x2[:n2,:]
print(f'compare diff, min = {np.nanmin(dx) } max= {np.nanmax(dx) } ' )

