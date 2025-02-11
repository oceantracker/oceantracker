from numba import  njit, prange, set_num_threads
import numpy as np
from timeit import timeit
from matplotlib import  pyplot as plt

@njitOT()
def kernal(a,b):
    out =0.
    for m in range(a.shape[0]):
        for p in range(a.shape[1]):
            out = a[m,p]*a[p,m] + b[m,p]
    return  out


@njitOT()
def F_base(A,B,out,sel, work):
    for n in sel:
        for w in range(work):
            out[n] = kernal(A[n, ...],B[n, ...])

@njitOT(parallel=True, nogil=True)
def FS(S,out, sel, work):
    for nn in prange(sel.size):
        n= sel[nn]
        for w in range(work):
            out[n] = kernal(S['A'][n, ...],S['B'][n, ...])


if __name__ == "__main__":
    Work= [1,2, 3, 5, 10,15, 20]

    n_part=np.asarray([10 ** 1,10 ** 2,10**3, 10 ** 4, 10 ** 5, 10 ** 6])
    #n_part = np.asarray([10 ** 1, 10 ** 3, 10 ** 4])
    t0= np.zeros((len(n_part),len(Work)))
    t0s = np.zeros((len(n_part),len(Work)))
    t0AOS = np.zeros((len(n_part), len(Work)))
    t0AOSs = np.zeros((len(n_part), len(Work)))
    num = 10
    M= 3
    set_num_threads(3)

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

            F_base(A, B,out,ids, w)
            out = np.zeros((N,))
            t0s[n, m] = timeit(lambda: F_base(A, B, out, ids, w), number=num)
            t0[n, m]= timeit(lambda: F_base(A, B, out,id, w),number=num)

            FS(S, out, ids, w)
            t0AOSs[n, m] = timeit(lambda: FS(S, out, ids, w), number=num)
            t0AOS[n, m] = timeit(lambda: FS(S, out, id, w), number=num)

    # plot agaist particles
    for m in [0]: #[0, t0.shape[1]-1]:
        plt.plot(n_part, t0[:,m] / t0s[0,m], label=f'unsorted {Work[m]:2d}')
        plt.plot(n_part, t0s[:,m] / t0s[0,m ], label=f'sorted {Work[m]:2d}')
        plt.plot(n_part, t0AOS[:, m] / t0s[0, m], label=f' structure unsorted {Work[m]:2d}')
        plt.plot(n_part, t0AOSs[:, m] / t0s[0, m], label=f' structure sorted {Work[m]:2d}')

    print(A.nbytes / 10 ** 6)
    plt.xscale('log')
    plt.yscale('log')
    #plt.plot([1,n_part[-1]],[10,n_part[-1]],c=(.8,.8,.8))
    plt.legend()
    plt.grid()
    plt.show()

    # efect of sorting
    for m in [0,t0.shape[1]-1]:
        plt.plot(n_part, t0s[:, m] / t0[:, m], label=f' {Work[m]:2d}')
    plt.xscale('log')
    plt.ylabel('time, sorted/unsorted')
    plt.legend()
    plt.show()

    # efect of array of structures
    for m in [0,t0.shape[1]-1]:
        plt.plot(n_part, t0AOSs[:, m] / t0s[:, m], label=f'sorted {Work[m]:2d}')
        plt.plot(n_part, t0AOS [:, m] / t0s[:, m], label=f'unsorted {Work[m]:2d}')
    plt.xscale('log')
    plt.ylabel('time, aos sorted/ sorted')
    plt.legend()
    plt.show()

    # effect of work
    for n in [0,t0.shape[0]-1]: #range(0,t0.shape[0],2):
        plt.plot(Work, t0s[n, :].T / t0s[n, 0].T, label=f'sorted{ n_part[n]:2d}')
        plt.plot(Work, t0[n,:].T / t0s[n, 0].T, label=f'unsorted{ n_part[n]:2d}')
        plt.plot(Work, t0AOS[n, :].T / t0s[n, 0].T, label=f'sorted structure{n_part[n]:2d}')
    plt.xlabel('time/time sorted[0]')
    plt.legend()
    plt.show()



