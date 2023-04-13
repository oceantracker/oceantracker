import numpy as np
from time import perf_counter

import numba as nb
from numba import njit,float64, void, float32, int32, from_dtype,types

N=2000000
M= 3
MM=100
print(8*N*MM/1e6,N*MM*8)
struct_dtype = np.dtype([  ('id', np.float64,(N,MM))])
struct_dtype = np.dtype([('row', np.float64,(N,M)),  ('id', np.float64,(100,MM)), ('col', np.float32,(N,))])
record_dtype = np.dtype([('row', np.float64,(M,)),  ('id', np.float64,(MM,)), ('col', np.float32)])
@njit(float64(float64[:,:],float32[:],int32[:]))
def s1(r , c, sel):
    s = 0.
    for n in sel:
        for m in range(r.shape[1]):
            s += r[n,m] + np.sin(c[n])
    return s
@njit(float64( from_dtype(struct_dtype),int32[:]))
def s2(S,sel):

    s = 0.
    for n in sel:
        for m in range(S['row'].shape[1]):
            s += S['row'][n,m] + np.sin(S['col'][n])
    return s

@njit(float64( from_dtype(record_dtype)[:],int32[:]))
def s3(R, sel):

    s = 0.
    M= R[0]['row'].shape[0]
    for n in sel:
        for m in range(M):
            s += R[n]['row'][m] + np.sin(R[n]['col'])
    return s

A = np.random.random((N,3))
B = A[:,0].copy().astype(np.float32)
sel = np.sort(np.flatnonzero(A[:,0]>.5)).astype(np.int32)
S= np.zeros((1,),dtype=struct_dtype)
S['row'] = A
S['col'] = B
S=S[0]

R=  np.zeros((N,),dtype=record_dtype)
for n in range(N):
    R[n]['row'][:] = S['row'][n,:].copy()
    R[n]['col']= S['col'][n].copy()

print('record',R[0]['row'])
nreps=500

print('Bytes',S.nbytes/10**6,R.nbytes/10**6)
s1(A, B,sel)
t0= perf_counter()
for n in range(nreps):
    out = s1(A, B,sel)
print('args',perf_counter()-t0,out)

s2(S,sel)
t0= perf_counter()
for n in range(nreps):
    out = s2(S,sel)
print('stucture',perf_counter()-t0,out)

s3(R,sel)
t0= perf_counter()
for n in range(nreps):
    out = s3(R,sel)
print('record',perf_counter()-t0,out)
