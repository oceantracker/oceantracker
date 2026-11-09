import pstats

from numba import njit, prange, float64,int32
import numpy as np
from timeit import timeit
import cProfile, pstats
from time import perf_counter
para=True
cache=True


def F0(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        tmp=0.
        for m in range(3):
            tmp += x[n,m]
        y[n] = tmp


def F1(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        tmp=0.
        for m in range(3):
            tmp += 1./x[n,m]
        y[n] = tmp

reps = 100
N = 10 ** 6
dt = np.float64

mask = np.random.rand(N) > .1
index = np.flatnonzero(mask).astype(np.int32)
x = np.random.rand(N, 3).astype(dt)
y = np.random.rand(N, 1).astype(dt)

error_models=['python', 'numpy']
Fs =[F0,F1]
#Fs=[F0,]
profiler = cProfile.Profile()
run=True
profiler.enable()
for m,em in enumerate(error_models):
    for n,F in enumerate(Fs):
        xx,yy=x.copy(), y.copy()
        f=njit(error_model=em,parallel=True)(F)
        f(x, y, index)
        t0=perf_counter()
        for nr in range(reps):
            f(xx, yy, index)
        print(em,'\t', f.__name__,perf_counter()-t0)

profiler.disable()


# Print statistics sorted by cumulative or total time to the screen
stats = pstats.Stats(profiler)
stats.sort_stats("tottime")  # or sort_stats('tottime')
stats.print_stats(20)