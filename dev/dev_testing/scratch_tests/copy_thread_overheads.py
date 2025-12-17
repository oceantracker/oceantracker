from IPython.core.pylabtools import figsize
from numba import njit, prange, set_num_threads
import numpy as np
from timeit import timeit
from time import perf_counter
from matplotlib import pyplot as plt


def copy(x, y, sel ):
    for nn in prange(sel.size):
        n = sel[nn]
        for m in range(x.shape[1]):
            y[n,m] = x[n,m]


reps = 100
Ns= 10**np.arange(2,7)

threads= np.asarray([1, 5, 10, 15, 20, 25, 32])
dts = [np.int8,np.int32,np.float32,np.float64]
dts = [np.float64]

dt =np.float64
t0= np.zeros((len(dts), Ns.size,),dtype=np.float64)
time_thread= np.zeros((len(dts), threads.size, Ns.size), dtype=np.float64)

M=3
y = np.ones((20,M), dtype=dt)



for ntype, dt in enumerate(dts):
    s = 0 if np.issubdtype(dt, np.integer) else 0.

    for n, N in enumerate(Ns):
        sel = np.sort(np.flatnonzero(np.random.rand(N) > .2))

        # no threads
        x = np.ones((N,M), dtype=dt)
        y = x.copy()

        F= njit(copy,parallel=False)

        for r in range(reps):
            t0[ntype, n] += timeit(lambda: F(x, y, sel), number=1, setup=lambda: F(x, y, sel))

        F = njit(copy, parallel=True)
        for nt,n_threads in enumerate(threads):
            set_num_threads(n_threads)

            for r in range(reps):
                x = np.ones((N,M), dtype=dt)
                y=x.copy()
                time_thread[ntype,nt, n]   += timeit(lambda: F(x, y, sel), number=1, setup=lambda: F(x, y, sel))


colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
fig,axs= plt.subplots(1,2, figsize=[12,6])

ax = axs[0]

for ntype, dt in enumerate(dts):
    ax.plot(Ns, t0[ntype,:]*1000/reps, ls='--',label='No threads')
    for nt, n_threads in enumerate(threads):
        ax.plot(Ns,  time_thread[ntype, nt, :]*1000/reps, c=colors[nt+1],label=f'Threads{n_threads}')



    ax.set_xlabel('Aray size,N')
    ax.set_ylabel('write/read ms per array sized N')
    ax.set_xscale('log')
    ax.set_yscale('log')

    ax.legend(fontsize=8)
    ax.grid(True)

    plt.title('Copy time')

ax = axs[1]

for ntype, dt in enumerate(dts):

    for n, N in enumerate(Ns):
        ax.plot(threads,  time_thread[ntype, :, n]*1000/reps, c=colors[n],label=f'Particles {N}')

        ax.plot(ax.get_xlim(), t0[ntype, n] * np.ones((2,))*1000 / reps, ls='--',c=colors[n], label='No threads')


    ax.set_xlabel('Threads')
    ax.set_ylabel('write/read ms per array sized N')
    #ax.set_xscale('log')
    ax.set_yscale('log')

    ax.legend(fontsize=8)
    ax.grid(True)

    plt.title('Copy time')


plt.show()

