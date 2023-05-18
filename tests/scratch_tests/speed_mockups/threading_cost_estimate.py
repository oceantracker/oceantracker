import numpy as np
from numba import njit,set_num_threads, prange
import timeit
import psutil
import platform


def F(A,work):
    s=0.
    for n in prange(A.size):
        for w in range(work):
            s += A[n]
    return s

def test_treading_cost(N=10**4, repeats=10, work=1):
    
    A=np.random.rand(N)   

    phyiscal_cores = np.arange(1,psutil.cpu_count(logical=False)).astype(np.int32)


    # compare non-parallel to // for differing number of threads
    
    # time non-parallel version
    F0 = njit(F,parallel=False)
    F0(A,work) # compile for thread count
    t0= np.asarray(timeit.repeat(lambda  : F0(A,work),  number =repeats)) 
    t0_out=np.asarray([t0.min(),t0.mean(),t0.max()  ])
    
    # parallel/threaded version 
    t1_out = np.zeros(( phyiscal_cores.size,3))
    F1 = njit(F,parallel=True)

    for n in range(phyiscal_cores.size):
            set_num_threads(phyiscal_cores[n])
            F1(A,work) # compile for thread count
            t1= np.asarray(timeit.repeat(lambda  : F1(A,work),  number =repeats)) 
            t1_out[n-1,0] = t1.min()  
            t1_out[n-1,1] = t1.mean()
            t1_out[n-1,2] = t1.max()

    return t0_out, t1_out, phyiscal_cores    


if __name__ == "__main__":

    from matplotlib import pyplot as plt 
    colours= [u'r', u'b', u'g', u'c', u'm', u'y', u'k']
    linestyle =['solid','dashed']
    marker =['x','+']
    fig,ax = plt.subplots()
    for n_work, work in enumerate( [1, 10]):
        for n, N in enumerate([10**3,10**4,10**5,10**6]):
            t0_out, t1_out, phyiscal_cores = test_treading_cost(N=N, work=work)
            # plot curves
            ax.plot(phyiscal_cores,t0_out[1]/t1_out[:,1],c=colours[n],label = f'N={N:1.0e}, work={work:3d}',linestyle =linestyle[n_work])
        

            #ax.scatter(1, t0_out[1],c=colours[n],marker=marker[n_work])
    
    #ax.set_xscale('log')
    #ax.set_yscale('log')
    ax.set_xlim([1,phyiscal_cores[-1]])


    ax.plot(ax.get_xlim(),np.ones((2,)),c=[.8, .8,.8],linestyle='dashed')
    ax.set_xlabel('Threads')
    ax.set_ylabel('Speed relative to non-parallel')
    ax.legend(prop={'size': 8})
    ax.set_title(platform.processor())
    fig.savefig('threadcost_estimate.png',dpi=600)
    plt.show()
    

   
