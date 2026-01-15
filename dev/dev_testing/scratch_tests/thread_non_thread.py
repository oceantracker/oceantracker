from psutil import cpu_count

physical_cores = cpu_count(logical=False)
import  numpy as np
from numba import njit, set_num_threads, prange

set_num_threads(physical_cores)
from time import perf_counter


def work(x,out,sel):
    for nn in prange(sel.size):
            n = sel[nn]
            out[n] = x[n]


reps = 10
Ns= np.asarray(10**np.arange(3,7))
t_nothreads = np.full((Ns.size,),0,dtype=np.float64)

t_threads = np.full((Ns.size,physical_cores),0,dtype=np.float64)

ndim=3



for n, N in enumerate(Ns):
    sel = np.random.randint(0, high=N, size=int(.9 * N), dtype=np.int32)
    x = np.random.rand(N) if ndim == 1 else np.random.rand(N, ndim)
    out = np.full_like(x, 0)

    F = njit(work, parallel=False)
    F(x, out, sel)
    t0 = perf_counter()
    for m in range(reps):
        F(x, out, sel)
    t_nothreads[n] = perf_counter() - t0

    for threads in range(physical_cores):
        x = np.random.rand(N)
        out= np.full_like(x,0)

        set_num_threads(threads+1)
        F= njit(work, parallel=True)
        # compile code
        F(x,out,sel)

        t0 = perf_counter()
        for m in range(reps):
            F(x,out,sel)
        t_threads[n,threads] = perf_counter()-t0



#asm(copy1)

from matplotlib import  pyplot as plt

for n, N in enumerate(Ns):
    plt.plot(np.arange(physical_cores)+1,t_threads[n,:],label=f'particles={N:,}')
    plt.scatter(1,t_nothreads[n])
plt.yscale('log')
plt.legend()
plt.grid('on')
plt.xlabel('threads')
plt.ylabel('time')
plt.show()





