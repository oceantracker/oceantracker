import os

#from Cython.Shadow import boundscheck
from numba import njit , prange
import numba
import numpy as np
from timeit import timeit, repeat
from time import perf_counter
numba.float64()

#import pyximport
#pyximport.install()
#pyximport.install(setup_args={"include_dirs":np.get_include()}, reload_support=True)
#from  copy_array import FnD_4_copy_cython

para=True
@njit(parallel=para)
def F3_current_ref(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        for m in range(3):
            y[n,m] = x[n,m]

@njit(parallel=para,boundscheck=True)
def F3_current_bounds(x, y, index):
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
def FnD_copy_slice(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        y[n, :] = x[n, :]

@njit(parallel=para)
def FnD_copy_slice_asbyte(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        y[n, :] = x[n, :]

def FnD_copy_to_mask(x, y, mask):
    np.copyto(y,x,where=mask[:,np.newaxis])

@njit(parallel=para)
def F3_blocked_index(x, y, block_index):
    for nn in prange(block_index.shape[0]):
        n1 = block_index[nn,0]
        n2 =  n1 + block_index[nn,1]
        y[n1:n2,:] = x[n1:n2,:]


@njit()
def get_blocked_index(index):
    max_block_size=10
    block_index=np.full((index.size,2),-1,dtype=index.dtype)
    current_block=0
    num_in_block=1

    block_index[0,0]= index[0]
    for nn in prange(index.size-1):
        if index[nn+1] == index[nn]+1 and num_in_block < max_block_size:
            num_in_block+=1
        else:
            # close block
            block_index[current_block, 1] = num_in_block

            # start new block
            current_block += 1
            block_index[current_block, 0] = index[nn + 1]
            num_in_block = 1

    # close last  block
    if index[-1] == index[-2]:
        # append to last block
        block_index[current_block, 1] += 1
    else:
        # close block and add a single block
        block_index[current_block, 1] = num_in_block
        current_block += 1
        block_index[current_block,0] = index[-1]
        block_index[current_block, 1] = 1

    return block_index[:current_block+1,:]



reps=10
N=10**6
mask =np.random.rand(N) > .1
index = np.flatnonzero(mask).astype(np.int32)

blocked_index = get_blocked_index(index)

dt =np.float64
Fs=[F3_current_ref, F3_current_bounds,FnD_current, FnD_copy_slice,
    FnD_copy_slice_asbyte,
    FnD_copy_to_mask, #FnD_4_copy_cython,
    F3_blocked_index]
x = np.random.rand(N, 3).astype(dt)
y = np.random.rand(N, 3).astype(dt)

for n , f in enumerate(Fs): # loop over Fs
    xx, yy = x.copy(), y.copy()

    if   'asbyte' in f.__name__:  xx, yy = xx.view(np.uint8), yy.view(np.uint8)

    if 'mask' in f.__name__:
        i = mask
    elif 'blocked' in f.__name__:
        i = blocked_index
    else:
        i = index

    t= timeit(lambda: f(xx,yy,i),setup=lambda: f(xx,yy,i)  ,number=reps)
    if n == 0: yref = yy
    if   'asbyte' in f.__name__:        yy = yy.view(dt)
    print(f'  {t:6.3f} sec  {(t/reps)*1000:5.1f} ms  \t {f.__name__}, {np.max(np.abs(yy-yref))}')



