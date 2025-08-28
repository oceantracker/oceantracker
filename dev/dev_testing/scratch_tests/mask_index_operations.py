import numpy as np
from time import perf_counter
from matplotlib import pyplot as plt
from numba import njit, prange, set_num_threads

@njit
def worker(a, b, w):
    s = 0.
    for m in range(w):
        s += a[m]*b[m]
    return  s

@njit()
def index_vals_not_para(x1,x2,out, index, w):
   for n in index:
       out[n] = worker(x1[n, :], x2[n, :], w)

@njit(parallel=True)
def index_vals_parallel(x1,x2,out, index,w):
   for nn in  prange(index.size):
       n= index[nn]
       out[n] = worker(x1[n, :], x2[n, :], w)
@njit()
def mask_vals_not_para(x1,x2,out, mask,w):
   for n in range( mask.size):
       if not mask[n]: continue
       out[n] = worker(x1[n, :], x2[n, :], w)

@njit(parallel=True)
def mask_vals_parallel(x1,x2,out, mask, w):
   for n in prange( mask.size):
       if not mask[n]: continue
       out[n] = worker(x1[n, :], x2[n, :], w)


if __name__ == "__main__":

    #N= int(4.2*10**6)
    N= 10**6
   # N = 10 ** 3

    work = 100
    reps = 50
    ty= np.int32
    probs = np.asarray([.05, .15, .8])
    Fs=[ index_vals_parallel,mask_vals_parallel,  ]
    x1 = np.random.random((N, work))
    x2 = np.random.random((N, work))
    fracs =np.asarray([.001,.01,.05,.1,.15,.2,.4,.5, .6,.8,.9, 1. ])

    cores=np.asarray([1, 5, 15], dtype=np.int32)
    d = {}

    for F in Fs:
        fname = F.__name__
        d[fname] =np.zeros((cores.size, fracs.size), dtype=np.float64)

        for nc, c in enumerate(cores):

            set_num_threads(c)
            for nfrac, frac in  enumerate(fracs):
                Mask = np.random.choice([False,True], size=(N,), p=[1. -frac, frac])
                #print(frac,frac*N,Mask.sum())
                Sel = np.flatnonzero(Mask)
                Out = np.full((N,), -1, dtype=x1.dtype)

                s = Sel if 'index' in fname else Mask
                F(x1,x2,Out,s,work)

                t = 0
                for r in range(reps):
                    sel = Sel.copy()
                    mask = Mask.copy()
                    out = Out.copy()
                    s = sel if 'index' in fname else mask
                    tt= perf_counter()
                    F(x1, x2, out, s,work)
                    t += perf_counter()-tt

                print(fname,'frac=', frac,'cores=',c,out.sum())
                d[fname][nc, nfrac] = t*1000/reps # msec per call

    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']


    for nc, c in enumerate(cores):
        for name, item in d.items():
            lt =  '-' if 'index' in name else '--'
            plt.plot(fracs, item[nc, :], lt, c=colors[nc],
                     label=f'{name}  cores={c}')
    plt.xlabel('Fraction operated on')
    plt.ylabel(' time masked, msec per time step')
    plt.grid()
    plt.title(f'work={work}')
    plt.legend(fontsize=6)
    plt.show()

    for nc, c in enumerate(cores):
        for name, item in d.items():
            lt =  '-' if 'index' in name else '--'
            base = d[name.replace('mask', 'index')][nc, :]
            plt.plot(fracs, item[nc, :]-base, lt,c=colors[nc],
                     label=f'{name}, cores={c}')
    plt.title(f'work={work}')
    plt.xlabel('Fraction operated on')
    plt.ylabel(' time masked - index, msec per time step')
    plt.grid()
    plt.legend(fontsize=8)
    plt.show()

    for nc, c in enumerate(cores):
        for name, item in d.items():
            lt = '-' if 'index' in name else '--'
            base = d[name.replace('mask','index')][nc, :]
            plt.plot(fracs, item[nc, :]/base,lt,c=colors[nc],
                      label=f'{name}  cores={nc}')

    plt.xlabel('Fraction operated on')
    plt.ylabel('Relative time = masked/ indexed')
    plt.grid()
    plt.legend(fontsize=8)
    plt.xscale('log')
    plt.yscale('log')
    plt.title(f'work={work}')
    plt.show()


