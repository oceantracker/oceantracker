import numba as nb
from matplotlib import  pyplot as plt
import numpy as np
from time import perf_counter

def loop(A,B, active):
    for nn in nb.prange(active.size):
        n = active[nn]
        #continue
        for m in range(A.shape[1]):
            B[n,m] = A[n,m]


reps=10
frac = .9
N=10**7


mask = np.random.rand(N) < frac
sel = np.flatnonzero(mask)
colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

M=[0, 1,10,100]
for nm, m in enumerate(M):
    A = np.random.rand(N, m)
    B = A.copy()

    F = nb.njit(loop)
    F(A,B,sel)
    t0=perf_counter()
    for r in range(reps):
        F(A,B,sel)
    t1 = perf_counter()-t0
    print('serial', t1)

    nthreads = np.arange(1, nb.get_num_threads())
    time=np.zeros((nthreads.size,), dtype=np.float64)
    F = nb.njit(loop, parallel=True)
    F(A,B,sel)

    for n, nt in enumerate(nthreads):
        nb.set_num_threads(nt)
        A = np.random.rand(N, m)
        B = A.copy()
        t0 = perf_counter()
        for r in range(reps):

            F(A,B,sel)
        time[n] = perf_counter()-t0
        print(m, 'threads=',nt, time[n])


    plt.plot(nthreads, time*1000/reps, label=f'work {m}', c = colors[nm], ls = '--')
    plt.plot(nthreads, t1*np.ones(nthreads.size)*1000/reps, label=f'work = # array columns= {m}', c = colors[nm], ls = '-')

plt.yscale('log')
plt.xlabel('threads')
plt.ylabel('time, msec per rep')
plt.legend()
plt.title('10 million particles , copy work # columns')
plt.savefig('paralell_threads01.png')
plt.show()


