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

@njitOT
def branch_index(status,val,out):
    nfound = 0
    for n in range(status.size):
        if status[n] >= val:
            out[n] = n
            nfound +=1
    return out[:nfound]

@njitOT
def branchless_index(status,val,out):
    nfound = 0
    for n in range(status.size):
        ok =  status[n] >= val
        out[n] = n
        nfound += ok
    return out[:nfound]


def show_llvm(f):
    for v, k in f.inspect_asm().items():
        print('xx', f.__name__, v, k)

if __name__ == "__main__":
    N= int(2.5*10**6)

    reps = 100
    ty= np.int32


    Fs=[branch_index, branchless_index]
    stat_max=10
    vals =np.arange(stat_max).astype(np.int32)
    d={}
    for nval, val in  enumerate(vals):
        status = np.random.randint(stat_max, size=(N,)).astype(np.int32)
        out = np.full_like(status, -1, dtype=np.int32)

        for F in Fs:
            F(status,val,out)
            if True:
                F(status, val, out.astype(np.int16)) # second signature
                F(status, val, out.astype(np.int8))
            fname= F.__name__
            if fname not in d: d[fname]=np.zeros((vals.size,))
            t0= perf_counter()
            for r in range(reps):
                F(status,val,out)
            d[fname][nval] = (perf_counter()-t0)*1000/reps # msec per call

    for name, item in d.items():
        plt.plot(vals, item, label=f'{name}')



    plt.xlabel('Probability of branching, ie x < xmin')
    plt.ylabel('Relative time = run  time/ runtime branching')
    plt.grid()
    plt.legend()
    plt.show(block=True)


