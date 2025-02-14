from os import  environ
#environ['NUMBA_PARALLEL_DIAGNOSTICS']= '4'

from oceantracker.util import  numba_util
import numba as nb
import numpy as np
from time import perf_counter

@nb.njit()
def T(a,b,scale):
    for n in range(a.shape[0]):
        for m in range(3):
            a[n,m] += scale*b[n, m]

N=5
a = np.random.random((N,3))
b = np.random.random((N,3))
s=.1

a= T(a,b,s)

c =T.inspect_asm(T.signatures[0])
print(c)
