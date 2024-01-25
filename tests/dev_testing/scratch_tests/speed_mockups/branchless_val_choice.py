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


@njitOT
def F1(x1,x2,out, sel, xmin):
    #
   for n in sel:
        if x1[n] >= xmin:
            out[n] = x1[n]
        else:
            out[n] = x2[n]

@njitOT
def F1a(x1,out, sel, xmin):
    #
   for n in sel:
        if x1[n] >= xmin:
            out[n] = x1[n]


@njitOT
def F2(x1,x2,out,sel, xmin):
   for n in sel:
        #out[n] = (x2[n] >= xmin)*x2[n] + (x2[n] < xmin)*x1[n]
        #s = x2[n] >= xmin
        #out[n] = s * x2[n] + (not s) * x1[n]
        #out[n] = s * x2[n] + (1-s) * x1[n]
        out[n] = branchless_value_choice(x1[n],x2[n],x1[n] >= xmin)
@njitOT()
def branchless_value_choice(a,b,cond):
    return cond*a + (not cond) *b
@njitOT
def F3(x1,x2,out,sel, xmin):
   for n in sel:
        out[n]= x1[n] if x1[n] >= xmin else x2[n]


def show_llvm(f):
    for v, k in f.inspect_asm().items():
        print('xx', f.__name__, v, k)

if __name__ == "__main__":
    N= 10**6

    reps =20
    ty= np.float64
    x=np.random.random((N,)).astype(ty)

    y= np.random.random((N,)).astype(ty)

    out=np.empty_like(x)
    p=.1
    mask = np.random.choice(a=[False, True], size=(N,), p=[p, 1 - p])
    sel = np.flatnonzero(mask).astype(np.int32)

    xmin = 0.1
    F1(x, y, out, sel, xmin)
    F2(x, y, out, sel, xmin)
    F3(x, y, out, sel, xmin)
    F1a(x, out, sel, xmin)

    xmins=np.arange(0.,1., .01)
    t1 = []
    t2 = []
    t3 = []
    t1a =[]

    for xmin in xmins:

        t0= perf_counter()
        for r in range(reps):
            F1(x, y, out, sel, xmin)
        t1.append(perf_counter()-t0)

        t0= perf_counter()
        for r in range(reps):
            F2(x, y, out, sel, xmin)
        t2.append(perf_counter() - t0)

        t0= perf_counter()
        for r in range(reps):
            F3(x, y, out, sel, xmin)
        t3.append(perf_counter() - t0)

        t0= perf_counter()
        for r in range(reps):
            F1a(x, out, sel, xmin)
        t1a.append(perf_counter() - t0)

    t1=np.asarray(t1)
    t2 = np.asarray(t2)
    t3 = np.asarray(t3)
    t1a = np.asarray(t1a)

    print('times',t1.mean(),t2.mean(),t3.mean(),t1a.mean())
    plt.plot(xmins,t2/t1,label='branch less out= cond*x1 + (not cod) *b')
    plt.plot(xmins, t3 / t1,label= 'out = x1 if () else x2')
    plt.plot(xmins, t1a / t1,label='one sided condition')

    plt.xlabel('Probability of branching, ie x < xmin')
    plt.ylabel('Relative time = run  time/ runtime branching')
    plt.grid()
    plt.legend()
    plt.show(block=True)

    #with perf_stat():
    #    F2(x, y, out, sel)
