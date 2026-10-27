from psutil import cpu_count

physical_cores = cpu_count(logical=False)

import  numpy as np



from numba import njit, get_num_threads, set_num_threads, prange

threads = 2
set_num_threads(threads)

from time import perf_counter
from dev.dev_testing.scratch_tests.simd.find_smid import asm
@njit()
def sel_part(x):
    return x > 0.1

@njit()
def IDfind(x,ID,sel):
    nfound=0
    for n in sel:
        if sel_part(x[n]):
            ID[nfound] = n
            nfound += 1
    return ID[:nfound]

@njit()
def pack_indicies(ID, nsel):
    nfound = 0
    for nn in range(nsel):
        if ID[nn] > -1:
            ID[nfound] = ID[nn]
            nfound += 1
    return ID[:nfound]

@njit(parallel=True)
def IDfind_twostep(x,ID,sel):

    for nn in prange(sel.size):
        n = sel[nn]
        ID[nn] = n if sel_part(x[n]) else -1

    return  pack_indicies(ID,sel.size)


@njit(parallel=True)
def IDfind_thread(x,IDthread,found_per_thread,starts,IDsplit,out,sel):
    found = 0
    for nthread in prange(found_per_thread.size):
        found_per_thread[nthread] = 0
        for n in IDsplit[nthread]:
            if sel_part(x[n]):
                IDthread[nthread, found_per_thread[nthread]] = n
                found_per_thread[nthread] += 1
                found += 1

    starts[0] = 0
    for n in range(1, found_per_thread.size):
        starts[n] = starts[n-1] + found_per_thread[n-1]

    for nthread in prange(found_per_thread.size):
        ns = starts[nthread]
        #out[ ns:ns + found_per_thread[nthread]] = IDthread[nthread, :found_per_thread[nthread]]
        for n in range(found_per_thread[nthread]):
            out[ ns + n] = IDthread[nthread, n]
    return out[:found]



reps = 10
Ns= np.asarray(10**np.arange(2,7))
t1 = np.full((Ns.size,),0,dtype=np.float64)
t3 = t1.copy()

for nt,  threads in enumerate([2, 4, 8, 10, 30, 45]):
    set_num_threads(threads)
    print(Ns)
    for n ,N in enumerate(Ns):
        ID = np.full((N,),0,dtype=np.int32)
        IDthread =  np.full((physical_cores,N //physical_cores +1),0,dtype=np.int32)
        IDperThread= np.full((physical_cores,),0,dtype=np.int32)
        starts= IDperThread.copy()
        IDs = np.arange(N,dtype=np.int32)
        IDsplit = np.array_split(IDs, get_num_threads())
        x= np.random.rand(N)
        sel = np.flatnonzero(x> .1)
        out1= x.copy()
        out2 = x.copy()
        out3 = x.copy()


        # compile code
        sel1 = IDfind(x,out1,sel)
        sel3 =  IDfind_twostep(x,out3,sel)


        t0 = perf_counter()
        for m in range(reps):
            sel1 = IDfind(x,out1,sel)
        t1[n] = perf_counter()-t0



        t0 = perf_counter()
        for m in range(reps):
            sel3 =  IDfind_twostep(x,out3,sel)
        t3[n] = perf_counter() - t0

        print('threads',threads,'N=', N, sel1.size,' check=', np.abs(sel1 - sel3).sum(),'\t\t\trelative speed=', t3[n]/t1[n])



    from matplotlib import  pyplot as plt
    plt.plot(Ns,t1/t3,label=f'loop,  threads= {threads} ')

    plt.legend()
    plt.xscale('log')
    plt.yscale('log')
    plt.grid('on')
    plt.ylabel('Realtice speed, loop/ twostep')
    plt.xlabel('particles, ms')


plt.show()




