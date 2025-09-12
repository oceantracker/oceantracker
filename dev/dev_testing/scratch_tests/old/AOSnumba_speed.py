import random

from numba import njit
import numpy as np
from matplotlib import pyplot as plt
from time import perf_counter

@njit()
def F1(a,b,out, active):

    for n in active:
        for m in range(3):
            for l in range(3):
                out[n] = a[n] * b[n,m,l]

@njit()
def F2(ab, out, active):

    for n in active:
        for m in range(3):
            for l in range(3):
                out[n] = ab[n]['a'] * ab[n]['b'][m,l]
def fill_cache():
    X=np.ones((10**3,1),dtype=np.float64)
    X=X.sum() # bring into memory
    return X


N_vals = 10**np.arange(2,7,.5)
M=3
reps=10

fract= np.asarray([.1,.5,.8,1])
times1 = np.ones((N_vals.size,fract.size))
times2 = np.ones((N_vals.size,fract.size))

for n_vals, N in enumerate(N_vals):
    NN = int(N)
    a= np.random.random((NN,))
    b = np.random.random((NN,M,M))
    ab = np.zeros((NN,), dtype=[('a','f8'), ('b', 'f4', (M,M))])
    ab['a'] = a
    ab['b'][:]=np.random.random((NN,M,M))

    out = np.full_like(a,0.)

    # pre compile
    F1(a, b, out, np.arange(1))
    F2(ab, out, np.arange(1))

    for n_fract, f in enumerate(fract):
        sel = np.arange(NN)
        t1,t2, = 0,0
        for n_reps in range(reps):
            sel = np.random.choice(sel,int(f*sel.size),replace=False)
            sel = np.sort(sel)

            # array
            X= fill_cache()
            t0 = perf_counter()
            F1(a, b, out, sel)
            t1 += perf_counter()-t0
            # struct
            X = fill_cache()
            t0 = perf_counter()
            F2(ab, out, sel)
            t2 += perf_counter() - t0

        times1[n_vals, n_fract] = t1 / (n_reps + 1)
        times2[n_vals, n_fract] = t2/(n_reps+1)
        pass


for n in range(times1.shape[1]):
    plt.plot(N_vals,times1[:,n],label=f'{fract[n]}')
    plt.plot(N_vals,times2[:,n],'--',label=f'{fract[n]}')
plt.legend()
plt.xscale('log')
plt.yscale('log')
plt.title(f' times N = {N_vals[-1]:.0f} frac={fract[-1]} {times1[-1,-1]*1000:.0f} ms, {times2[-1,-1]*1000:.0f} ms')
plt.show()

for n in range(times1.shape[1]):
    plt.plot(N_vals,times2[:,n]/times1[:,n],label=f'{fract[n]}')

plt.plot(N_vals,np.ones((N_vals.size,)),'--')
plt.legend()
plt.xscale('log')
plt.show()
