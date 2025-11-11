from numba import njit , prange
import numba
import numpy as np
from timeit import timeit, repeat
from time import perf_counter
numba.float64()

@njit()
def F01D(x,y,index):
    for nn in range(index.size):
        n = index[nn]
        y[n] = x[n]
@njit()
def F02D(x,y,index):
    for nn in range(index.size):
        n = index[nn]
        for m in range(2):
            y[n,m] = x[n,m]
@njit()
def F03D(x,y,index):
    for nn in range(index.size):
        n = index[nn]
        for m in range(3):
            y[n,m] = x[n,m]


@njit()
def F11D(x,y,index):
    for nn in range(index.size):
        n = index[nn]
        y[n] = x[n]
@njit()
def F12D(x,y,index):
    for nn in range(index.size):
        n = index[nn]
        y[n,:2] = x[n,:2]
@njit()
def F13D(x,y,index):
    for nn in range(index.size):
        n = index[nn]
        y[n,:3] = x[n,:3]

def F21D(x,y,mask):
    if x.ndim>1:
        mask = mask.reshape([mask.size,1] )
    np.copyto(x,y,where=mask)


reps=100
N=10**6
mask =np.random.rand(N) > .2
index = np.flatnonzero(mask)
dt =np.float64
F0 = [F01D,F02D,F03D,]
F1 = [F11D,F12D,F13D,]
F2 = [F21D,F21D,F21D,]
x = [np.random.rand(N, ).astype(dt),np.random.rand(N, 2).astype(dt),np.random.rand(N,3 ).astype(dt)]
y = [np.random.rand(N, ).astype(dt),np.random.rand(N, 2).astype(dt),np.random.rand(N,3 ).astype(dt)]


for n , (f0,f1,f2,x,y) in enumerate(zip(F0,F1,F2,x,y)):



    t= timeit(lambda: f0(x,y,index),setup=lambda: f0(x,y,index)  ,number=reps)
    print(f'  {t:6.3f} sec  {(t/reps)*1000:5.1f} ms  \t {f0.__name__}')
    t = timeit(lambda: f1(x, y, index), setup=lambda: f1(x, y, index), number=reps)
    print(f'  {t:6.3f} sec  {(t / reps) * 1000:5.1f} ms  \t {f1.__name__}')

    t = timeit(lambda: f2(x, y, mask), setup=lambda: f2(x, y, mask), number=reps)
    print(f'  {t:6.3f} sec  {(t / reps) * 1000:5.1f} ms  \t {f2.__name__}')


