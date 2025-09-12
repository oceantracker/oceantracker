from os import  environ
#environ['NUMBA_PARALLEL_DIAGNOSTICS']= '4'

from oceantracker.util import  numba_util
from numba import njit
import numpy as np
from time import perf_counter

@njit()
def T0(a,b,sel):
    for n in sel:
        for m in range(a.shape[1]):
            a[n,m] = b[n, m]

@njit()
def T1(a,b,sel):
    for n in sel:
        for m in range(3):
            a[n,m] = b[n, m]
@njit()
def T2(a,b,sel):
    for n in sel:
            a[n, 0] = b[n, 0]
            a[n, 1] = b[n, 1]
            a[n, 2] = b[n, 2]

@njit()
def T3(a,b,sel):
    for n in sel:
        a[n, 0], a[n, 1] ,a[n,2]= b[n, 0], b[n, 1],b[n,2]


N=10**6
M=3
reps=100
sel =np.sort(np.random.choice(N,int(.9*N)))





for n in range(4):
    a = np.random.random((N, M))
    b = np.random.random((N, M))
    match n:
        case 0:
            F= T0
            lab= 'variable sized loop'
        case 1:
            F = T1
            lab = 'fixed sized loop'
        case 2:
            F = T2
            lab = 'two line '
        case 3:
            F = T3
            lab = 'one line '

    F(a,b,sel) # compile

    t0 = perf_counter()
    for r in range(reps):
        F(a,b,sel)
    t = perf_counter()-t0
    if n ==0 : tref= t
    print(lab,t,t/tref)



#c =T.inspect_asm(T.signatures[0])
#print(c)
