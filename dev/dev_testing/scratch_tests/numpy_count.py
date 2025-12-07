import numpy as np
from numba import njit
from timeit import timeit
from time import perf_counter
N=100
M=10**6

x= np.random.rand(N,M)

count = np.zeros((N,),dtype=np.int32)
out= np.zeros((N,),dtype=np.int32)
reps=1

t0 = perf_counter()
for r in range(reps):
    c = np.count_nonzero(x>.1, axis=1,out=count)
print('x=cont',perf_counter()-t0)
print(c-np.count_nonzero(x,axis=1))