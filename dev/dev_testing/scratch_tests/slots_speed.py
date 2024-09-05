from timeit import timeit, repeat
from dataclasses import dataclass
from time import perf_counter
import numpy as np
class Dummy():
    d=1.

class C(object):
    def __init__(self):

        self.a=1.
        self.b=1.
        self.C = Dummy()
class S(object):
    __slots__ = ['a', 'b','c','C']
    s= 1
    def __init__(self):

        self.a=1.
        self.b=1.
        self.C = Dummy()
@dataclass
class D(object):
    a=1.
    b=1.
    C=Dummy()
N=10**7


a=C()
t0= perf_counter()
for n in range(N):  x = a.C.d
t1= perf_counter()-t0

a=D()
t0= perf_counter()
for n in range(N):  x = a.C.d
t2= perf_counter()-t0

a=S()
t0= perf_counter()
for n in range(N):  x =a.C.d
t3= perf_counter()-t0

t = np.asarray([t1,t2,t3])/N*10**6

print(t,'mSec')
print(t[1:]/t[0],' ratios to class')






