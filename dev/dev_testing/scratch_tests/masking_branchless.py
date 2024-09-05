from numba import njit
import numba
import numpy as np
from timeit import timeit

@njitOT
def sqdiff(x, y):
    out = np.empty_like(x)
    for i in range(x.shape[0]):
        out[i] = (x[i] - y[i])**2
    return out

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

@njitOT
def F1(x1,x2,out, sel):
 for n in sel:
     out[n] = x1[n]**2+ x2[n]**2

@njitOT
def F2(x1,x2,out,mask):
 for n in range(x1.size):
     if mask[n]:
         out[n] = x1[n] ** 2 + x2[n] ** 2
@njitOT
def F3(x1,x2,out,mask):
 for n in range(x1.size):
    #a= mask[n]*x1[n] ** 2
    #b = mask[n] * x2[n] ** 2
    out[n] =  x1[n] * x2[n]

    #out[n] = (x1[n]- x2[n]) ** 2
N= 10**7

reps =5
x=np.ones((N,),dtype=np.float32)
y= np.full_like(x,1.)
out=np.empty_like(x)

p= .5
mask= np.random.choice(a=[False, True], size=(N, ), p=[p, 1-p])
sel = np.flatnonzero(mask).astype(np.int32)
F1(x,y,out,sel)
t1= timeit(lambda : F1(x,y,out,sel),number=reps )
find_instr(F1, keyword='subp', sig=0)
print(F1.signatures)
F2(x,y,out,mask)
t2= timeit(lambda : F2(x,y,out,mask),number=reps )
find_instr(F2, keyword='subp', sig=0)

F3(x,y,out,mask)
t3= timeit(lambda : F3(x,y,out,mask),number=reps )
find_instr(F3, keyword='subp', sig=0)

print('times',t1,t2,t3)

sqdiff(x, y)
find_instr(sqdiff, keyword='subp', sig=0)

