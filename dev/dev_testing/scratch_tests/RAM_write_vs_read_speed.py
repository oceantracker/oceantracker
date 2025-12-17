
from numba import njit, prange, set_num_threads
import numpy as np
from timeit import timeit
from time import perf_counter
from matplotlib import pyplot as plt

p = True
@njit(parallel=p)
def write(x, sel):
    for nn in prange(sel.size):
        n = sel[nn]
        x[n] = n


@njit(parallel=p)
def read(x,sel,s):
    for nn in prange(sel.size):
        n = sel[nn]
        s += x[n]
    return s

set_num_threads(64)
reps = 100
Ns= 10**np.arange(2,8)
dt =np.float64
tw= np.zeros((Ns.size,),dtype=np.float64)
tr= np.zeros((Ns.size,),dtype=np.float64)
tr2= np.zeros((Ns.size,),dtype=np.float64)

colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
for nt, dt in enumerate( [np.int8,np.int32,np.float32,np.float64]):
    x = np.ones((20,), dtype=dt)
    s = 0 if np.issubdtype(dt , np.integer) else 0.

    for n, N in enumerate(Ns):
        sel = np.sort(np.flatnonzero(np.random.rand(N) > .2))
        for r in range(reps):
            x = np.ones((N,), dtype=dt)
            tr[n] += timeit(lambda: read(x,sel,s), number=1, setup=lambda: read(x,sel,s))
            tr2[n] += timeit(lambda: read(x,sel, s), number=1, setup=lambda: read(x,sel, s))
            tw[n] += timeit(lambda: write(x,sel), number=1,setup=lambda: write(x,sel))


    plt.plot(Ns,1000*tr/reps,label=f'read {dt.__name__}',c=colors[nt])
    if dt==np.float64:
        plt.plot(Ns, 1000 * tr2 / reps, label=f'read again {dt.__name__}', linestyle=':', c=colors[nt])
    plt.plot(Ns,1000*tw/reps,label=f'write {dt.__name__}',linestyle='--',c=colors[nt])

#plt.plot(plt.xlim(),plt.ylim(),c=[.8,.8,.8])
plt.xlabel('Aray size,N')
plt.ylabel('write/read ms per array sized N')
plt.legend()
plt.grid(True)
plt.xscale('log')
plt.yscale('log')
plt.title('RAM read vs write speed')

plt.show()

