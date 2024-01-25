from numba import njit, vectorize,float64, bool_,guvectorize, boolean
import numba
import os
import numpy as np
import timeit
from time import perf_counter

def find_instr(func, keyword, sig=0, limit=5):
    count = 0
    for l in func.inspect_asm(func.signatures[sig]).split('\n'):
        if keyword in l:
            count += 1
            print(func.__name__,'found',l)
            if count >= limit:
                break
    if count == 0:
        print(func.__name__,'No instructions found')
    print( '    ',func.signatures)





@njitOT
def sqdiff(x, y):
    out = np.empty_like(x)
    for i in range(x.shape[0]):
        out[i] = (x[i] - y[i])**2
    return out

@njitOT
def F1a(x,y,out,mask):
    out = np.empty_like(x)
    for i in range(x.shape[0]):
        if mask[i]:
            out[i] = x[i] - y[i]


@njitOT
def F1(x,y,out, mask):
    for n in range(x.shape[0]):
        if mask[n]:
            for m in range(x.shape[1]):
                out[n,m] = x[n,m] + y[n,m]



@njitOT
def F3(x,y,out,sel):
    for n in sel:
        for m in range(x.shape[1]):
            out[n,m] = x[n,m] + y[n,m]


N= 10**6
M=10
reps =2
x=np.ones((N,M),dtype=np.float64)
y= np.full_like(x,1.)
out =np.full_like(x,0.)

p= .1
mask= np.random.choice(a=[False, True], size=(N, ), p=[p, 1-p])
import timeit

os.environ['NUMBA_ENABLE_AVX'] ='1'
mask=mask.astype(np.int32)
sel = np.flatnonzero(mask).astype(np.int32)
F1(x[:1],y[:1],out,mask[:1])
F3(x[:1],y[:1],out, sel[:1])

t0 = perf_counter()
for n in range(reps):
    F1(x,y,out,mask)
t1 = perf_counter() -t0

t0= perf_counter()
for n in range(reps):
    F3(x,y,out,sel)

t3 = perf_counter() -t0
print('F1,F3',t1,t3)
find_instr(F1, keyword='subp', sig=0)


F1a(x[:,0].copy(), y[:,0].copy(),out, mask)
find_instr(F1a, keyword='subp', sig=0)

find_instr(F3, keyword='subp', sig=0)

sqdiff(x, y)
find_instr(sqdiff, keyword='subp', sig=0)