import numpy as np
from numba import types as nbt, typed, njit, typeof, prange

from oceantracker.util import numba_util
from oceantracker.util.numpy_util import  numpy_structure_from_dict
def add0(x, y):
    return x +y

def sum(a):
    s = 0.

    for n in prange(a.x.shape[0]):
        m = a.id[3]
        s += a.x[n] + a.x[m]
    return s/a.x.size


d={'x':np.random.rand(100_000),'id': np.random.randint(0,10,size=30),'p':1}
a=numba_util.numba_class_from_dict(d)
print('a',a.x.shape)
print(typeof(a))

x=.1
y=.1
print('xy',x,y)
F= numba_util.njitter(add0,[typeof(x),typeof(y)])
print('add0', F(x,y))

F= numba_util.njitter(sum,[typeof(a)], parallel=True)

print( F(a))

s= numpy_structure_from_dict(d)

print( sum(s))