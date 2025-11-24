import numpy as np
from numba import njit, prange
from timeit import timeit
from oceantracker.util import numba_util
@njit()
def find_interval_right(x, xq):
    # binary search for interval index in sorted data unevenly spaced
    #  data[index] <= val < data[index+1]
    left = 0
    right = x.size - 1
    while right - left > 1:
        index = (right+left) // 2
        if xq >= x[index]:
            left = index
        elif xq < x[index]:
            right= index

    return left

@njit(parallel=True )
def interval_numba(x, xq, out):

    for n in prange(xq.size):
        out[n] = find_interval_right(x, xq[n])

@njit(parallel=True )
def find_last( x,xq, out):

    #for n, v in enumerate(vals):
    for n in prange(xq.size):
        out[n] = numba_util.find_last_less_than(x, xq[n])

if __name__ == "__main__":


    N=10**6
    M=50
    reps=1000
    x = np.random.rand(M)
    x = np.append(0, np.cumsum(x))

    xq=np.sort(x[-1] * np.random.rand(N))
    xq = np.append(x,xq)# insetd data as query
    out= np.ones((xq.size,),dtype=np.int32)

    t = timeit(lambda: interval_numba(x, xq, out), setup=lambda:interval_numba( x,xq, out), number=reps)
    print('interval_numba time',t ,', ms per rep',t*1000/reps)
    ok = np.logical_and(xq >= x[out], xq < x[out + 1])
    print('bad ' , np.sum(~ok))

    t = timeit(lambda: find_last(x, xq, out), setup=lambda: find_last(x, xq, out), number=reps)
    print('find_last time', t, ', ms per rep', t * 1000 / reps)
    ok = np.logical_and(xq >= x[out], xq < x[out + 1])
    print('interval_numba, bad ', np.sum(~ok))

    t = timeit(lambda: np.searchsorted(x, xq),  number=reps)
    print('time', t, ', ms per rep', t * 1000 / reps)
    out  = np.minimum(np.searchsorted(x, xq,side='right')-1, x.shape[0]-2) # clip mast cell
    ok = np.logical_and(xq >= x[out], xq < x[out + 1])
    print('searchsorted bad ', np.sum(~ok))
    #print(out)
    #print(data)





