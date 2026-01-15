from numba import njit
import numpy as np
from timeit import timeit
from time import perf_counter

@njit
def F0(x,y,sel):
    for nn in range(sel.size):
        n= sel[nn]
        s = 0.
        for m in range(x.shape[1]):
            s += x[n,m]
        y[n] = s

Ns = 10**np.arange(3,8)
t=np.zeros((Ns.size,3))
M=3
reps=100
lab=[]
for n, N in enumerate(Ns.tolist()):
    x30 = np.full((N,M),0., dtype=np.float32)
    x3 = np.full((N,1,M,1),0., dtype=np.float32)
    x3v = x3[:,0,:,0]
    x3s = np.squeeze(x3)
    y= np.full((N,),0., dtype=np.float32)
    sel = np.flatnonzero(np.random.rand(N) > 0.2).astype(np.int32)

    F0(x30.copy(),y,sel)
    lab.append('F0 small')
    for nr in range(reps):
        x= x30.copy()
        t0 = perf_counter()
        F0(x, y, sel)
        t[n,0] += perf_counter()- t0

    F0(x3v.copy(),y,sel)
    lab.append('F0 view')
    t2=0.
    for nr in range(reps):
        x = x3v.copy()
        t0 = perf_counter()
        F0(x, y, sel)
        t[n,1] += perf_counter()-t0

    F0(x3s.copy(),y,sel)
    lab.append('F0 squeeze')
    t3=0.
    for nr in range(reps):
        x = x3s.copy()
        t0 = perf_counter()
        F0(x, y, sel)
        t[n,2] += perf_counter()-t0

print(t[-1,:])
print(F0.signatures)
from matplotlib import pyplot as plt

for m in range(1,t.shape[1]):
    plt.plot(Ns,t[:,m]/t[:,0],label=f'{lab[m]}')

plt.xscale('log')
plt.show()