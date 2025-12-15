from numba import njit, prange
import numpy as np
from timeit import timeit
from time import perf_counter

@njit()
def F0(x,y,weights, index):

    for nn in range(index.size):
        n = index[nn]
        y[n]=0.
        for m in range(x.shape[1]):
            y[n]+= weights[n,m]*x[n,m]
@njit()
def Fm(xs,ys,weights, index):

    for nn in range(index.size):
        n = index[nn]

        for nx in range(len(xs)):
            x = xs[nx]
            y = ys[nx]
            y[n] = 0.
            for m in range(x.shape[1]):
                y[n]+= weights[n,m]*x[n,m]

@njit()
def Fviews(xb, yb, weights, index):
    nw = weights.shape[1]
    for nn in range(index.size):
        n = index[nn]
        for nb in range(nw):
            x = xb[n,nb*nw:nb*nw+nw]
            y = 0.
            w= weights[n,:]
            for m in range(nw):
                y += w[m] * x[m]
            yb[n,nb] = y
reps = 2
nf=10
N=10**7
M=5
x_base= np.random.randn(N,M)
xs =[x_base.copy() for i in range(nf)]
weights = x_base.copy()
index = np.flatnonzero(np.random.rand(N) > 0.1)
y = np.zeros((N,))
ys =[y.copy() for i in range(nf)]

xblock = np.random.randn(N,M*nf)
yblock = np.random.randn(N,nf)

F0(xs[0],y,weights,index)
t0 =perf_counter()
for nr in range(reps):
    for m in range(nf):
        F0(xs[m],y,weights,index)
t1=perf_counter()-t0
print('F0',t1)

Fm(xs, ys, weights, index)
t0 =perf_counter()
for nr in range(reps):
    Fm(xs,ys,weights,index)
t2=perf_counter()-t0
print('mutli',t2,t2/t1)

Fviews(xblock, yblock, weights, index)
t0 =perf_counter()
for nr in range(reps):
    Fviews(xblock, yblock, weights, index)
t3=perf_counter()-t0
print('block',t3,t3/t1)