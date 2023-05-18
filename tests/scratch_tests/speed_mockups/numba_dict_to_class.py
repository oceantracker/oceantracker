import numpy as np
from numba import types as nbt, typed, njit, typeof
from numba.experimental import jitclass
from oceantracker.util import numba_util

def add0(x, y):
    return x +y

#@njit()
def add(c):
    return np.sum(c.data)


d={'x':np.zeros((2,2)),'z0':2.}
a=numba_util.numba_class_from_dict(d)
print(a.x,a.z0)
print(typeof(a))
x=.1
y=.1
print('xy',x,y)
F= numba_util.njitter(add0,[typeof(x),typeof(y)])
print('add0', F(x,y))

#F= numba_util.njitter(add,[a])
#print(F(a))