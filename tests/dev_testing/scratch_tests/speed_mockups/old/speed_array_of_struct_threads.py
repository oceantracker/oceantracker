from numba import  njit, prange, set_num_threads
import numpy as np
from timeit import timeit
from matplotlib import  pyplot as plt

@njit()
def kernal(a,b):
    out =0.
    for m in range(a.shape[0]):
        for p in range(a.shape[1]):
            out = a[m,p]*a[p,m] + b[m,p]
    return  out

def FS(S,out, sel, work):
    for nn in prange(sel.size):
        n= sel[nn]
        for w in range(work):
            out[n] = kernal(S['A'][n, ...],S['B'][n, ...])


if __name__ == "__main__":
    ntheads= 1 + np.arange(32)
    Work= [1,10]

    n_part=np.asarray([ 10**4,10**5,10 ** 6])
    #n_part = np.asarray([10 ** 1, 10 ** 3, 10 ** 4])
    t0 = np.zeros((len(n_part), len(Work)))
    tp = np.zeros((len(n_part), len(Work), len(ntheads)))

    num = 10
    M= 3


    for p,nt in enumerate(ntheads):
        set_num_threads(nt)
        for m, w  in enumerate(Work):
            for n , N in enumerate(n_part):

                id= np.random.choice(np.arange(N),size=int(.1*N),replace=False)
                ids = np.sort(id)  # these are sorted in order
                id=ids.copy()
                np.random.shuffle(id)

                #print(ids[:10])
                #print(np.sort(id)[:10])
                out = np.zeros((N,))
                A = np.random.rand(N, M, M)
                B = A.copy()
                S=np.zeros((N,),np.dtype([('A',np.float64, (M,M)), ('B',np.float64, (M,M))]))
                np.copyto(S['A'], A)
                np.copyto(S['B'], B)

                F_base = njit(FS, parallel=False, nogil=True)
                F_base(S, out, ids, w)
                t0[n, m] = timeit(lambda: F_base(S, out, id, w), number=num)

                Fp = njit(FS,parallel=True, nogil=True)
                Fp(S, out, ids, w)
                tp[n, m, p] = timeit(lambda: Fp(S, out, id, w), number=num)

    # plot agaist particles
    for n in range(tp.shape[0]):
        for m in range(tp.shape[1]):
            plt.plot(ntheads,t0[n, m]/ tp[n, m, :]  , label=f' structure unsorted work  {Work[m]:2d}  {n_part[n]:2d}')

    print(t0*10e3)
    print(S.nbytes / 10 ** 6)

    #plt.plot([1,n_part[-1]],[10,n_part[-1]],c=(.8,.8,.8))
    plt.legend()
    plt.grid()
    plt.show()


