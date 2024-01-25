# https://pythonspeed.com/articles/speeding-up-numba/

from numba import njit
import numba
import numpy as np
from timeit import timeit, repeat
from time import perf_counter
from matplotlib import pyplot as plt

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

@njitOT
def F1(x1,x2,out, sel):
    #
   for n in sel:
       for m in range(x1.shape[1]):
            out[n,m] = x2[n,m] * x1[n,m]



@njitOT
def F2(x1,x2,out,mask):
   for n in range(mask.size):
       if mask[n]:
           for m in range(x1.shape[1]):
                out[n,m] = x2[n,m] * x1[n,m]


if __name__ == "__main__":
    N= 10**6
    M=1
    reps =5
    x=np.random.random((N,M)).astype(np.float64)
    y = np.random.random((N,M)).astype(np.float64)
    out=np.empty_like(x)

    prob=np.linspace(0,1.,10)
    t1 = []
    t2=[]
    for m in range(prob.size):
        p =  prob[m]
        mask = np.random.choice(a=[False, True], size=(N,), p=[p, 1 - p])
        sel = np.flatnonzero(mask).astype(np.int32)
        F1(x, y, out, sel)
        t0= perf_counter()
        for r in range(reps):
            F1(x, y, out, sel)
        t1.append(perf_counter()-t0)

        x= x.copy()
        y = y.copy()
        F2(x, y, out, mask)
        t0= perf_counter()
        for r in range(reps):
            F2(x, y, out, mask)
        t2.append(perf_counter() - t0)

    t1=np.asarray(t1)
    t2 = np.asarray(t2)
    find_instr(F1, keyword='subp', sig=0)
    find_instr(F2, keyword='subp', sig=0)


    print('times',t1,t2)
    plt.plot(prob,t1)
    plt.plot(prob, t2)
    plt.show(block=True)



    #with perf_stat():
    #    F2(x, y, out, sel)
