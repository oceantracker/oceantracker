from numba import njit , prange
import numba
import numpy as np
from timeit import timeit, repeat
from time import perf_counter
numba.float64()

@njit()
def K(x,y):
    sum = 0.
    for m in range(3):
        sum += x[m] * y[m]
    return sum

def F0(x,y,out,index):
    for nn in range(index.size):
        n = index[nn]
        out[n] = 0.
        for m in range(x.shape[1]):
            out[n] += x[n,m] * y[n,m]

def F1_fixed_range(x,y,out,index):
    for nn in range(index.size):
        n = index[nn]
        out[n] = 0.
        for m in range(3):
            out[n] += x[n,m] * y[n,m]

def F2_sum_then_assign(x,y,out,index):
    for nn in range(index.size):
        n = index[nn]
        sum = 0.
        for m in range(3):
            sum += x[n,m] * y[n,m]
        out[n] = sum
def F1_fixed_range_kernal(x,y,out,index):
    for nn in range(index.size):
        n = index[nn]
        out[n] =  K(x[n,:], y[n,:])




reps=1000
N=10**6
index = np.flatnonzero(np.random.rand(N) > .2)

Fs = [F1_fixed_range,F2_sum_then_assign,F1_fixed_range_kernal,
        F1_fixed_range,
        F0,
        F1_fixed_range_kernal,F2_sum_then_assign,
            F1_fixed_range]

for nt, dt in enumerate([np.float32, np.float64]):
    print(f'start {dt.__name__} ')
    for n , F in enumerate(Fs):

        x = np.random.rand(N, 3).astype(dt)
        y = x.copy()
        out= np.zeros((N,))
        f = njit(F)
        f(x, y, out, index)
        if False:
            t= timeit(lambda: f(x,y,out,index),setup=lambda: f(x,y,out,index)  ,number=reps)
        else:
            ts= perf_counter()
            f(x, y, out, index)
            for r in range(reps):
                f(x, y, out, index)
            t = perf_counter()- ts

        if n==0: t0 = t
        print(f'\t {x.dtype} : {t/t0:8.3%}  {t:6.3f} sec  {(t/reps)*1000:5.1f} ms  \t {f.__name__}')


        asm = list(f.inspect_asm().values())[0]
        with open(f'output\{f.__name__}.asm', 'w') as file:
            file.write(asm)

