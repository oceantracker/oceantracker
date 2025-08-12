from psutil import cpu_count
import  os
physical_cores = cpu_count(logical=False)
import  numpy as np
from numba import njit, get_num_threads, set_num_threads, prange, get_thread_id
set_num_threads(physical_cores)
from time import perf_counter

@njit(parallel=True)
def copy1(x,out,sel):
    if x.ndim==1:
        for nn in prange(sel.size):
            n = sel[nn]
            out[n] = x[n]
    else:
        for nn in prange(sel.size):
            n = sel[nn]
            for m in range(x.shape[1]):
                out[n,m] = x[n,m]
@njit(parallel=True)
def copy2(x,out,sel):

    if x.ndim == 1:
        for nn in prange(sel.size):
            n = sel[nn]
            out[n ] = x[ n]
    elif x.ndim == 2:
        for nn in prange(sel.size):
            n = sel[nn]
            for m in range(2):
                out[n, m] = x[n, m]
    elif x.ndim == 3:
        for nn in prange(sel.size):
            n = sel[nn]
            for m in range(3):
                out[n, m] = x[n, m]




reps = 10
Ns= np.asarray(10**np.arange(2,7))
t1 = np.full((Ns.size,),0,dtype=np.float64)
t2 = t1.copy()
ndim=3
dtype=np.int32
dtype=np.float64

for n ,N in enumerate(Ns):
    sel = np.random.randint(0, high=N, size=int(.9 * N), dtype=np.int32)
    x = np.random.rand(N) if ndim == 1 else np.random.rand(N, ndim)
    x = x.astype(dtype=dtype)
    out1= np.full_like(x,0)
    out2 = np.full_like(x,0)


    # compile code
    copy1(x,out1,sel)
    copy2(x,out2,sel)
    print('check',N,  np.abs(out2 - out1).sum())

    x = np.random.rand(N) if ndim == 1 else np.random.rand(N, ndim)
    x = x.astype(dtype=dtype)
    out1 = np.full_like(x, 0)
    out2 = np.full_like(x, 0)
    t0 = perf_counter()
    for m in range(reps):
        copy1(x,out1,sel)
    t1[n] = perf_counter()-t0

    x = np.random.rand(N) if ndim == 1 else np.random.rand(N, ndim)
    x = x.astype(dtype=dtype)
    out1 = np.full_like(x, 0)
    out2 = np.full_like(x, 0)
    t0 = perf_counter()
    for m in range(reps):
        copy2(x,out2,sel)
    t2[n] = perf_counter()-t0

print('relative speed',t2[-1], t2[-1]/t1[-1])
from matplotlib import  pyplot as plt
plt.plot(Ns,t1,label='copy 1')
plt.plot(Ns,t2,label='copy 2 ')
plt.legend()
plt.grid('on')
plt.show()





