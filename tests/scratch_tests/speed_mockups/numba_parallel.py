import numpy as np
from numba import njit , prange, types as nbtypes ,vectorize, literally, set_num_threads
from numba.core.types.containers import LiteralStrKeyDict,StructRef,Literal
from time import perf_counter
from numba.typed import Dict

#set_num_threads(32)

@njit(inline='never')
def F(a,b,c):
    s= 0.
    for w in range(20):
        for m in range(b.shape[0]):
            if a > .5:
                s += a + b[m] + c[m]
    return s

@njit()
def K1(a, b,c, c_index, o,  id):

    for i in range(id.size):
        n = id[i]
        o[n] += F(a[n], b[n, :], c[c_index[i], :]) # random row acess to C rows


@njit(parallel=True)
def K3(a, b,c,c_index, o, id):
    counts =np.zeros((2,),dtype = np.int32)
    for i in prange(id.size):
        n = id[i]
        o[n] += F(a[n], b[n, :], c[c_index[i], :])

        counts[0] +=1  # check race condtion on this

    return s
N=100000
M=2
A = np.random.rand(N)
B = np.random.rand(N,M)
C = np.random.rand(N,M)
O = np.zeros((N,),dtype=np.float64)
mask =(np.random.rand(N) > .5).astype(bool)
id = np.sort(np.flatnonzero(mask)).astype(np.int32)

# random access to c rows
c_index= np.random.randint(0,high=N,size=id.size)

nreps=1000


K1(A, B,C,c_index, O, id)
O = np.zeros((N,),dtype=np.float64)
t0=perf_counter()
for n in range(nreps):
    s = K1(A, B,C,c_index, O, id)
t1 =perf_counter()-t0
print('time',t1, O.sum())


K3(A, B,C, c_index, O, id)
O = np.zeros((N,),dtype=np.float64)
t0=perf_counter()
for n in range(nreps):
    s = K3(A, B,C,c_index, O, id)
t3 =perf_counter()-t0
print('time',t3,  O.sum())
print('rel speed', t3/t1)
