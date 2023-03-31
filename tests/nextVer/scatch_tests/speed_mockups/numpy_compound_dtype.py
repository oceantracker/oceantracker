import numpy as np
from time import perf_counter
from numba import njit

@njit()
def M1a(A,sel):
    s=0.
    for n in sel:
        for m in range(A['x'].shape[1]):
            for l in range(A['x'].shape[2]):
                s += A['x'][n, m ,l] + A['y'][n, m ,l]+ A['z'][n, m ,l]
    return  s/A['x'].size

@njit()
def M1b(A,sel):
    s=0.
    for n in sel:
        for m in range(A['x'].shape[1]):
            for l in range(A['x'].shape[2]):
                s += A['x'][n,  m ,l] + A['y'][n, m ,l]+ A['z'][n, m ,l]
    return  s/A['x'].size

@njit()
def M2(x,y, z, sel):
    s=0.
    for n in sel:
        for m in range(x.shape[1]):
            for l in range(x.shape[2]):
                s += x[n,m,l] + y[n,m,l] + z[n,m,l]
    return  s/x.size/3.

@njit()
def M3(x, sel):
    s=0.
    for n in sel:
        for m in range(x.shape[1]):
            for l in range(x.shape[2]):
                s += x[n,m,l]
    return  s/x.size

N = 10 ** 5
frac = .7 # 0.5
sel1 = np.random.choice(N, size=int(N * frac), replace=False)
sel2 = np.sort(sel1)

M=3
nspep=50
t1= np.dtype([('x',np.float64,(M,3)),('y',np.float64,(nspep*M, 3)),('z',np.float64,(M,3))])
A= np.full((N,),0,dtype=t1)
A['x']= np.random.random(A['x'].shape)
A['y']= np.random.random(A['y'].shape)
A['z']= np.random.random(A['z'].shape)

t2= np.dtype([('x',np.float64,(N,M,3)),('y',np.float64,(N,nspep*M,3)),('z',np.float64,(N,M,3))])
B= np.full((1,),0,dtype=t2)
B['x']= A['x'].copy()
B['y']= A['y'].copy()
B['z']= A['z'].copy()

m= M1a(A,sel2)
nreps=100

t0=perf_counter()
#m= np.mean(A['x'])
for n in range(nreps):
    m= M1a(A,sel2)

tc =perf_counter()-t0
print('compound array', m,tc )


t0=perf_counter()
#m= np.mean(A['x'])
for n in range(nreps):
    m= M1a(B[0],sel2)
tcn= perf_counter() - t0
print('compound N array', m, tcn)


x=A['x'].copy()*1.0
y=A['y'].copy()*1.0
z=A['z'].copy()*1.0

m= M2(x,y,z, sel2)
t0=perf_counter()

for n in range(nreps):
    m= M2(x,y, z,sel2)
tn= perf_counter() - t0
print('numpy array', m, tn)

M3(x,sel2)
t0=perf_counter()
for n in range(nreps):
    m  = M3(x,sel2)
    m += M3(y, sel2)
    m += M3(z, sel2)
tserial= perf_counter() - t0
print('serial numpy array', m/3, tserial)


t0=perf_counter()
#m= np.mean(A['x'])
for n in range(nreps):
    m= np.mean(np.take(x+y[:,:M,:]+z, sel2))
tnumpy= perf_counter() - t0
print('pure numpy', m/3, tc)

print('Compound n=',tcn/tc,', Separate np arrays=',tn/tc, ', Serial np arrays=', tserial/tc, ', Pure numpy=',tnumpy/tc)
print(A.nbytes,B.nbytes)