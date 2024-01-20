from os import  environ
environ['NUMBA_ENABLE_AVX']='1'
import numba
numba.core
from numba import njit, guvectorize, vectorize

import numpy as np
from timeit import timeit
from matplotlib import pyplot as plt

from oceantracker.util.numba_util import find_simd_code, time_numba_code


@njit
def F_base(x1,x2,out, sel):
    # base case, only given indicies
    for n in sel:
        out[n]=0.
        for m in range(x1.shape[1]):
            out[n] += x1[n, m]*x2[n,m]

@njit
def F1(x1,x2,out,mask):
    # masked all
 for n in range(x1.shape[0]):
     if mask[n]:
        out[n]=0.
        for m in range(x1.shape[1]):
            out[n] += x1[n, m]*x2[n,m]


@njit
def F2(x1,x2,out, sel):
    # split index
     for n in sel:
        out[n] = 0.
        for m in range(x1.shape[1]):
            out[n] += x1[n][m]*x2[n][m]

@njit
def F5(x1,x2,out, sel):
    # 1D kernal
     for n in sel:
        out[n] = F5s(x1[n,:], x2[n,:])

@njit()
def F5s(x1,x2):
    out = 0.
    for m in range(x1.shape[0]):
       out += x1[m]*x2[m]
    return out

N= 10**6
M= 1
reps =1
dt=np.float32
x=np. random.random((N,M)).astype(dt)
y= np. random.random((N,M)).astype(dt)
out=np.empty_like(x)
t_base=[]
t1=[]
t2=[]
t5=[]
frac= np.arange(.1,1,.1)
mask= np.random.choice(a=[False, True], size=(N, ), p=[1-frac[1] , frac[1]])
sel = np.flatnonzero(mask).astype(np.int32)
# check code
time_numba_code(F_base,x,y,out,sel)

F_base(x,y,out,sel)
print('F_base',out.sum())

F1(x,y,out,mask)
print('F1',out.sum())

F2(x,y,out,sel)
print('F2',out.sum())

F5(x,y,out,sel)
print('F5',out.sum())

find_simd_code(F_base,show=True)
find_simd_code(F1,show=True)
find_simd_code(F2,show=True)
find_simd_code(F5,show=True)
if len(F5s.signatures) >0 :
    find_simd_code(F5s,show=True)

for f in frac:
    mask= np.random.choice(a=[False, True], size=(N, ), p=[1-f , f])
    sel = np.flatnonzero(mask).astype(np.int32)

    t_base.append(time_numba_code(F_base,x,y,out,sel,number=reps))
    t1.append(time_numba_code(F1,x,y,out,mask,number=reps ))
    t2.append(time_numba_code(F2,x,y,out,sel,number=reps ))
    t5.append(time_numba_code(F5,x,y,out,sel,number=reps ))

t_base = np.asarray(t_base)
t1 = np.asarray(t1)
t2 = np.asarray(t2)
t5 = np.asarray(t5)

#sqdiff(x, y)
#find_instr(sqdiff,  sig=0)
plt.plot(frac, t_base, label='selected values')
plt.plot(frac,t1,label='masked values')
plt.plot(frac,t2,label='selected values, split index ')
plt.plot(frac,t5,label= 'selected  sub func ')
plt.ylabel('Time per call')
plt.legend()
plt.show(block=True)

plt.plot(frac,t_base/t1,label='masked values')
plt.plot(frac,t_base/t5,label= 'selected  1D sub func ')
plt.ylabel('Time relative to index sel 2D')
plt.legend()
plt.show()

