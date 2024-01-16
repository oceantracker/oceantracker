from os import  environ
environ['NUMBA_ENABLE_AVX']='1'
import numba
numba.core
from numba import njit, guvectorize, vectorize

import numpy as np
from timeit import timeit
from matplotlib import pyplot as plt

@njit
def sqdiff(x, y):
    out = np.empty_like(x)
    for i in range(x.shape[0]):
        out[i] = (x[i] - y[i])**2
    return out

def find_instr(func, sig=0, limit=2):
    count = 0
    keywords = ['addp','subp']
    #keywords=['ADDPS', 'SUBPS', 'MULPS', 'DIVPS', 'RCPPS', 'SQRTPS', 'MAXPS', 'MINPS', 'RSQRTPS']
    #keywords= [k.lower() for k in keywords]
    for l in func.inspect_asm(func.signatures[sig]).split('\n'):
        if any([(v in l) for v in keywords]) :
            count += 1
            print(func.__name__,'found',l)
            if count >= limit:
                break
    if count == 0:
        print(func.__name__,'No instructions found')

@njit
def F1(x1,x2,out):
    for n in range(x1.shape[0]):
        for m in range(x1.shape[1]):
            out[n, m] = x1[n, m]**2+ x2[n,m]**2

@njit
def F2(x1,x2,out,mask):
 for n in range(x1.shape[0]):
     if mask[n]:
        for m in range(x1.shape[1]):
            out[n, m] = x1[n, m]**2+ x2[n,m]**2


@njit
def F3(x1,x2,out, sel):
    for n in sel:
        for m in range(x1.shape[1]):
            out[n, m] = x1[n, m]**2+ x2[n,m]**2

@njit
def F4(x1,x2,out, mask):
    # run on transpose
     for m in range(x1.shape[0]):
         F4s(x1[m,:],x2[m,:],out[m,:],mask)
@njit
def F4s(x1,x2,out,mask):
      for n in range(x1.shape[0]):
                if mask[n]:
                    out[n] = x1[n]**2+ x2[n]**2
@njit
def F5(x1,x2,out, mask):
     for m in range(x1.shape[1]):
         F5s(x1[:, m],x2[:, m],out[:, m],mask)
@njit
def F5s(x1,x2,out,mask):
      for n in range(x1.shape[0]):
                if mask[n]:
                    out[n] = x1[n]**2+ x2[n]**2
N= 10**6
M= 10
reps =10
dt=np.float32
x=np. random.random((N,M)).astype(dt)
y= np. random.random((N,M)).astype(dt)
out=np.empty_like(x)
t1=[]
t2=[]
t3=[]
t4=[]
t5=[]
frac= np.arange(.1,1,.1)
mask= np.random.choice(a=[False, True], size=(N, ), p=[1-frac[1] , frac[1]])
sel = np.flatnonzero(mask).astype(np.int32)
# complie code

F1(x,y,out)
print('F1',out.sum())
out[:] =0.
F2(x,y,out,mask)
print('F2',out.sum())
F3(x,y,out,sel)
print('F2',out.sum())

xT=np. random.random((M,N)).astype(dt)
yT= np. random.random((M,N)).astype(dt)
outT=np.empty_like(x)
F4(xT,yT,outT,mask)
print('F4',out.sum())

F5(x,y,out,mask)
print('F5',out.sum())

for f in frac:
    mask= np.random.choice(a=[False, True], size=(N, ), p=[1-f , f])
    sel = np.flatnonzero(mask).astype(np.int32)

    t1.append(timeit(lambda : F1(x,y,out),number=reps ))
    t2.append(timeit(lambda : F2(x,y,out,mask),number=reps ))
    t3.append(timeit(lambda : F3(x,y,out,sel),number=reps ))

    t4.append(timeit(lambda : F4(xT,yT,outT,mask),number=reps ))
    t5.append(timeit(lambda : F5(x,y,out,mask),number=reps ))

find_instr(F1)
find_instr(F2)
find_instr(F3)
find_instr(F4)
find_instr(F4s)
find_instr(F5)
find_instr(F5s)

#print('times',t1,t2,t3,t4)


#sqdiff(x, y)
#find_instr(sqdiff,  sig=0)

plt.plot(frac,t1,label='all values')
plt.plot(frac,t2,label='masked all values ')
plt.plot(frac,t3,label='selected values')
plt.plot(frac,t4,label= 'masked sub func  transpose')
plt.plot(frac,t5,label= 'masked  sub func ')
plt.legend()
plt.show()

