import numpy as np
from time import perf_counter
from matplotlib import  pyplot as plt
from importlib import reload
import os

#os.environ['NUMBA_NUM_THREADS'] ='32'
import numba as nb
#


def numba_setup():

    global nb
    os.environ['NUMBA_NUM_THREADS'] ='30'
    reload(nb)

def get_data(Nodes, time_steps):
    A = np.sin(np.arange(Nodes))
    B = np.cos(np.arange(Nodes))
    t= np.sin(np.arange(time_steps))
    A = (t.reshape(-1,1)*A.reshape(1,-1))
    B = (t.reshape(-1,1)*B.reshape(1,-1))
    tri= np.random.randint(Nodes, size = (Nodes,3))
    return A, B, tri

@nb.njit
def load1(a,b,tri):
    s = 0.
    for m in range(3):
        s += a[tri[m]]*b[tri[m]]
    return  s


@nb.njit
def base_eval_interp(A,B,tri, cells, C, active):
    for n in active:
        C[n] =load1(A, B,tri[cells[n],:])

@nb.njit(parallel=True)
def prange_eval_interp(A, B, tri, cells, C, active):
    for i in nb.prange(active.shape[0]):
        n = active[i]
        C[n] =load1(A, B,tri[cells[n],:])

if __name__ == "__main__":
    pass
    #numba_setup()

    frac= .9
    data=dict()
    N = np.asarray([1,  100, 500,10**3, 10 ** 4, 10 ** 5, 10 ** 6])
    time_steps= 100
    Nodes = 10**5


    A, B, tri = get_data(Nodes,time_steps)
    funcs =  [base_eval_interp, prange_eval_interp]
    threads =np.asarray([1, 5, 10 ,15, 30, 60])
    data=dict()
    for F in funcs:
       data[F.__name__] = dict(N=N, time=np.zeros((N.size,threads.size),dtype=np.float64), threads=threads)

    for nth, n_thread in enumerate(threads):
        nb.set_num_threads(n_thread)
        print('Threads', nb.config.NUMBA_NUM_THREADS)

        for nn , n in enumerate(N):
            sel = np.random.rand(n) < frac
            active = np.flatnonzero(sel)
            cells  = np.random.randint(Nodes, size=(n,))
            C = np.full((n,), 0., dtype=A.dtype)

            for F in funcs:
                F(A[0,:],B[0,:],tri, cells,C,active[:2]) # compile code

                # time code
                t0 = perf_counter()
                for nt in range(time_steps):
                    F(A[nt, :], B[nt, :],tri, cells, C, active)

                data[F.__name__]['time'][nn, nth]= perf_counter()-t0

                check_sum = np.sum(C[active])
                print(n, F.__name__,check_sum )


        # do plots
    plt.plot(data['base_eval_interp']['N'], data['base_eval_interp']['time'][:, nth] * 1000 / time_steps, label=f'base_eval_interp')

    for nth, n_thread in enumerate(threads):
        for f in funcs[1:]:
            name = f.__name__
            plt.plot(data[name]['N'], data[name]['time'][:,nth]*1000/time_steps, label = f'{name}, threads={n_thread}')

    plt.ylabel('Time per time step, msec')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    plt.grid()
    plt.show()
    m = np.inf
    for nth, n_thread in enumerate(threads):
        for f in funcs[1:]:
            name= f.__name__
            r= data[name]['time'][:,nth]/data['base_eval_interp']['time'][:,nth]
            plt.plot(data[name]['N'], r, label=f'{name}, threads={n_thread}, min = {np.round(r.min(),4)}')

    plt.xlabel('Number of particles')
    plt.ylabel('Speed relative to single core')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    plt.grid()
    plt.show()

    for nn , n in enumerate(N):
        for f in funcs[1:]:
            name = f.__name__
            r= data[name]['time'][nn,:]/data['base_eval_interp']['time'][nn,:]
            plt.plot(data[name]['threads'], r, label=f'{name}, N={n}, min = {np.round(r.min(),4)}')

    plt.xlabel('Threads')
    plt.ylabel('Speed relative to single core')
    #plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    plt.grid()
    plt.show()