from numba import njit , prange
import numba
import numpy as np
from timeit import timeit, repeat
from time import perf_counter

para=True

@njit(parallel=para)
def read_write(x,y,index):
    for nn in prange(index.size):
        n = index[nn]
        for m in range(3):
            y[n,m] = 2.*x[n, m]
    return x[0,0]

@njit(parallel=para)
def read(x,y,index):
    s= 0.
    for nn in prange(index.size):
        n = index[nn]
        for m in range(3):
            s += x[n, m]
    return s

@njit(parallel=para)
def write(x,y,index):
    for nn in prange(index.size):
        n = index[nn]
        for m in range(3):
            y[n, m] = x[0,0]
    return x[0, 0]

reps=10
N=10**6
dt =np.float64

mask =np.random.rand(N) > .01
index = np.flatnonzero(mask).astype(np.int32)
x = np.random.rand(N, 3).astype(dt)
y = np.random.rand(N, 3).astype(dt)

# compile and check sum

read_write(x, y, index)
t1 = 0.
for r in range(reps):
    xx = x.copy()
    yy = y.copy()
    t0 = perf_counter()
    read_write(xx,yy,index)
    t1 += perf_counter() - t0
print('read_write', t1)

read(x, y, index)
t2 =0.
for r in range(reps):
    xx = x.copy()
    yy = y.copy()
    t0 = perf_counter()
    read(xx,yy,index)
    t2 += perf_counter() - t0
print('read', t2, )

write(x, y, index)
t3 =0.
for r in range(reps):
    xx = x.copy()
    yy = y.copy()
    t0 = perf_counter()
    write(xx,yy,index)
    t3 += perf_counter() - t0
print('write', t3, )



print('read/read write', t2/t1 , 'write/read write', t3/t1 )