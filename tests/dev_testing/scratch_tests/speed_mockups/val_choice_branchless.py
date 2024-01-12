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

@contextmanager
def perf_stat():
    p = Popen(["perf", "stat", "-p", str(getpid())])
    sleep(0.5)
    yield
    p.send_signal(SIGINT)


@njit
def sqdiff(x, y):
    out = np.empty_like(x)
    for i in range(x.shape[0]):
        out[i] = (x[i] - y[i])**2
    return out

def find_instr(func, keyword, sig=0, limit=5):
    count = 0
    for l in func.inspect_asm(func.signatures[sig]).split('\n'):
        if keyword in l:
            count += 1
            print(func.__name__,'found',l)
            if count >= limit:
                break
    if count == 0:
        print(func.__name__,'No instructions found')

@njit
def F1(x1,x2,out, sel, xmin):
    #
   for n in sel:
        if x2[n] >= xmin:
            out[n] = x2[n]
        else:
            out[n] = x1[n]



@njit
def F2(x1,x2,out,sel, xmin):
   for n in sel:
        #out[n] = (x2[n] >= xmin)*x2[n] + (x2[n] < xmin)*x1[n]
        s = x2[n] >= xmin
        #out[n] = s * x2[n] + (not s) * x1[n]
        out[n] = s * x2[n] + (1-s) * x1[n]

@njit
def F3(x1,x2,out,sel, xmin):
   for n in sel:
        out[n]= x2[n] if x2[n] >= xmin else x1[n]


def show_llvm(f):
    for v, k in f.inspect_asm().items():
        print('xx', f.__name__, v, k)

if __name__ == "__main__":
    N= 10**6

    reps =5
    x=np.random.random((N,))

    y= np.random.random((N,))
    out=np.empty_like(x)
    p=.1
    mask = np.random.choice(a=[False, True], size=(N,), p=[p, 1 - p])
    sel = np.flatnonzero(mask).astype(np.int32)

    xmin = 0.1
    F1(x, y, out, sel, xmin)
    print(F1.signatures)
    find_instr(F1, keyword='subp', sig=0)
    F2(x, y, out, sel, xmin)
    print(F2.signatures)
    find_instr(F2, keyword='subp', sig=0)

    F3(x, y, out, sel, xmin)
    print(F2.signatures)
    find_instr(F3, keyword='subp', sig=0)

    xmins=np.arange(0,1.2,.005)
    t1 = []
    t2 = []
    t3 = []

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

    t1=np.asarray(t1)
    t2 = np.asarray(t2)
    t3 = np.asarray(t3)

    print('times',t1.mean(),t2.mean(),t3.mean())
    plt.plot(xmins,t2/t1)
    plt.plot(xmins, t3 / t1)

    plt.xlabel('Probability of branching, ie x < xmin')
    plt.ylabel('Time out = (a>xmin) * x1 + = (a>xmin) * x1  no branch/ time branching')
    plt.grid()
    plt.show(block=True)

    #with perf_stat():
    #    F2(x, y, out, sel)
