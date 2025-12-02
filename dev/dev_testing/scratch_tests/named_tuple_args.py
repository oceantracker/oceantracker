
from numba import njit , prange
import numba
import numpy as np
from timeit import timeit, repeat
import matplotlib.pyplot as plt
from collections import namedtuple
p=True

@njit(inline='always')
def K5(x1,x2,x3,x4,x5):
    y=0.
    for m in range(3):
        y = x1[m]+x2[m]+x3[m]+x4[m]+x5[m]
    return y

@njit(parallel=p)
def arg5(x1,x2,x3,x4,x5, y,sel):
    for nn in prange(sel.size):
        n = sel[nn]
        y[n]=K5(x1[n,:], x2[n,:], x3[n,:], x4[n,:], x5[n,:])


@njit(parallel=p)
def tuplehom5(xx,y, sel):
    for nn in prange(sel.size):
        n = sel[nn]
        y[n]=K5(xx.x1[n,:],xx.x2[n,:],xx.x3[n,:],xx.x4[n,:],xx.x5[n,:])

@njit(parallel=p)
def tuplehom_array5(xx,y, sel):
    x1 = xx.x1[:]
    x2 = xx.x2[:]
    x3 = np.asarray(xx.x3)
    x4 = np.asarray(xx.x4)
    x5 = np.asarray(xx.x5)
    for nn in prange(sel.size):
        n = sel[nn]
        y[n]=K5(x1[n,:],x2[n,:],x3[n,:],x4[n,:],x5[n,:])

@njit(parallel=p)
def tupleinhom5(xx,y, sel):
    for nn in prange(sel.size):
        n = sel[nn]
        y[n]=K5(xx.x1[n,:],xx.x2[n,:],xx.x3[n,:],xx.x4[n,:],xx.x5[n,:])


reps=1000
from typing import NamedTuple


F=[arg5, tuplehom5,tuplehom_array5, tupleinhom5 ]
Ns=10**np.arange(1,7)

result= dict(time=np.zeros((len(Ns),len(F)),dtype=float),
             N=np.asarray((Ns)),
            name=np.full((len(F),),' ',dtype=object))
nargs =5
for n, N in enumerate(Ns):
    mask = np.random.rand(N) > .2
    index = np.flatnonzero(mask).astype(np.int32)
    x1 = np.round(np.random.rand(N, 3) * 1000, 0)
    out = np.zeros((N,), dtype=x1.dtype)
    inhom_dtype = [np.int64, np.float64, np.int32, np.float32, np.int8, np.float64, ]
    xs_inhom = [x1.copy().astype(ty) for ty in inhom_dtype]

    for nf, f in enumerate(F):


        # make arg list tuple
        result['name'][nf] = f.__name__
        if f.__name__.startswith('arg'):
            x = tuple(x1.copy() for n in range(nargs))
            args = x+(out,index)
        elif f.__name__.startswith('tuplehom'):
            T = namedtuple('T', [f'x{m+1}' for m in range(nargs)])
            args=( T( **{f'x{m+1}':x1.copy() for m in range(nargs)} ),
                  out,index)
        elif f.__name__.startswith('tupleinhom'):
            T = namedtuple('T', [f'x{m + 1}' for m in range(nargs)])
            args = (T(**{f'x{m + 1}': xs_inhom[m] for m in range(nargs)}), out, index)


        t = timeit(lambda: f(*args), setup=lambda: f(*args), number=reps)
        result['time'][n, nf]=t
        f(*args)
        print(f'{n:02} {N:8d} check {out.sum()} {t:6.3f} sec  {(t / reps) * 1000:5.1f} ms  \t {f.__name__}, ')

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
ax.set_ylabel('Time relative to simple args')
ax.legend(fontsize=10)
ax.set_ylim(0,3)


plt.show(block=True)