import numpy as np
from Cython.Shadow import boundscheck
from numba import njit, prange, typed
from time import sleep,perf_counter
from timeit import timeit
import matplotlib.pyplot as plt
from copy import deepcopy
p=False
@njit(parallel=p,boundscheck=True)
def f0(x,y,index):
    for nn in prange(index.size):
        n = index[nn]
        for m in range(x.shape[1]):
            y[n] += x[n,m]

    for nn in prange(index.size):
        n = index[nn]
        for m in range(x.shape[1]):
            y[n] += x[n,m]

@njit(parallel=p,boundscheck=True)
def fb1(x,y,index,blocks):
    splits = np.array_split(index, blocks)
    for s in splits:
        for nn in prange(s.size):
            n = index[nn]
            for m in range(x.shape[1]):
                y[n] += x[n,m]
        for nn in prange(s.size):
            n = index[nn]
            for m in range(x.shape[1]):
                y[n] += x[n, m]

reps = 200
M=3
Ns=[10**3,10**4,10**5,10**6]
#Ns=[10**6]
blocks =np.arange(1,900,50).astype(np.int32)
time0 = np.full((len(Ns),),fill_value=0.)
timeb = np.full((len(Ns),blocks.size),fill_value=0.)


dt = np.float64
for nn,N in enumerate(Ns):
    x = np.ones((N, M),dtype=dt)
    y = np.zeros((N,),dtype=dt)
    index= np.flatnonzero(np.random.random(N) > 0.1)


    for nb, b in enumerate(blocks):
        print(N,b)
        splits = np.array_split(index, b)
        ss = [n.size for n in splits]
        print(len(splits), min(ss),max(ss))

        timeb[nn,nb] = timeit(lambda: fb1(x, y, index, blocks), setup=lambda: fb1(x, y, index, blocks), number=reps)

    time0[nn,] = timeit(lambda: f0(x, y, index), setup=lambda: f0(x, y, index), number=reps)

for nn,N in enumerate(Ns):
    plt.plot(blocks,timeb[nn,:]/time0[nn],label=f'N= {N}')


plt.legend()
plt.show()



