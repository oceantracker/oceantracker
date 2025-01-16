from numba import njit
import numpy as np
from timeit import timeit
from time import perf_counter
from copy import  copy
@njit()
def arg_max(zq,z,nz):
    for n in range(zq.size):
        for m in range(z.size-1):
            if zq[n] < z[m+1]:
                break
        nz[n] = m

@njit()
def walk1(zq,z,nz):
    for n in range(zq.size):
        n0 = nz[n]
        m = n0 # backup if loops are not run
        if zq[n] >= z[n0]: # dz >=0, search above current
            for m in range(n0,z.size-1):
                if zq[n] < z[m+1]:
                    break
        else:
            for m in range(n0-1, -1, -1): # search down to zero, if n0==0 then nz unchanged
                if zq[n] >= z[m]:
                    break
        nz[n] = m

@njit()
def map1(zq,z,nz,nz_map,dz_map):
    for n in range(zq.size):
        n0 = int((zq[n]-z[0])/dz_map)
        nz[n] = nz_map[n0]
        # correction step
        nz[n] -= zq[n] < z[nz[n]]
        pass


nz = 30
z= np.random.random(nz).cumsum()
z= (z -z[0])/(z[-1]-z[0])
delta_z= np.diff(z)
N= 10**6
M=5

zq0= np.random.random(N,)
nz = np.zeros((N,),dtype=np.int32)



# build map,
z_range=z[-1]-z[0]
n= int(np.ceil(z_range/(0.6*np.min(delta_z))))
nz_map= np.zeros((n+1,),dtype=np.int32)
dz_map=z_range/n
sel = (z/dz_map).astype(np.int32)
nz_map[sel[1:-1]] = 1
nz_map = nz_map.cumsum()

print('z diffs', np.min(np.diff(z)), np.max(np.diff(z)),'zq', np.min(zq0), np.max(zq0))
dz_max= np.max(np.diff(z))

for F, args in zip([arg_max,walk1, map1],[(zq0,z,nz), (zq0,z,nz), (zq0,z,nz, nz_map, dz_map)]):
    F(*args)
    t = 0.
    for reps in range(M):
        zq = zq0 + .2 * (np.random.rand(N, ) - .5) * (reps != M-1) # no random on last
        zq = np.minimum(np.maximum(zq, 0.), 1.)
        # swap in zq column into args
        a= list(copy(args))
        a[0] = zq

        t0 = perf_counter()
        F(*tuple(a))
        t += perf_counter() - t0

        if reps == M-1:
            # copy last with no random ness
            nz_M=a[2].copy()

    dz = (zq - z[nz])/delta_z[nz]
    sel = np.logical_or(dz > 1., dz < 0)
    print(F.__dict__['__name__'],t,'sec, z fraction out of interval', nz[sel],z[nz[sel]],dz[sel])
    if F.__dict__['__name__']=='arg_max':
        nz_ref= nz_M.copy()
    print('check- compare nz with arg max', np.max(nz_M-nz_ref))
