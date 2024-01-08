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
def F1(x1,x2,out, sel):
    #
   for n in sel:
   #for n in range(x1.shape[0]):
        if x1[n] > 0.:
            out[n] = x2[n] / x1[n]
        else:
            out[n] = 0.

        if x2[n] > 0.:
            out[n] += x1[n] / x2[n]
        else:
            out[n] += 0.


@njit
def F2(x1,x2,out,sel):
   for n in sel:
    #
    #for n in range(x1.shape[0]):
        out[n] =  (x2[n]/x1[n]) if x1[n] > 0. else 0.
        out[n] += (x1[n] / x2[n]) if x2[n] > 0. else 0.

def show_llvm(f):
    for v, k in f.inspect_asm().items():
        print('xx', f.__name__, v, k)

if __name__ == "__main__":
    N= 10**6

    reps =5
    x=np.ones((N,),dtype=np.float64)

    y= np.full_like(x,1.)
    out=np.empty_like(x)

    p=.5
    mask = np.random.choice(a=[False, True], size=(N,), p=[p, 1 - p])
    sel = np.flatnonzero(mask).astype(np.int32)

    F1(x, y, out, sel)
    print(F1.signatures)
    find_instr(F1, keyword='subp', sig=0)
    F2(x, y, out, sel)
    print(F2.signatures)
    find_instr(F2, keyword='subp', sig=0)

    prob=np.linspace(0,1.,10)
    t1 = []
    t2=[]
    for m in range(prob.size):
        x[:] = 1.
        x[ np.random.random((N,)) <  prob[m]] = 0.

        t0= perf_counter()
        for r in range(reps):
            F1(x, y, out, sel)
        t1.append(perf_counter()-t0)

        t0= perf_counter()
        for r in range(reps):
            F2(x, y, out, sel)
        t2.append(perf_counter() - t0)

    t1=np.asarray(t1)
    t2 = np.asarray(t2)


    print('times',t1,t2)
    plt.plot(prob,t1)
    plt.plot(prob, t2)
    plt.show(block=True)



    #with perf_stat():
    #    F2(x, y, out, sel)
