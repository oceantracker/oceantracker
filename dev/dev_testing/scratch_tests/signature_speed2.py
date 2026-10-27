from time import  perf_counter


#os.environ['NUMBA_CPU_FEATURES'] = '-avx,-avx2,-sse'
from numba import jit,njit, float64,int32, types, prange
import numpy as np
from timeit import timeit
from matplotlib import pyplot as plt

para = True
@njit(parallel=para)
def add1(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        y[n] =  x[n] #np.sin(x[n]) ** 2 + x[n] +3*x[n]**2


@njit((float64[::1], float64[::1], int32[::1]), parallel=para)
def add2(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        y[n] =  x[n] #np.sin(x[n]) ** 2 + x[n] +3*x[n]**2

reps = 1000

Ns=10**np.arange(1,7)
t1= np.zeros((Ns.size),dtype=np.float64, order='C')
t2= np.zeros((Ns.size),dtype=np.float64,order='C')


for n,N in enumerate(Ns):

    x = np.random.rand(N)
    y = np.random.rand(N)
    index = np.flatnonzero(np.random.rand(N)> 0.1).astype(np.int32)

    t0 = perf_counter()
    add1(x, y, index)
    if n==1: t1c = perf_counter() - t0

    t0 = perf_counter()
    for r in range(reps):
        add1(x, y, index)
    t1[n] = perf_counter()-t0

    x = np.random.rand(N)
    y = np.random.rand(N)

    t0 = perf_counter()
    add2(x, y, index)
    if n==1: t2c = perf_counter() - t0

    t0 = perf_counter()
    for r in range(reps):
        add2(x, y, index)
    t2[n] = perf_counter()-t0
    pass

print('compile times =', t1c,t2c, t2c/t1c, ' not add2 complied on import' )

fig,axs= plt.subplots(1,2,figsize=[12,6])
ax=axs[0]
ax.plot(Ns,t1)
ax.plot(Ns,t2, label='sig')
ax.set_xscale('log')
ax.set_yscale('log')
ax.legend()

ax=axs[1]
r = t2/t1
ax.plot(Ns[1:],r[1:])
#ax.set_ylim([.5,1.5])
ax.set_title(f'{r[-1]}')
ax.set_xscale('log')
#ax.set_yscale('log')
plt.show()
