# compare geographic coods with and withouit broacasting
from numba import njit, prange
import numpy as np
from timeit import timeit
from time import perf_counter
from matplotlib import pyplot as plt
p=True
@njit(parallel=p)
def coord_trans_not_geographic(x, y, index ):
    for nn in prange(index.size):
        n = index[nn]
        temp = 0.
        for m in range(2):
            temp += x[n, m]
        temp += x[n, 2]
        y[n] = temp

@njit(parallel=p)
def coord_trans_geographic(x, y, trans, index ):
    for nn in prange(index.size):
        n = index[nn]
        temp = 0.
        for m in range(2):
            temp += x[n, m]*trans[n,m]
        temp += x[n,2]
        y[n] = temp

@njit(parallel=p)
def coord_trans_geographic_manual_broadcast(x, y, trans, index ):
    for nn in prange(index.size):
        n = index[nn]
        temp = 0.
        nm = n % trans.shape[0]
        for m in range(2):
            temp += x[n, m]*trans[nm,m]
        temp += x[n,2]
        y[n] = temp

N= 10**7
dt =np.float64

reps=100

index = np.sort(np.flatnonzero(np.random.rand(N) > .2))
M=3
x1 = np.ones((1,M), dtype=np.float64)
x_full = np.ones((N,M), dtype=np.float64)

y= np.zeros((N,), dtype = x1.dtype)
y1= y.copy()
y2=y1.copy()
y3=y1.copy()
y4=y1.copy()
trans_full = np.ones((N,M-1),dtype=x1.dtype)
trans_broad1 = trans_full[0,:].reshape((1, M-1))
trans_broad = np.broadcast_to(trans_broad1, (N, M-1))


# meters grid, no tansform
t1   = timeit(lambda: coord_trans_not_geographic(x_full, y1, index), number=reps, setup=lambda: coord_trans_not_geographic(x_full, y, index))
print('done t1')

# test full geographic
t2   = timeit(lambda: coord_trans_geographic(x_full, y2, trans_full, index), number=reps, setup=lambda: coord_trans_geographic(x_full, y, trans_full, index))
print('done t2')

# broadcast geogrphic
t3   = timeit(lambda: coord_trans_geographic(x_full, y3, trans_broad, index), number=reps, setup=lambda: coord_trans_geographic(x_full, y, trans_broad, index))
print('done t3')

# manual broadcast geographic
t4   = timeit(lambda: coord_trans_geographic_manual_broadcast(x_full, y4, trans_broad1, index), number=reps, setup=lambda: coord_trans_geographic_manual_broadcast(x_full, y, trans_broad1, index))
print('done t4')

print('full geo to non geo full', t1,t2,"t2/t1", t2/t1)
print('broadcast geo to non geo,',t3,"t3/t1", t3/t1)

print('broadcast geo to manual broadcast ',t4,"t4/t3", t4/t3, 'check y4-y1=', np.max(np.abs(y1-y3)))
print('Checks', 'check y1-y2=', np.max(np.abs(y1-y2)), '\t check y1-y2=', np.max(np.abs(y1-y3)), '\t check y4-y3=', np.max(np.abs(y4-y3)), )