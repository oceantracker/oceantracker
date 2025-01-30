# https://pythonspeed.com/articles/speeding-up-numba/

from numba import njit
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
            out[n] = n
            nfound +=1
    return out[:nfound]

@njit
def comp_function(status,val,out, cf):
    nfound = 0
    for n in range(status.size):
        if cf(status[n],val):
            out[n] = n
            nfound += 1

    return out[:nfound]

if __name__ == "__main__":
    N= int(4.2*10**6)

    reps = 100
    ty= np.int32

    cf = _get_comparison('gteq')
    Fs=[comp_explict, comp_function]
    stat_max=10
    vals =np.arange(stat_max).astype(np.int8)
    d={}
    for nval, val in  enumerate(vals):
        status = np.random.randint(stat_max, size=(N,)).astype(np.int8)
        out = np.full_like(status, -1, dtype=np.int8)
        for F in Fs:
            fname= F.__name__
            if fname == 'comp_explict':
                F(status,val,out)
                if False:
                    F(status.astype(np.int32), val, out)
                    F(status.astype(np.int64), val, out)
            else:
                F(status, val, out, cf)

            if fname not in d: d[fname]=np.zeros((vals.size,))
            t0= perf_counter()
            for r in range(reps):
                if fname == 'comp_explict':
                    F(status, val, out)
                else:
                    F(status, val, out, cf)
            d[fname][nval] = (perf_counter()-t0)*1000/reps # msec per call

    for name, item in d.items():
        plt.plot(vals, item, label=f'{name}')



    plt.xlabel('Probability of branching, ie x < xmin')
    plt.ylabel('Relative time = run  time/ runtime branching')
    plt.grid()
    plt.legend()
    plt.show(block=True)


