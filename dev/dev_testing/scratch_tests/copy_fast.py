import os

from Cython.Shadow import boundscheck
from numba import njit , prange
import numba
import numpy as np
from timeit import timeit, repeat
from time import perf_counter
numba.float64()

import pyximport
#pyximport.install()
pyximport.install(setup_args={"include_dirs":np.get_include()},
                  reload_support=True)
from  copy_array import FnD_4_copy_cython

para=True
@njit(parallel=para)
def F2D_0_current(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        for m in range(2):
            y[n,m] = x[n,m]

@njit(parallel=para,boundscheck=False)
def F2D_0_current_bounds(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        for m in range(2):
            y[n,m] = x[n,m]

@njit(parallel=para)
def F3D_0_current(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        for m in range(3):
            y[n,m] = x[n,m]

@njit(parallel=para)
def FnD_current(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        for m in range(x.shape[1]):
            y[n,m] = x[n,m]

@njit(parallel=para)
def FnD_2_copy_slice(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        y[n, :] = x[n, :].copy()

@njit(parallel=para)
def FnD_2_2D3D_combined(x, y, index):

    if x.shape[1] ==2:
        for nn in prange(index.size):
            n = index[nn]
            for m in range(2):
                y[n, m] = x[n, m]
    else:
        for nn in prange(index.size):
            n = index[nn]
            for m in range(3):
                y[n, m] = x[n, m]

def FnD_copy_to(x, y, mask):
    np.copyto(y,x,where=mask[:,np.newaxis])


@njit(parallel=para)
def FnD_4_packed_vectors(x, y, index):

    for nn in prange(index.size):
        n = index[nn]
        for m in range(x.shape[1]):
            y[n,m] = x[n,m]

@njit(parallel=para)
def FnD_5_listcopy1(x_list, y_list, index):

    for x,y in zip(x_list, y_list):
        for nn in prange(index.size):
            n = index[nn]
            for m in range(2):
                y[n,m] = x[n,m]

@njit(parallel=para)
def FnD_5_listcopy2(x_list, y_list, index):

    for nn in prange(index.size):
        n = index[nn]
        for x, y in zip(x_list, y_list):
            for m in range(2):
                y[n,m] = x[n,m]
reps=100
N=10**6
mask =np.random.rand(N) > .2
index = np.flatnonzero(mask).astype(np.int32)
dt =np.float64
Fs=[[F2D_0_current,F2D_0_current_bounds, FnD_current ,
     FnD_2_copy_slice, FnD_copy_to, FnD_2_2D3D_combined,FnD_4_copy_cython,
     FnD_5_listcopy1,FnD_4_packed_vectors],
    [F3D_0_current, FnD_current, FnD_2_copy_slice, FnD_copy_to,
     FnD_2_2D3D_combined,FnD_4_copy_cython,FnD_5_listcopy1,FnD_5_listcopy2,
     FnD_4_packed_vectors]]

for ndim , fs in enumerate(Fs): # loop over dims
    x = np.random.rand(N,ndim+2 ).astype(dt)
    y = np.random.rand(N,ndim+2 ).astype(dt)



    for f in fs:
        if f in [FnD_5_listcopy1,FnD_5_listcopy2]:
            xx,yy = [x,x.copy(),x.copy(),x.copy()], [y,y.copy(),y.copy(),y.copy()]
        elif   f in [FnD_4_packed_vectors]:
            xx, yy = np.column_stack((x,x,x,x)), np.column_stack((y,y,y,y))
        else:
            xx,yy = x,y

        i = mask if f in [FnD_copy_to] else index

        t= timeit(lambda: f(xx,yy,i),setup=lambda: f(xx,yy,i)  ,number=reps)
        print(f'  {t:6.3f} sec  {(t/reps)*1000:5.1f} ms  \t {f.__name__}')



