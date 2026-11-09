import pstats

from numba import njit, prange, float64,int32
import numpy as np
from timeit import timeit
import cProfile, pstats
from time import perf_counter
para=True
cache=True


@njit(parallel=para, cache=cache)
def F0(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        tmp=0.
        for m in range(3):
            tmp += x[n,m]
        y[n] = tmp

@njit(inline='never')
def Un(x):
    tmp= 0.
    for m in range(3):
        tmp += x[m]
    return tmp

@njit(parallel=para, cache=cache)
def F_util_no_inline(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        y[n] =Un(x[n,:])

@njit(inline='always')
def Ua(x):
    tmp= 0.
    for m in range(3):
        tmp += x[m]
    return tmp

@njit(parallel=para, cache=cache)
def F_util_always_inline(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        y[n] =Ua(x[n,:])


@njit((float64[:,:], float64[:,:], int32[:]),parallel=para
      , cache=cache)
def F0_sig(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        tmp=0.
        for m in range(3):
            tmp += x[n,m]
        y[n] = tmp
reps = 100
N = 10 ** 6
dt = np.float64

mask = np.random.rand(N) > .1
index = np.flatnonzero(mask).astype(np.int32)
x = np.random.rand(N, 3).astype(dt)
y = np.random.rand(N, 1).astype(dt)

Fs=[F0_sig, F0,F_util_no_inline, F_util_always_inline,]
#Fs=[F0,]
profiler = cProfile.Profile()
run=True
profiler.enable()
for n,F in enumerate(Fs):
    xx,yy=x.copy(), y.copy()
    F(x, y, index)
    t0=perf_counter()
    F(xx, yy, index)
    print(F.__name__,perf_counter()-t0)

profiler.disable()


# Print statistics sorted by cumulative or total time to the screen
stats = pstats.Stats(profiler)
stats.sort_stats("tottime")  # or sort_stats('tottime')
stats.print_stats(20)