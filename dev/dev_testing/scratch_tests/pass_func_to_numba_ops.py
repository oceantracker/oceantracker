
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


@njit(inline='always')
def op(x):
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

@njit(inline='always')
def op1(n,x,y):
    s= 0.
    for m in range(x.shape[1]):
        s+=x[n,m]
    y[n] = s

@njit(parallel=p)
def compare3(x, y,sel):
    for nn in prange(sel.size):
        n = sel[nn]
        op1(n,x,y)

@njit(parallel=p)
def compare4(x,fn, y,sel):
    for nn in prange(sel.size):
        n = sel[nn]
        fn(n,x,y)

reps = 50
Ns= 10**np.arange(3,8)
t0= np.zeros((Ns.size,),dtype=np.float64)
t1= np.zeros((Ns.size,),dtype=np.float64)
t2= np.zeros((Ns.size,),dtype=np.float64)
t3= np.zeros((Ns.size,),dtype=np.float64)
t4= np.zeros((Ns.size,),dtype=np.float64)

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
        x = xvals.copy()
        t3[n] += timeit(lambda: compare3(x, y,sel), number=1, setup=lambda: compare3(x,  y,sel[:5]))
        x = xvals.copy()
        t4[n] += timeit(lambda: compare4(x, op1, y, sel), number=1, setup=lambda: compare4(x, op1, y, sel[:5]))


x = xvals.copy()
compare0(x, y, sel)
s0 = y.sum()
compare3(x, y,sel)
s3 = y.sum()
print(s0,s3)

fig, axs = plt.subplots(1,2,figsize=(10,5))
ax= axs[0]
ax.plot(Ns,t0*1000/reps,label='F0')
ax.plot(Ns,t1*1000/reps,'--',label='F0+func call')
ax.plot(Ns,t2*1000/reps,label=' Pass func')
ax.plot(Ns,t3*1000/reps,label='Index func call')
ax.plot(Ns,t4*1000/reps,label='Passed+index func call')
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_ylabel('Time per call,ms')
ax.legend()

ax= axs[1]
ax.plot(Ns,t1/t0,'--',label='F0+func call')
ax.plot(Ns,t2/t0,label=' Pass func')
ax.plot(Ns,t3/t0,label='Index func call')
ax.plot(Ns,t4*1/t0,label='Passed+index func call')
ax.set_ylabel('Time / F0 time')
ax.set_ylim([.5,1.5])
ax.legend()
plt.show()


