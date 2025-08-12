from psutil import cpu_count
import  os
physical_cores = cpu_count(logical=False)
import  numpy as np
from numba import njit, get_num_threads, set_num_threads, prange, get_thread_id
set_num_threads(physical_cores)
from time import perf_counter

@njit()
def sel_part(x):
    return x > 0.1

@njit()
def IDfind(x,ID):
    nfound=0
    for n in range(x.size):
        if sel_part(x[n]):
            ID[nfound] = n
            nfound += 1
    return ID[:nfound]
@njit(parallel=True)
def IDfind_thread(x,IDthread,found_per_thread,starts,IDsplit,out):
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
        for n in range(found_per_thread[nthread]):
            out[ ns + n] = IDthread[nthread, n]

    return out[:found]


reps = 10
Ns= np.asarray(10**np.arange(2,7))
t1 = np.full((Ns.size,),0,dtype=np.float64)
t2 = t1.copy()

print(Ns)
for n ,N in enumerate(Ns):
    ID = np.full((N,),0,dtype=np.int32)
    IDthread =  np.full((physical_cores,N //physical_cores +1),0,dtype=np.int32)
    IDperThread= np.full((physical_cores,),0,dtype=np.int32)
    starts= IDperThread.copy()
    IDs = np.arange(N,dtype=np.int32)
    IDsplit = np.array_split(IDs, get_num_threads())
    x= np.random.rand(N)
    out1= ID.copy()
    out2 = ID.copy()


    # compile code
    sel1 = IDfind(x,out1)
    sel2 = IDfind_thread(x,IDthread,IDperThread,starts,IDsplit,out2)
    print('check',N,sel1.size,  np.abs(sel1 - sel2).sum())

    t0 = perf_counter()
    for m in range(reps):
        sel1 = IDfind(x,out1)
    t1[n] = perf_counter()-t0

    t0 = perf_counter()
    for m in range(reps):
        sel2 = IDfind_thread(x,IDthread,IDperThread,starts,IDsplit, out2)
    t2[n] = perf_counter()-t0


from matplotlib import  pyplot as plt
plt.plot(Ns,t1,label='loop')
plt.plot(Ns,t2,label='threaded find loop')
plt.legend()
plt.grid('on')
plt.show()




