import numpy as np
import numba as nb
from time import perf_counter
from matplotlib import pyplot as plt
p = False
@nb.njit(parallel=p)
def F1(A,B,C, active):
    for nn in nb.prange(active.size):
        n = active[nn]
        C[n] = 0.
        for m in range(3):
            C[n] += A[n,m]*B[n,m]



reps=20
N=10**7
dt = np.float64
A = np.random.rand(N,3).astype(dt)
B = A.copy()
C= np.full((N,),0,dtype=dt)

mask = np.random.rand(N)
active = np.flatnonzero(mask < .9)

F1(A,B,C, active)

t0 = perf_counter()
for r in range(reps):
    F1(A, B, C, active)

t = perf_counter()-t0
print('F1', A.dtype, B.dtype, C.dtype,t )


A = A.astype(np.float32)
B = B.astype(np.float32)
C = C.astype(np.float32)
F1(A,B,C, active)

t0 = perf_counter()
for r in range(reps):
    F1(A, B, C, active)

t = perf_counter()-t0
print('F2', A.dtype, B.dtype, C.dtype,t )