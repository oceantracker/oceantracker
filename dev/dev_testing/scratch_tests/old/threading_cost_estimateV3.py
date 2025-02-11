import numpy as np
from numba import njit,set_num_threads, prange
import timeit
import psutil
import platform


def F(A,B, C):

    for n in prange(A.shape[0]):
        for m in range(A.shape[1]):
            A[n,m] += B[n,m] * C[n,m]


def test_treading_cost(N, repeats=10):
    
    A=np.random.rand(N,3)
    B=A.copy()
    C = A.copy()
    phyiscal_cores = np.arange(1,psutil.cpu_count(logical=True)).astype(np.int32)


    # compare non-parallel to // for differing number of threads
    
    # time non-parallel version

    
    # parallel/threaded version 
    t = np.zeros(( phyiscal_cores.size,))
    F1 = njit(F,parallel=True)

    for n in range(phyiscal_cores.size):
            set_num_threads(phyiscal_cores[n])
            F1(A,B, C) # compile for thread count
            t[n]= np.asarray(timeit.timeit(lambda  : F1(A,B, C),  number =repeats))

    F1 = njit(F,parallel=False)
    F1(A,B,C)
    tnp = timeit.timeit(lambda: F1(A,B, C), number=repeats)
    return t, phyiscal_cores , tnp


if __name__ == "__main__":

    from matplotlib import pyplot as plt 
    colours= [u'r', u'b', u'g', u'c', u'm', u'y', u'k']
    linestyle =['solid','dashed']
    marker =['x','+']
    fig1,ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    for n, N in enumerate([10**4,10**5,10**6]):
        t, phyiscal_cores, tnp = test_treading_cost(N=N)
        # plot curves
        ax1.plot(phyiscal_cores,tnp/t,c=colours[n],label = f'N={N:1.0e}')
        ax2.plot(phyiscal_cores,t/N*10**6, c=colours[n], label=f'N={N:1.0e}')

        

            #ax.scatter(1, t0_out[1],c=colours[n],marker=marker[n_work])
    
    #ax.set_xscale('log')
    #ax.set_yscale('log')
    ax1.set_xlim([1,phyiscal_cores[-1]])


    ax1.plot(ax1.get_xlim(),np.ones((2,)),c=[.8, .8,.8],linestyle='dashed')
    ax1.plot(ax1.get_xlim(),ax1.get_xlim(), c=[.8, .8, .8], linestyle='dashed')
    ax1.set_xlabel('Threads')
    ax1.set_ylabel('Speed relative to non-parallel')
    ax1.legend(prop={'size': 8})
    ax1.set_title(platform.processor())
    fig1.savefig('threadcost_estimate.png',dpi=600)

    ax2.legend(prop={'size': 8})
    #ax2.set_yscale('log')

    plt.show()
    

   
