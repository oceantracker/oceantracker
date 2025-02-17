import numpy as np
from time import perf_counter
from matplotlib import pyplot as plt
from numba import njit, prange, set_num_threads

@njit
def worker(a, b, w):
    s = 0.
    for n in range(w):
        for m in range(3):
            s += a[m]*b[m]
    return  s

@njit()
def index_vals(x1,x2,out, index, w):
   for n in index:
       out[n] = worker(x1[n, :], x2[n, :], w)

@njit(parallel=True)
def index_vals_parallel(x1,x2,out, index,w):
   for nn in  prange(index.size):
       n= index[nn]
       out[n] = worker(x1[n, :], x2[n, :], w)
@njit()
def mask_vals(x1,x2,out, mask,w):
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
    #N = 10 ** 4


    reps = 50
    ty= np.int32
    probs = np.asarray([.05, .15, .8])
    Fs=[index_vals,mask_vals,
        index_vals_parallel,mask_vals_parallel,  ]
    x1 = np.random.random((N, 3))
    x2 = np.random.random((N, 3))
    fracs =np.asarray([.001,.01,.05,.1,.15,.2,.4,.5, .6,.8,.9, 1. ])
    d={}
    cores=np.asarray([2, 8], dtype=np.int32)
    work = np.asarray([ 1,10])

    for nc, c in enumerate(cores):
        set_num_threads(c)

        for nw, w in enumerate(work):
            for nfrac, frac in  enumerate(fracs):
                Mask = np.random.choice([False,True], size=(N,), p=[1. -frac, frac])
                #print(frac,frac*N,Mask.sum())
                Sel = np.flatnonzero(Mask)
                Out = np.full((N,), -1, dtype=x1.dtype)


                for F in Fs:

                    fname= F.__name__
                    s = Sel if 'index' in fname else Mask
                    F(x1,x2,Out,s,w)

                    if fname not in d: d[fname]=np.zeros((cores.size, fracs.size,work.size))
                    t = 0
                    for r in range(reps):
                        sel = Sel.copy()
                        mask = Mask.copy()
                        out = Out.copy()
                        s = sel if 'index' in fname else mask
                        tt= perf_counter()
                        F(x1, x2, out, s,w)
                        t += perf_counter()-tt

                    print(fname,'work=',w,'frac=', frac,'cores=',c,out.sum())
                    d[fname][nc, nfrac, nw] = t*1000/reps # msec per call

    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

    for name, item in d.items():
        for nc, c in enumerate(cores):
            if 'parallel' in name:
                lt = ':' if c == cores[0] else '--'
                core_lab = c
            else:
                lt = '-'
                core_lab = 1
            for nw, w in enumerate(work):
                plt.plot(fracs, item[nc, :,nw], lt,
                         label=f'{name} work={w}, cores={core_lab}')
    plt.xlabel('Fraction operated on')
    plt.ylabel(' time masked, msec per time step')
    plt.grid()
    plt.legend(fontsize=6)
    plt.show()

    for name, item in d.items():
        if 'index' in name: continue
        for nc, c in enumerate(cores):
            if 'parallel' in name:
                lt = ':' if c == cores[0] else '--'
                core_lab = c
            else:
                lt = '-'
                core_lab = 1
            for nw, w in enumerate(work):
                base = d[name.replace('mask', 'index')][nc, :, nw]
                plt.plot(fracs, item[nc, :,nw]-base, lt,
                         label=f'{name} work={w}, cores={core_lab}')



    plt.xlabel('Fraction operated on')
    plt.ylabel(' time masked - index, msec per time step')
    plt.grid()
    plt.legend(fontsize=8)
    plt.show()

    for nn ,(name, item) in enumerate(d.items()):
        if 'index' in name: continue
        for nc, c in enumerate(cores):
            if 'parallel' in name:
                lt = ':' if c == cores[0] else '--'
                core_lab= c
            else:
                lt = '-'
                core_lab = 1
            for nw, w in enumerate(work):
                base = d[name.replace('mask','index')][nc, :,nw]
                plt.plot(fracs, item[nc, :,nw]/base,lt,
                          label=f'{name} work={w} cores={core_lab}')

    plt.xlabel('Fraction operated on')
    plt.ylabel('Relative time = masked/ indexed')
    plt.grid()
    plt.legend(fontsize=8)
    plt.xscale('log')
    plt.yscale('log')

    plt.show()


