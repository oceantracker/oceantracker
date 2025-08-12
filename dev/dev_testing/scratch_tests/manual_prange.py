from psutil import cpu_count
import  os
physical_cores = cpu_count(logical=False)
import  numpy as np
from numba import njit, get_num_threads, set_num_threads, prange, get_thread_id
set_num_threads(physical_cores)
from time import perf_counter

@njit()
def sel_part(x):
    return x > 0.5

@njit(parallel=True)
def work1(x,IDs,out):
    for nn in prange(IDs.size):
        n = IDs[nn]
        out[n] = x[n]
@njit(parallel=True)
def work2(x,IDs,out):
    IDsplits = np.array_split(IDs, get_num_threads())
    for nn in prange(len(IDsplits)):
        for n in IDsplits[nn]:
            out[n] = x[n]


reps = 10
Ns= np.asarray(10**np.arange(2,8))
t1 = np.full((Ns.size,),0,dtype=np.float64)
t2 = t1.copy()

print(Ns)
for n ,N in enumerate(Ns):
    ID = np.full((N,),0,dtype=np.int32)
    IDthread =  np.full((physical_cores,N //physical_cores +1),0,dtype=np.int32)
    IDperThread= np.full((physical_cores,),0,dtype=np.int32)
    starts= IDperThread.copy()
    x= np.random.rand(N)
    IDs = np.flatnonzero( x >.01)
    IDsplit = np.array_split(IDs, get_num_threads())

    out1= np.full_like(x,0.)
    out2 = np.full_like(x,0.)


    # compile code
    work1(x,IDs,out1)
    work2(x,IDs,out2)
    print('check',N,  np.abs(out2 - out1).sum())

    t0 = perf_counter()
    for m in range(reps):
        work1(x, IDs, out1)
    t1[n] = perf_counter()-t0
    print('done 1')
    t0 = perf_counter()
    for m in range(reps):
        work2(x, IDs, out1)
    t2[n] = perf_counter()-t0


from matplotlib import  pyplot as plt
plt.plot(Ns,t1,label='numba split')
plt.plot(Ns,t2,label='manual split ')
plt.legend()
plt.grid('on')
plt.show()
print('relative speed', t2[-1]/t1[-1])




