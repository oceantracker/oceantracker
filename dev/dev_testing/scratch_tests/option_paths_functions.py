from numba import njit , prange
import numpy as np
from timeit import timeit, repeat
import matplotlib.pyplot as plt
from time import perf_counter
#il = 'always'
il = 'never'
p=True

@njit(inline='always')
def W(x): return x**2

@njit(inline=il)
def K2(x):
    y=0.
    for m in range(2):
        y += W(x[m])
    return y
@njit(inline=il)
def K3(x):
    y=0.
    for m in range(3):
        y += W(x[m])
    return y
@njit(inline=il)
def Kn(x):
    y=0.
    for m in range(x.size):
        y += W(x[m])
    return y


@njit(parallel=p)
def F30(x,y,sel):
    for nn in prange(sel.size):
        n = sel[nn]
        y[n] = K3(x[n,:])
@njit(parallel=p)
def Fn0(x,y,sel):
    for nn in prange(sel.size):
        n = sel[nn]
        y[n] = Kn(x[n,:])
@njit(parallel=p)
def F3mixed(x,y,sel):
    if x.shape[1] ==2:
        for nn in prange(sel.size):
            n = sel[nn]
            y[n] = K2(x[n,:])
    else:
        for nn in prange(sel.size):
            n = sel[nn]
            y[n] = K3(x[n, :])

@njit(parallel=p)
def F3func_kernal_arg(x, y, sel, K):
    for nn in prange(sel.size):
            n = sel[nn]
            y[n] = K(x[n, :])

@njit(parallel=p)
def F3func_kernal(x, y, sel):

    K = K2 if x.shape[1] ==2 else K3

    for nn in prange(sel.size):
            n = sel[nn]
            y[n] = K(x[n, :])

reps=10000
from typing import NamedTuple

F=[F30, Fn0, F3mixed,F3func_kernal, F3func_kernal_arg]
Ns=10**np.arange(1,7)

result= dict(time=np.zeros((len(Ns),len(F)),dtype=float),
             N=np.asarray((Ns)),
            name=np.full((len(F),),' ',dtype=object))

for n, N in enumerate(Ns):
    mask = np.random.rand(N) > .1
    index = np.flatnonzero(mask).astype(np.int32)
    x1 = np.round(np.random.rand(N, 3) * 1000, 0)

    for nf, f in enumerate(F):
        x = x1.copy()
        out = np.zeros((N,), dtype=x1.dtype)
        # make arg list tuple
        result['name'][nf] = f.__name__
        arg = (x,out,index)

        if 'F3func_kernal_arg' in f.__name__:
            t = timeit(lambda: f(x1, out, index, K3), setup=lambda: f(x1, out, index, K3), number=reps)
        else:
            t = timeit(lambda: f(x1,out,index), setup=lambda: f(x1,out,index), number=reps)

        result['time'][n, nf] = t
        print(f'{n:02} {N:9,d} check {out.sum()} {t:6.3f} sec  {(t / reps) * 1000:5.1f} ms  \t {f.__name__}, ')

prop_cycle = plt.rcParams['axes.prop_cycle']
default_colors = prop_cycle.by_key()['color']

fig,axs = plt.subplots(2,1,figsize=(7,10))
ax = axs[0]

for nt in range(result['time'].shape[1]):
    ax.plot(result['N'],result['time'][:,nt]*1000/reps,
             label=result['name'][nt] ,c=default_colors[nt])
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('Particles')
ax.set_ylabel('mSec per call')
ax.legend(fontsize=10)

ax = axs[1]
for nt in range(result['time'].shape[1]):
    ax.plot(result['N'],result['time'][:,nt]/result['time'][:,0],
             label=result['name'][nt],c=default_colors[nt] )
ax.set_xscale('log')
ax.set_xlabel('Particles')
ax.set_ylabel('Time relative to F30')
ax.legend(fontsize=10)
ax.set_ylim(.5,2)
plt.show()