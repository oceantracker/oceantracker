from numba import njit, prange
import  numpy as np
from time import perf_counter
from oceantracker.interpolator.util.triangle_interpolator_util import _get_single_BC_cord_numba

para= False
@njit(parallel=para)
def F1a(a, b,c, out):
    # work on nth row view
    for m in prange(a.shape[0]):
        for i in range(a.shape[1]):
            out[m,i] = a[ m,i] + b[m,i]*c[i,m]

@njit()
def F1b(a,b,c, out,n):
    for m in range(a.shape[1]):
        for i in range(a.shape[2]):
            out[n, m,i] = a[n, m,i] + b[n, m,i]*c[n,i,m]

@njit()
def F1c(n,m,a,b,c, out):
    for i in range(a.shape[2]):
        out[n,m,i] = a[n,m,i] + b[n,m,i]*c[n,i,m]
    #out[n, m] = F1(a[n, m],b[n, m])

@njit()
def F2a(a,b,c, out):
    for n in range(a.shape[0]):
        F1a(a[n, :], b[n, :], c[n, :], out[n, :])
@njit()
def F2b(a,b,c, out):
    for n in range(a.shape[0]):
        F1b(a, b,c, out,n)
@njit()
def F2c(a,b,c, out):
    for n in range(a.shape[0]):
        for m in range(a.shape[1]):
               F1c(n,m,a,b,c, out)
@njit()
def F2d(a,b,c,out):
    for n in range(a.shape[0]):
        for m in range(a.shape[1]):
            for i in range(a.shape[2]):
                out[n,m,i] =  a[n,m,i]+ b[n,m,i]*c[n,i,m]

N=10**7
M=2
A= np.full((N, M, 3*M), 0.,dtype=np.float64)
B= A.copy()
C= A.copy()
O =A.copy()

F2a(A,B,C,O)
F2b(A,B,C,O)
F2c(A,B,C,O)
F2d(A,B,C,O)

reps= 100
t0= perf_counter()
for n in range(reps):
    F2a(A,B,C, O)
print('F2a',perf_counter()-t0)

t0= perf_counter()
for n in range(reps):
    F2b(A,B,C ,O)
print('F2b',perf_counter()-t0)

t0= perf_counter()
for n in range(reps):
    F2c( A,B, C,O)

print('F2c',perf_counter()-t0)

t0= perf_counter()
for n in range(reps):
    F2d( A,B,C, O)

print('F2d',perf_counter()-t0)