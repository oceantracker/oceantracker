
from numba import njit, prange
import numpy as np
from timeit import timeit
from time import perf_counter
from matplotlib import pyplot as plt
p=True
@njit(parallel=p)
def copy(x, y, sel ):
    for nn in prange(sel.size):
        n = sel[nn]
        y[n] = x[n]

@njit(parallel=p)
def copyBranch(x,y,sel,z=None):
    for nn in prange(sel.size):
        n = sel[nn]
        y[n] = x[n]
        if z is not None:
            y[n] += z[n]


reps = 100
Ns= 10**np.arange(2,7)
dt =np.float64
t= np.zeros((Ns.size,),dtype=np.float64)
tab= np.zeros((Ns.size,),dtype=np.float64)
tdb= np.zeros((Ns.size,),dtype=np.float64)

y = np.ones((20,), dtype=dt)

colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
for nt, dt in enumerate( [np.int8,np.int32,np.float32,np.float64]):
    x = np.ones((20,), dtype=dt)

    z=x.copy()
    s = 0 if np.issubdtype(dt , np.integer) else 0.

    for n, N in enumerate(Ns):
        sel = np.sort(np.flatnonzero(np.random.rand(N) > .2))
        for r in range(reps):
            x = np.ones((N,), dtype=dt)
            y=x.copy()
            z= x.copy()
            t[n]   += timeit(lambda: copy(x, y,sel ), number=1,setup=lambda: copy(x, y, sel))
            x= np.ones((N,), dtype=dt)
            y = x.copy()
            z = x.copy()
            tab[n] += timeit(lambda: copyBranch(x, y,sel, z=z), number=1, setup=lambda: copyBranch(x, y, sel,z=z))
            x= np.ones((N,), dtype=dt)
            y = x.copy()
            z = x.copy()
            tdb[n] += timeit(lambda: copyBranch(x, y,sel, z=None), number=1, setup=lambda: copyBranch(x, y,sel, z=None))

    plt.plot(Ns, 1000 * t/reps,label=f'copy {dt.__name__}',c=colors[nt])
    plt.plot(Ns, 1000 * tab / reps, label=f'copy  alive branch {dt.__name__}', linestyle=':', c=colors[nt])
    plt.plot(Ns, 1000 * tdb / reps, label=f'copy dead branch {dt.__name__}',
             linestyle='--', c=colors[nt],lw=2,alpha=.5)


plt.xlabel('Aray size,N')
plt.ylabel('write/read ms per array sized N')
plt.legend(fontsize=8)
plt.grid(True)
plt.xscale('log')
plt.yscale('log')
plt.title('Branching, with alive/dead branch')
plt.show()

