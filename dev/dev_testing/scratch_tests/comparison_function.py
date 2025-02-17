# https://pythonspeed.com/articles/speeding-up-numba/

from numba import njit, prange
import numba
import numpy as np
from timeit import timeit, repeat
from time import perf_counter
from matplotlib import pyplot as plt

from subprocess import Popen
from contextlib import contextmanager
from os import getpid
from time import sleep
from signal import SIGINT
from oceantracker.util.numba_util import njitOT
from numba import njit

from oceantracker.particle_properties.util.particle_comparisons_util import  _get_comparison
@njit
def comp_explict(status,val,out):
    nfound = 0
    for n in range(status.size):
        if status[n] >= val:
            out[nfound] = n
            nfound +=1
    return out[:nfound]

@njit(inline='never')
def cf(a,b): return a>=b

@njit()
def comp_explict_branchless(status,val,out, cf):
    nfound = 0
    for n in range(status.size):
        ok =  cf(status[n],val)
        nfound += ok
        out[nfound] = n


    return out[:nfound]



@njitOT
def comp_function(status,val,out, cf):
    nfound = 0
    for n in range(status.size):
        if cf(status[n],val):
            out[nfound] = n
            nfound += 1

    return out[:nfound]

@njit
def comp_mask(status,val,mask, out):

    for n in prange(status.size):
        mask[n] = status[n] >= val

    return mask

if __name__ == "__main__":
    N= int(4.2*10**6)
    #N= 10**6
    reps = 100
    ty= np.int32
    probs = np.asarray([.05, .15, .8])
    Status = np.random.choice(3, size=(N,),p= probs).astype(np.int8)
    Out = np.full_like(Status, -1, dtype=np.int32)
    Mask = np.full_like(Out, False, dtype=bool)
    Fs=[comp_explict,comp_explict_branchless, comp_function, comp_mask]
    stat_max=10
    vals =np.arange(stat_max).astype(np.int8)
    d={}
    for nval, val in  enumerate(vals):

        for F in Fs:

            fname= F.__name__
            if fname in ['comp_explict' ] :
                F(Status,val,Out)

            elif fname== 'comp_mask' :
                F(Status, val, mask, Out)
            else:
                F(Status, val, Out, cf)

            if fname not in d: d[fname]=np.zeros((vals.size,))
            t = 0
            for r in range(reps):
                out = Out.copy()
                status = Status.copy()
                mask = Mask.copy()
                tt= perf_counter()
                if fname in ['comp_explict']:
                    F(status, val, out)
                elif fname == 'comp_mask':
                    F(status, val, mask, out)
                else:
                    F(status, val, out, cf)
                t += perf_counter()-tt
            d[fname][nval] = t*1000/reps # msec per call

    for name, item in d.items():
        plt.plot(vals, item, label=f'{name}')



    plt.xlabel('Probability of branching, ie x < xmin')
    plt.ylabel('Relative time = run  time/ runtime branching')
    plt.grid()
    plt.legend()
    plt.title(f'status prob {str(probs)}')
    plt.show(block=True)


