from numba import njit
import numpy as np
from time import  perf_counter

@njit()
def F1(x,index):
    s=0
    for n in index:
        s+=x[n]
    return s
@njit()
def F2(x,r):
    s=0.
    for n in range(r[0],r[1]):
        s+=x[n]
    return s

N= 10**6
x= np.random.randn(N)
r= (0,x.size)
i= np.arange(0,x.size).astype(np.int32)
for F,args in zip([F1,F2],[(x,i),(x,r)]):
    F(*args)
    t0 = perf_counter()
    for m in range(10):
        s = F(*args)
    print(F, perf_counter()-t0, s)