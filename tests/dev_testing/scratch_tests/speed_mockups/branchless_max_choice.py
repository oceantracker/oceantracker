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


@njit
def F1(x1,sel, a):
    #  take x1 only if > xmin
   for n in sel:
        if x1[n] >= a:
            x1[n] = a


@njit
def F2(x1,sel, a):
   for n in sel:
        x1[n] = max(x1[n], a)

if __name__ == "__main__":
    N= 10**6

    reps =20
    ty= np.float64
    x=np.random.random((N,)).astype(ty)

    p=.1
    mask = np.random.choice(a=[False, True], size=(N,), p=[p, 1 - p])
    sel = np.flatnonzero(mask).astype(np.int32)

    xmin = 0.1
    F1(x, sel, xmin)
    F2(x, sel, xmin)


    xmins=np.arange(0.,1., .01)
    t1 = []
    t2 = []



    for xmin in xmins:

        t0= perf_counter()
        for r in range(reps):
            F1(x, sel, xmin)
        t1.append(perf_counter()-t0)

        t0= perf_counter()
        for r in range(reps):
            F2(x, sel, xmin)
        t2.append(perf_counter() - t0)


    t1=np.asarray(t1)
    t2 = np.asarray(t2)

    print('times',t1.mean(),t2.mean())
    plt.plot(xmins,t2/t1)


    plt.xlabel('Probability of branching, ie x < xmin')
    plt.ylabel('Relative time = run  time/ runtime branching')
    plt.grid()
    plt.show(block=True)

    #with perf_stat():
    #    F2(x, y, out, sel)
