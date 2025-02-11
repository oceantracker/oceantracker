from numba import njit
import numpy as np
from matplotlib import pyplot as plt

@njit
def F1(x1): return
@njit
def F2(x1,x2): return
@njit
def F3(x1,x2, x3): return
@njit
def F4(x1,x2, x3,x4): return
@njit
def F5(x1,x2, x3,x4,x5): return
@njit
def F6(x1,x2, x3,x4,x5,x6): return
@njit
def F7(x1,x2, x3,x4,x5,x6,x7): return
from oceantracker.util.numba_util import time_numba_code
@njit
def F8(x1,x2, x3,x4,x5,x6,x7,v8): return
from oceantracker.util.numba_util import time_numba_code
N=100
M=10
num=1000
x_array= [np.random.random((N,)) for x in range(M)]
x_int = [int(x) for x in range(M)]
x_float = [float(x) for x in range(M)]
x_bool = [True for x in range(M)]
dtype=[('name', '<U10'), ('age', '<i4'), ('weight', '<f4')]
x_rec = [np.zeros((2,0),dtype=dtype) for x in range(M)]
Funcs=[F1,F2,F3,F4,F5,F6,F7,F8]

# numbers of signatures
data_sig= {}
for nx in range(len(Funcs)):
    d = dict(time=[], sigs=[], n_sigs=[])
    for lab, ty in zip(['Bool','Int','Float','Array','Rec Array'],[x_bool,x_int,x_float,x_array,x_rec]):
        F = Funcs[nx]
        args = ty[:nx + 1]
        F(*args)
        t = time_numba_code(F, *args, number=num) * 1e6
        d['time'].append(t)
        d['sigs'].append(F.signatures)
        d['n_sigs'].append(len(F.signatures))
    data_sig.update({f' Num args {nx+1}': d})

for ty, d in data_sig.items():
    plt.plot(d['n_sigs'],d['time'],label=ty)
plt.legend()
plt.xlabel('Number of signatures')
plt.ylabel('Time, mSec')
plt.title('Numba Dispatch time for diff. num. signatures')
plt.show()

data= {}
for lab, ty in zip(['Bool','Int','Float','Array','Rec Array'],[x_bool,x_int,x_float,x_array,x_rec]):
    d= dict(nx=[], time=[])
    for nx in range(len(Funcs)):
        F = Funcs[nx]
        args = ty[:nx+1]
        t= time_numba_code(F, *args, number=num)*1e6
        print(lab, f'{type(ty[0])} {len(args)}  dargs, time={t*10**6},mSec')
        d['nx'].append(len(args))
        d['time'].append(t)
    data.update({lab: d})


data_m= {}
for lab, ty in zip(['Float+Array','Array+Rec Array'],
                    [[x_float,x_array],
                     [x_array,x_rec]]):
    d= dict(nx=[], time=[])
    args=[]
    for nx in range(1,len(Funcs),2):
        F = Funcs[nx]
        args.append(ty[0][((nx+1)//2)])
        args.append(ty[1][((nx+1)//2)])
        t= time_numba_code(F, *tuple(args), number=num)*1e6
        print(lab, f'{type(ty[0])} {len(args)}  dargs, time={t*10**6},mSec')
        d['nx'].append(len(args))
        d['time'].append(t)
    data_m.update({lab: d})

for ty, d in data.items():
    plt.plot(d['nx'],d['time'],label=ty)
for ty, d in data_m.items():
    plt.plot(d['nx'],d['time'],'--',label=ty)
plt.legend()
plt.xlabel('Number of function arguments')
plt.ylabel('Time, mSec')
plt.title('Numba Dispatch time for diff. arg types')
plt.show()


