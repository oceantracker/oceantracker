from numba import njit
import numpy as np
from timeit import timeit
from time import perf_counter

bt= False
@njit(boundscheck=bt)
def F0(x,y,sel):
    for nn in range(sel.size):
        n= sel[nn]
        s = 0.
        for m in range(x.shape[1]):
            s += x[n,m]
        y[n] = s

@njit(boundscheck=bt)
def F1(x,y,sel):
    xv= x[0,:,:,0]
    for nn in range(sel.size):
        n= sel[nn]
        s = 0.
        for m in range(xv.shape[1]):
            s += xv[n,m]
        y[n] = s

Ns = 10**np.arange(3,7)
t=np.zeros((Ns.size,2))
M=3
reps=100
lab=[]
for n, N in enumerate(Ns.tolist()):
    x4D = np.full((1,N,M,1),0., dtype=np.float32)

    y= np.full((N,),0., dtype=np.float32)
    sel = np.flatnonzero(np.random.rand(N) > 0.2).astype(np.int32)

    F0(x4D.copy().squeeze(),y,sel)
    lab.append('F0 squeeze')
    for nr in range(reps):
        x= x4D.copy().squeeze()
        t0 = perf_counter()
        F0(x, y, sel)
        t[n,0] += perf_counter()- t0

    F1(x4D.copy(),y,sel)
    lab.append('F1 numba view')
    for nr in range(reps):
        x = x4D.copy()
        t0 = perf_counter()
        F1(x, y, sel)
        t[n,1] += perf_counter()-t0



print(t[-1,:])
print(F0.signatures)
from matplotlib import pyplot as plt

fig, axs= plt.subplots(1,2,figsize=[8,4])
ax= axs[0]
for m in range(t.shape[1]):
    ax.plot(Ns,t[:,m]*1000/reps,label=f'{lab[m]}')
ax.legend()
ax.set_xscale('log')

ax= axs[1]
for m in range(1,t.shape[1]):
    ax.plot(Ns,t[:,m]*1/t[:,0],label=f'{lab[m]}')
ax.legend()
ax.set_xscale('log')
ax.set_ylim([.9,1.1])
plt.show()