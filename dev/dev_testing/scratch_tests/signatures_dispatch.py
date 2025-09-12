from psutil import cpu_count
physical_cores = cpu_count(logical=False)
import  numpy as np
from numba import njit, get_num_threads, set_num_threads, prange, get_thread_id
set_num_threads(physical_cores)
from time import perf_counter

@njit(parallel=True)
def copy(x,out,sel):
    for nn in prange(sel.size):
        n = sel[nn]
        for m in range(x.shape[1]):
            out[n,m] = x[n,m]

reps = 100
N=10**2
dtypes=[np.int8, np.int16,np.int32, np.float32,np.float64]
t1 = np.full((len(dtypes),),0,dtype=np.float64)
t2 = t1.copy()
ndim=2

sel = np.random.randint(0, high=N, size=int(.5 * N), dtype=np.int32)

for n ,dtype in  enumerate(dtypes):

    x =  np.random.rand(N, ndim)
    out1 = np.full_like(x, 0)
    x = x.astype(dtype=dtype)
    # compile code
    copy(x, out1, sel)

    x = np.random.rand(N, ndim)
    out1 = np.full_like(x, 0)
    x = x.astype(dtype=dtype)
    t0 = perf_counter()
    for m in range(reps):
        copy(x, out1, sel)
    t1[n] = perf_counter() - t0


print('relative speed',1000*t2[-1]/reps, t2[-1]/t1[-1])
print(copy.signatures)
from matplotlib import  pyplot as plt
x= np.arange((len(dtypes)))
plt.plot(x,t1*1000/reps,label='copy 1')

plt.legend()
plt.grid('on')
plt.show()





