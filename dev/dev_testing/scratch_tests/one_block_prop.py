from collections import namedtuple

from numba import njit, prange
import numpy as np
from timeit import timeit
from time import perf_counter
bc=True
@njit(boundscheck=bc)
def F0(x,y,weights, index):

    for nn in range(index.size):
        n = index[nn]
        y[n]=0.
        for m in range(x.shape[1]):
            y[n]+= weights[n,m]*x[n,m]


@njit(boundscheck=bc)
def Fviews(prop, index):

    for nn in range(index.size):
        n = index[nn]
        prop.y[n] = 0.
        for m in range(prop.x.shape[1]):
            prop.y[n] += prop.weights[n, m] * prop.x[n, m]

@njit(boundscheck=bc)
def Fnumbaviews(prop,prop_views, index):
    x = prop[:, prop_views.x[0]:prop_views.x[1]]
    y = prop[:, prop_views.y[0]:prop_views.y[1]]
    weights = prop[:, prop_views.weights[0]:prop_views.weights[1]]
    #x = prop[:, :3]
    #y = prop[:, 3]
    #weights = prop[:, 4:]

    for nn in range(index.size):
        n = index[nn]
        y[n] = 0.
        for m in range(x.shape[1]):
            y[n] += weights[n, m] * x[n, m]
reps = 50
nf=10
N=10**6
M=3
x= np.random.randn(N,M)
y = np.zeros((N,))
x1 = x.copy()
weights = x.copy()
index = np.flatnonzero(np.random.rand(N) > 0.1)

names= ('x','y','weights')
vars = (x,y.reshape((-1,1)),weights)
prop_block = np.concat(vars, axis=1)

NTPnamed = namedtuple('NTPnamed',names)
prop_named = NTPnamed(x,y,weights)

# views
views=[]
incidies=[]
n0 = 0
for m, v in enumerate(vars):
    views.append( prop_block[:, n0:n0+v.shape[1]] )
    incidies.append( [n0,n0+v.shape[1]] )
    n0 = n0 + v.shape[1]
NTPview = namedtuple('NTPview',names)
prop_view = NTPview(*views)
prop_incidies = NTPview(*incidies)
# compile and check
print(timeit(lambda :Fviews( prop_view,  index), number=1))
print(timeit(lambda :Fviews( prop_view,  index), number=1))

F0(x,y,weights,index)
s1=y.sum()

Fviews( prop_named,  index)
s2=prop_named.y.sum()

Fviews(prop_view,  index)
s3=prop_view.y.sum()

F0(prop_view.x, prop_view.y, prop_view.weights, index)
s4=prop_view.y.sum()

F0(prop_block[:, :3], prop_block[:, 3], prop_block[:, 4:], index)
s5=prop_block[:,3].sum()

Fnumbaviews(prop_block, prop_incidies, index)
s6=prop_block[:,3].sum()
print(s1,s2,s3,s4,s5,s6)

t0 =perf_counter()
for nr in range(reps):
    F0(x,y,weights,index)
t1=perf_counter()-t0
print('1:F0',t1/reps)



t0 = perf_counter()
for nr in range(reps):
    Fviews(prop_named,  index)
t2 = perf_counter() - t0
print('2:prop named as tuple', t2/reps, t2 / t1)
Fviews( prop_view,  index)

t0 = perf_counter()
for nr in range(reps):
    Fviews( prop_view,  index)
t3 = perf_counter() - t0
print('3:prop named tuple view', t3/reps, t3 / t1)

t0 = perf_counter()
for nr in range(reps):
    F0(prop_named.x,prop_named.y,prop_named.weights,index)
t4 = perf_counter() - t0
print('4:F0  prop_named as args', t4/reps, t4 / t1)

t0 = perf_counter()
for nr in range(reps):
    F0(prop_block[:,:3],prop_block[:,3],prop_block[:,4:],index)
t5 = perf_counter() - t0
print('5:F0 prop_block views', t5/reps, t5 / t1)

t0 = perf_counter()
for nr in range(reps):
    Fnumbaviews(prop_block, prop_incidies, index)
t6 = perf_counter() - t0
print('6:F0 prop_block views', t6/reps, t6 / t1)