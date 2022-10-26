import numpy as np
from  numba import njit
from time import perf_counter

nops=5

@njit
def Fserial(x,s, sel):
    for n in sel:
        for m in range(x.shape[1]):
            s[m] += float(x[n, m]) * np.pi
            s[m] += float(x[n, m]) * np.pi
            s[m] += float(x[n, m]) * np.pi


@njit
def F3(x, y, z, sel):
    s=np.full((x.shape[1],),0,dtype=np.float64)
    for n in sel:
        for o in range(nops):
            for m in range(x.shape[1]):
                s[m]  += float(x[n, m])*np.pi
                s[m]  += float(y[n, m])*np.pi
                s[m]  += float(z[n, m])*np.pi
    return s


@njit
def FX3(x3, sel):
    s=np.full((x3['x'].shape[1],),0,dtype=np.float64)
    for n in sel:
        for o in range(nops):
            for m in range(3):
                s[m]  += float(x3['x'][n][m])*np.pi
                s[m]  += float(x3['y'][n][m])*np.pi
                s[m]  += float(x3['z'][n][m])*np.pi
    return s


if __name__ == '__main__':

    N= 10**6
    M=3
    frac= .9#0.5
    sel1= np.random.choice(N,size=int(N*frac), replace=False)
    sel2 = np.sort(sel1)
    nreps=10

    for dt in [np.int8,np.int16,np.int32,np.float32, np.int64, np.float64]:

        X = (np.random.rand(N, M) * 128).astype(dt)
        s0=np.sum(3*X,axis=0)
        s0=F3(X.copy(), X.copy(), X.copy(), sel1)

        t0 = perf_counter()
        for n in range(nreps):
            srandom=F3(X.copy(), X.copy(), X.copy(), sel1)
        trandom=perf_counter() - t0

        t0 = perf_counter()
        for n in range(nreps):
            ssorted= F3(X.copy(), X.copy(), X.copy(), sel2)
        tsorted=perf_counter() - t0


        X3 = np.dtype([('x', dt,(M,)), ('y', dt, (M,)), ('z', dt, (M,))])
        C = np.full((N,), 0, dtype=X3)
        C['x'][:] = X.copy()
        C['y'][:] = X.copy()
        C['z'][:] = X.copy()
        FX3(C, sel2)
        t0 = perf_counter()
        for n in range(nreps):
            sdtype= FX3(C,  sel2)
        tdtype = perf_counter() - t0

        # serial operations, like current OT
        sserial = np.full((X.shape[1],), 0, dtype=np.float64 )
        Fserial(X.copy(), sserial, sel2)
        t0 = perf_counter()
        for n in range(nreps):
            sserial = np.full((X.shape[1],), 0, dtype=np.float64)
            for o in range(nops):
                Fserial(X.copy(),sserial,  sel2)

        tserial = perf_counter() - t0

        print(str(dt), 'random', trandom, 'sorted', tsorted,  'serial', tserial, 'dtype', tdtype)

        T0 = tsorted
        print('\t','random/sorted',trandom/T0,'serial/sorted',tserial/T0,
              'dtype/sorted',tdtype/T0 )

        print('\t\t ', 'random', np.max(np.abs(srandom-s0))/np.max(X),
              'sorted', np.max(np.abs(ssorted-s0))/np.max(X),
              'tserial', np.max(np.abs(sserial - s0)) / np.max(X),
              'dtype', np.max(np.abs(sdtype-s0))/np.max(X))