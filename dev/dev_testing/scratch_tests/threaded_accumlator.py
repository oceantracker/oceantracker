from numba import njit, prange, set_num_threads
from time import perf_counter
import numpy as np

def  Fraw(x, y):
    count=0
    for n in prange(x.size):
        y[n] = 6.*x[n]
        count += n
    return count

N=10**7
reps =10

set_num_threads(2)

for p in [False,True, ]:
    F = njit(Fraw, parallel=p)
    x = np.random.rand(N)
    y = np.full_like(x,0.)
    c =F(x, y)
    t0= perf_counter()
    for rep in range(reps):
        c = F(x, y)

    print('parallel', p,c, (perf_counter()-t0)*1000/reps, 'ms per step')