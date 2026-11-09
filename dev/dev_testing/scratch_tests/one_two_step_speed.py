from numba import njit , prange
import numba
import numpy as np
from timeit import timeit, repeat
from time import perf_counter

para=False

@njit(parallel=para)
def one_step(x,y,index):
    for nn in prange(index.size):
        n = index[nn]
        tmp = 0.
        for m in range(3):
            tmp += x[n, m] ** 2
        y[n] += tmp

@njit(parallel=para)
def two_step(x,y,index):
    for nn in prange(index.size):
        n = index[nn]
        tmp = 0.
        for m in range(3):
            tmp += x[n,m] ** 2
        for m in range(3):
            tmp += x[n, m] ** 2
        y[n] += tmp

reps=10
N=10**6
dt =np.float64

mask =np.random.rand(N) > .1
index = np.flatnonzero(mask).astype(np.int32)
x = np.random.rand(N, 3).astype(dt)
y = np.random.rand(N, 1).astype(dt)

# compile and check sum
y=y*0.
one_step(x, y, index)
one_step(x, y, index)
s1 = y[index].sum()
t1 = 0.
for r in range(reps):
    xx = x.copy()
    yy = y.copy()
    t0 = perf_counter()
    one_step(xx,yy,index)
    one_step(xx, yy, index)
    t1 += perf_counter() - t0
print('one step', t1/reps)

y=y*0.
two_step(x, y, index)
s2 = y[index].sum()
t2 =0.
for r in range(reps):
    xx = x.copy()
    yy = y.copy()
    t0 = perf_counter()
    two_step(xx,yy,index)
    t2 += perf_counter() - t0
print('two step', t2/reps, )

print('check', s1-s2,'two/one speed', t2/t1 )