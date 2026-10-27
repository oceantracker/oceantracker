import os

from numba import njit , prange
import numba
import numpy as np
from timeit import timeit, repeat
from time import perf_counter

@njit
def F2D_00(x, y, index):
    for n in index:
        for m in range(2):
            y[n,m] = x[n,m]


para=True
@njit(parallel=para)
def F2D_0_numba(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        for m in range(2):
            y[n,m] = x[n,m]

@njit(parallel=para,boundscheck=True)
def F2D_0_numba_nobounds(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        for m in range(2):
            y[n,m] = x[n,m]

@njit(parallel=para)
def F2D_numba_row_copy(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        y[n,:]=x[n,:]


def FnD_mask_copy_to(x, y, mask):
    np.copyto(y,x,where=mask[:,np.newaxis])

def FnD_numpy_index(x, y, index):
    y[index,:] = x[index,:]


@njit(parallel=para)
def FnD_block_copy(x, y, index):
    index_blocks= np.array_split(index, 40)
    for n in prange(len(index_blocks)):
        #b = index_blocks[n]
        #y[b, :] = x[b, :]
        F2D_00(x, y, index_blocks[n])

reps=1
N=10**6
mask =np.random.rand(N) > .2
index = np.flatnonzero(mask).astype(np.uintp)
dt =np.float64
Fs=[[F2D_0_numba, F2D_0_numba_nobounds, FnD_mask_copy_to,F2D_numba_row_copy, FnD_block_copy,FnD_numpy_index],
    [    ]]

for ndim , fs in enumerate(Fs): # loop over dims
    x = np.random.rand(N,ndim+2 ).astype(dt)
    y = np.random.rand(N,ndim+2 ).astype(dt)

    for f in fs:
        xx,yy = x.copy(),y.copy()

        i = mask if 'mask' in f.__name__ else index

        t= timeit(lambda: f(xx,yy,i),setup=lambda: f(xx,yy,i)  ,number=reps)
        print(f'  {t:8.4f} sec  {(t/reps)*1000:6.3f} ms/rep  \t {f.__name__}')



