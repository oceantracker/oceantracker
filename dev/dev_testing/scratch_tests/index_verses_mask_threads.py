from psutil import cpu_count
import  os
physical_cores = cpu_count(logical=False)
max_threads = max(physical_cores - 1, 1)
os.environ['NUMBA_NUM_THREADS'] = str(max_threads)

import numba as nb
import numpy as np
from matplotlib import pyplot as plt
from time import perf_counter

parallel = True
@nb.njit()
def work(a,b):
    sum = 0.
    for m in range(a.shape[0]):
        sum += a[m] + b[m]
    return sum
@nb.njit(parallel = parallel)
def F1(A,B,C, sel):
    for nn in  nb.prange(sel.size):
        n = sel[nn]
        C[n] = work(A[n,:],B[n,:])

@nb.njit(parallel = parallel)
def F1mask(A, B, C, mask):
    for n in nb.prange(mask.size):
        if not mask[n]:continue
        C[n] = work(A[n, :], B[n, :])

reps = 5
N=10**6
fracs= np.asarray([1E-5, 1E-3, .1,  .5 ,.75 , 1.])
M = np.asarray([0, 1, 20, 100, 200, 500], dtype=np.int32)
funcs =  [F1,F1mask]
times = np.full((M.size, fracs.size),0, dtype =np.float64)

d={}
for  nm, m in enumerate(M):
    for nfrac, frac in enumerate(fracs):
        A = np.random.rand(N,m)
        B = A.copy()
        C= np.full((N,),0, dtype =np.float64)
        mask = np.random.rand(N) <  frac
        sel = np.flatnonzero(mask)
        for F in funcs:
            name = F.__name__
            if name not in d:
                d[name] = dict(work=M,fracs=fracs, time= times.copy())
           # complile

            if 'mask' in name:
                F(A, B,C, mask[:3])
            else:
                F(A, B, C, sel[:3])

            t0 = perf_counter()
            for r in range(reps):
                if 'mask' in name:
                    F(A, B, C, mask)
                else:
                    F(A, B, C, sel)

            d[name]['time'][nm,nfrac] = perf_counter()-t0

            print(name, C.sum(), sel.size, mask.dtype)
            pass


colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

for name, f in d.items():
    for nfrac, frac in enumerate(f['fracs']):
        lt = '--' if 'mask' in name else '-'
        plt.plot(f['work'], f['time'][:, nfrac], label=f'{name} frac={frac}', c = colors[nfrac], ls = lt)

plt.xscale('log')
plt.yscale('log')
plt.xlabel('Work')
plt.ylabel('Time, sec')
plt.legend()
plt.show()

for name, f in d.items():
    for nwork, work in enumerate(f['work']):
        lt = '--' if 'mask' in name else '-'
        plt.plot(f['fracs'], f['time'][nwork, :], label=f'{name} work={work}',c = colors[nwork], ls = lt)

plt.yscale('log')
plt.xlabel('Frac ')
plt.ylabel('Time, sec')
plt.legend()
plt.show()
