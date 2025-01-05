from numba import njit, prange
import numpy as np
from time import perf_counter
from matplotlib import  pyplot as plt
def get_data(N, fac_active):
    A = np.sin(np.arange(N))
    B = np.cos(np.arange(N))

    sel = np.random.rand(N) < frac
    active = np.flatnonzero(sel)

    return A, B, active
@njit
def load1(a,b):
    #return np.sin(a)+ np.cos(b)
    return a + b

@njit
def base(A,B,C, active):
    for n in active:
        C[n] =load1(A[n], B[n])

@njit(parallel=True)
def prange1(A,B,C, active):
    for i in prange(active.shape[0]):
        n = active[i]
        C[n] =load1(A[n], B[n])


if __name__ == "__main__":
    pass

    print(load1(1,2))
    frac= .9
    data=dict()
    N= [ 100,10**4,10**5,10**6]
    time_steps= 100
    for F in [base, prange1]:
        t = []
        for n in N:

            A, B, active= get_data(n,frac)
            C= np.full_like(A,0., dtype= np.float64)
            F(A,B,C,active[:2]) # compile code

            # time code
            t0 = perf_counter()
            for nt in range(time_steps):
                F(A, B, C, active)  # compile code
            t.append(perf_counter()-t0)

        data[F.__name__] = dict(N=N, time=np.asarray(t))


    for name, d in data.items():
        plt.plot(d['N'], d['time'], label = name)

    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    plt.show()
    m = np.inf
    for name, d in data.items():
        r= d['time']/data['base']['time']
        plt.plot(d['N'], r, label=f'{name}, min = {r.min()}')

    #plt.ylim([0, 3])
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    plt.show()
