import os
os.environ['NUMBA_ENABLE_AVX']= str(-1)
os.environ['NUMBA_DEBUG_CACHE']=str(1)

#os.environ['NUMBA_CPU_FEATURES'] = '-avx,-avx2,-sse'
from numba import njit, vectorize,float64, bool_,guvectorize, boolean, jit

import numba

import numpy as np
from timeit import timeit
from time import perf_counter




def add1(x,y,mask):
    for n in range(x.shape[0]):
        if mask[n]==0: continue
        for m in range(x.shape[1]):
            x[n, m] +=  2. * y[n, m] ** 2 + y[n,m]

def add2(x,y,sel):
    for n in sel:
        for m in range(x.shape[1]):
            x[n,m] += 2.*y[n,m]**2 + y[n,m]

def find_instr(func, keyword, sig=0, limit=5):
    count = 0
    for l in func.inspect_asm(func.signatures[sig]).split('\n'):
        if keyword in l:
            count += 1
            print(l)
            if count >= limit:
                break
    if count == 0:
        print('No instructions found')

N= 10**6
M=50
reps =5
x=np.ones((N,M),dtype=np.float64)
y= np.full_like(x,1.)
p= .8
mask= np.random.choice(a=[False, True], size=(N, ), p=[p, 1-p])

#os.environ['NUMBA_ENABLE_AVX'] ='1'
#os.environ['NUMBA_CPU_FEATURES']= '+avx,+avx2'

mask=mask.astype(np.int32)
sel = np.flatnonzero(mask).astype(np.int32)


f=njit(add2)
f(x,y,sel[:1])
print('add2  njit',timeit(lambda : f(x,y,sel),number=reps ))
print(f.signatures)

f=njit(add2,fastmath=True)
f(x,y,sel[:1])
print('add2  njit fastmath',timeit(lambda : f(x,y,sel),number=reps ))
find_instr(f, keyword='subp', sig=0)
print(f.signatures)

f=njit(add1,fastmath=True)
f(x,y,mask[:1])
print('add1  njit ',timeit(lambda : f(x,y,mask),number=reps ))
find_instr(f, keyword='subp', sig=0)
print(f.signatures)

print('abx denm')
@jit(nopython=True)
def sqdiff(x, y,out):

    for i in range(x.shape[0]):
        for m in range(x.shape[1]):
            out[i,m] = (x[i,m] - y[i,m])**2
    return out




N=10**6
M=10
reps=500
reps=500
x32 = np.random.random((N,M)).astype(np.float32)
y32 = np.random.random((N,M)).astype(np.float32)
out32 = np.empty_like(x32)
sqdiff(x32, y32,out32)
for n in range(reps):
    sqdiff(x32, y32,out32)

x64 = x32.astype(np.float64)
y64 = y32.astype(np.float64)
out64 = np.empty_like(x64)
sqdiff(x64, y64,out64)
for n in range(reps):
    sqdiff(x64, y64,out64)

print(sqdiff.signatures)
print(timeit(lambda : sqdiff(x32, y32,out32), number=20))
find_instr(sqdiff, keyword='subp', sig=0)
print(timeit(lambda : sqdiff(x64, y64,out64),number=20))
find_instr(sqdiff, keyword='subp', sig=1)

