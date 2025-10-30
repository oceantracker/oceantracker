from numba import njit, prange
import numpy as np
from time import perf_counter
from oceantracker.util.numba_util import count_simd_intructions
p = True
@njit(parallel=p)
def copy1D(a,b, active):

    for nn in prange(active.shape[0]):
        n = active[nn]
        a[n] = b[n]*b[n]
@njit(parallel=p)
def copy3D(a, b, active):
    for nn in prange(active.shape[0]):
        n = active[nn]
        #a[n, 0], a[n, 1], a[n, 2] = b[n, 0]*b[n, 0], b[n, 1]*b[n, 1], b[n, 2]*b[n, 2]
        for m in range(a.shape[1]):
            a[n, m] = b[n, m] *b[n,m]

@njit(parallel=p)
def copy_multi(a, b, active):

    if a.ndim == 1:
        for nn in prange(active.shape[0]):
            n = active[nn]
            a[n] = b[n]*b[n]
    else:
        for nn in prange(active.shape[0]):
            n = active[nn]
            #for m in range(3):
             #   a[n, m] = b[n, m]*b[n,m]
            #a[n, 0] =  b[n, 0]
            #a[n, 1] = b[n, 1]
            #a[n, 2] = b[n, 2]
            a[n, 0], a[n, 1], a[n, 2] = b[n, 0]*b[n, 0], b[n, 1]*b[n, 1], b[n, 2]*b[n, 2]


if __name__ == "__main__":
    N=10**6
    reps = 1000
    dt= np.float32
    a1 = np.random.random((N,)).astype(dt)
    b1 = np.random.random((N,)).astype(dt)
    a3 = np.random.random((N,3)).astype(dt)
    b3 = np.random.random((N,3)).astype(dt)

    active = np.flatnonzero(np.random.rand(N) > .1)

    copy1D(a1, b1, active)
    copy3D(a3, b3, active)
    copy_multi(a1, b1, active)
    copy_multi(a3, b3, active)

    t0= perf_counter()
    for r in range(reps):
        copy1D(a1, b1, active)
        copy3D(a3, b3, active)

    print('split', perf_counter()-t0)
    print('split', count_simd_intructions(copy1D)[0])
    print('split', count_simd_intructions(copy3D)[0])

    t0 = perf_counter()
    for r in range(reps):
        copy_multi(a1, b1, active)
        copy_multi(a3, b3, active)

    print('multi', perf_counter() - t0)
    print('multi',count_simd_intructions(copy_multi, sig=0)[0])
    print('multi',count_simd_intructions(copy_multi, sig=1)[0])


