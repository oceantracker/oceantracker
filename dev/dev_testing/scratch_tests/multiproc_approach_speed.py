import numpy as np
from time import perf_counter
from matplotlib import  pyplot as plt
from importlib import reload
import os
from psutil import  cpu_count
import numba as nb
#



def get_data(Nodes, time_steps):
    A = np.sin(np.arange(Nodes))
    t= np.sin(np.arange(time_steps))
    A = (t.reshape(-1,1)*A.reshape(1,-1))
    tri= np.random.randint(Nodes, size = (Nodes,3))

    A= np.tile(A[:,:,np.newaxis],(1,1,3))
    B = A.copy()*np.random.random(A.shape)
    return A, B, tri

@nb.njit
def load1(a,b,tri):
    s = 0.
    for m in range(3):
        for ncomp in range(a.shape[1]):
            s += a[tri[m],ncomp]*b[tri[m],ncomp]
    return s


@nb.njit
def no_threads_eval_interp(A,B,tri, cells, C, active):
    for n in active:
        C[n] =load1(A, B,tri[cells[n],:])

@nb.njit(parallel=True)
def prange_eval_interp(A, B, tri, cells, C, active):
    for i in nb.prange(active.shape[0]):
        #if nb.get_thread_id() > 0: print('xxID', nb.get_thread_id())
        n = active[i]
        C[n] =load1(A, B,tri[cells[n],:])

if __name__ == "__main__":


    frac= .9
    data=dict()
    N = np.asarray([1,  100, 500,10**3, 10 ** 4, 10 ** 5, 10 ** 6, 10**7, 10**8])
    #N = N[:6]
    time_steps= 24
    Nodes = 10**5


    A, B, tri = get_data(Nodes,time_steps)
    funcs =  [prange_eval_interp]
    threads = np.asarray([1,2, 5, 10 ,15,20, 25, 30, 60])
    max_threads = max(cpu_count(logical=False) - 1, 1)
    threads = threads[threads < max_threads]

    print('max threads=',max_threads)

    # set up data ouput dict
    data=dict(no_threads_eval_interp=dict(N=N, time=np.zeros((N.size,),dtype=np.float64), threads=threads))
    for F in funcs:
       data[F.__name__] = dict(N=N, time=np.zeros((N.size,threads.size),dtype=np.float64), threads=threads)

    for nn , n in enumerate(N):
        sel = np.random.rand(n) < frac
        active = np.flatnonzero(sel)
        cells  = np.random.randint(Nodes, size=(n,))
        C = np.full((n,), 0., dtype=A.dtype)

        # no threads case
        no_threads_eval_interp(A[0,:],B[0,:],tri, cells,C,active[:2]) # compile code
        t0 = perf_counter()
        for nt in range(time_steps):
            no_threads_eval_interp(A[nt, :], B[nt, :], tri, cells, C, active)

        data['no_threads_eval_interp']['time'][nn] = perf_counter() - t0

        print(f'particles {n:,}','Base checksum ',  np.sum(C[active]))

        for nth, n_thread in enumerate(threads):
            nb.set_num_threads(n_thread)
            for F in funcs:
                F(A[0,:],B[0,:],tri, cells,C,active[:2]) # compile code

                # time code
                t0 = perf_counter()
                for nt in range(time_steps):
                    F(A[nt, :], B[nt, :],tri, cells, C, active)

                data[F.__name__]['time'][nn, nth]= perf_counter()-t0


                print(F.__name__,f'particles {n:,}',f'threads { n_thread}', 'checksum=', np.sum(C[active]))


        # do plots
    #1 time  per time step verse particles
    plt.plot(data['no_threads_eval_interp']['N'], data['no_threads_eval_interp']['time'] * 1000 / time_steps, label=f'no_threads_eval_interp')

    for nth, n_thread in enumerate(threads):
        for f in funcs:
            name = f.__name__
            plt.plot(data[name]['N'], data[name]['time'][:,nth]*1000/time_steps, label = f'{name}, threads={n_thread}')

    plt.xlabel('Particles')
    plt.ylabel('Time per time step, msec')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend(fontsize="8")
    plt.grid()
    plt.show()

    #2 time per partilce per time step
    plt.plot(data['no_threads_eval_interp']['N'], data['no_threads_eval_interp']['time'] * 1000 / time_steps / N,
             label=f'no_threads_eval_interp')

    for nth, n_thread in enumerate(threads):
        for f in funcs:
            name = f.__name__
            plt.plot(data[name]['N'], data[name]['time'][:, nth] * 1000 / time_steps / N,
                     label=f'{name}, threads={n_thread}')

    plt.xlabel('Particles')
    plt.ylabel('Time per time step per particle, msec')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend(fontsize="8")
    plt.grid()
    plt.show()

    #3 time per partilce per time step verses threads

    for nn , n in enumerate(N):
        plt.scatter(0,data['no_threads_eval_interp']['time'][nn]  * 1000 / time_steps / N[nn])#,  label=f'no_threads_eval_interp, particles={n:,}')
        for f in funcs:
            name = f.__name__
            plt.plot(data[name]['threads'], data[name]['time'][nn,:]*1000/time_steps/N[nn], label = f'{name}, particles={n:,}')

    plt.ylabel('Time per time step per particle, msec')
    plt.xlabel('Threads')
    plt.yscale('log')
    plt.legend(fontsize="8")
    plt.grid()
    plt.show()



    # realtive timer per particle verses threads
    for nth, n_thread in enumerate(threads):
        for f in funcs:
            name= f.__name__
            r= data[name]['time'][:,nth]/data['no_threads_eval_interp']['time']
            plt.plot(data[name]['N'], r, label=f'{name}, threads={n_thread}, min = {np.round(r.min(),4)}')

    plt.xlabel('Number of particles')
    plt.ylabel('Speed relative to single core')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend(fontsize="8")
    plt.grid()
    plt.show()

    # time per time step verses threads
    for nn , n in enumerate(N):
        for f in funcs:
            name = f.__name__
            r= data[name]['time'][nn,:]/data['no_threads_eval_interp']['time'][nn]
            plt.plot(data[name]['threads'], r, label=f'{name}, N={n}, min = {np.round(r.min(),4)}')

    plt.xlabel('Threads')
    plt.ylabel('Speed relative to single core')
    #plt.xscale('log')
    plt.yscale('log')
    plt.legend(fontsize="8")
    plt.grid()
    plt.show()

