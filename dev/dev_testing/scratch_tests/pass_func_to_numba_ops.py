
from numba import njit, prange
import numpy as np
from timeit import timeit
from time import perf_counter
from matplotlib import pyplot as plt

from oceantracker.util.numba_util import njitOT

p=True
@njit(parallel=p)
def compare0(x, y,sel):
    for nn in prange(sel.size):
        n = sel[nn]
        s = 0.
        for m in range(x.shape[1]):
            s += x[n, m]
        y[n] = s


def op0(x,inline='always'):
    s= 0.
    for m in range(x.size):
        s+=x[m]
    return s

@njit(parallel=p)
def compare1(x, y, sel):
    for nn in prange(sel.size):
        n = sel[nn]
        y[n] = op(x[n,:])

@njit(parallel=p)
def compare2(x,fn, y,sel):
    for nn in prange(sel.size):
        n = sel[nn]
        y[n] = fn(x[n, :])


op =njitOT(op0)
reps = 50
Ns= 10**np.arange(3,7)
t0= np.zeros((Ns.size,),dtype=np.float64)
t1= np.zeros((Ns.size,),dtype=np.float64)
t2= np.zeros((Ns.size,),dtype=np.float64)


for n, N in enumerate(Ns):
    xvals = np.random.rand(N, 3)
    y = np.random.rand(N)
    sel = np.flatnonzero( np.random.rand(N) > .1)
    op(xvals[0])
    for r in range(reps):
        x = xvals.copy()
        t0[n] += timeit(lambda: compare0(x, y,sel), number=1,setup=lambda: compare0(x, y, sel[:5]))
        x = xvals.copy()
        t1[n] += timeit(lambda: compare1(x,  y,sel), number=1, setup=lambda: compare1(x,  y,sel[:5]))
        x = xvals.copy()
        t2[n] += timeit(lambda: compare2(x, op, y,sel), number=1, setup=lambda: compare2(x, op, y,sel[:5]))


fig, axs = plt.subplots(1,2,figsize=(10,5))
ax= axs[0]
ax.plot(Ns,t0*1000/reps,label='F0')
ax.plot(Ns,t1*1000/reps,'--',label='F0+func call')
ax.plot(Ns,t2*1000/reps,label=' Pass func')
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_ylabel('Time per call,ms')
ax.legend()

ax= axs[1]
ax.plot(Ns,t1/t0,'--',label='F0+func call')
ax.plot(Ns,t2/t0,label=' Pass func')
ax.set_ylabel('Time / F0 time')
ax.set_ylim([.5,2])
ax.legend()
plt.show()


