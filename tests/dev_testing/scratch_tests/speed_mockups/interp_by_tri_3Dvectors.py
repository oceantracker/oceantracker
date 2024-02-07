from os import  environ
environ['NUMBA_BOUNDSCHECK'] = '1'
from numba import njit, guvectorize, vectorize, prange

import numpy as np

from matplotlib import pyplot as plt

from oceantracker.util.numba_util import count_simd_intructions,compare_simd, time_numba_code
from scipy.spatial import Delaunay

from collections import Counter

def run_code(F,reps=10):
    # run code with different particle sections

    # randomise which cells are used and their bc_cords
    n_cell =np. random.random((N,)).astype(np.int32)
    bc_cords= np. random.random((N,3)).astype(data.dtype)
    nz_cell =np. random.randint(0,data.shape[1]-1,N).astype(np.int32)
    z_frac= np. random.random((N,2)).astype(data.dtype)
    z_frac[:,1] = 1.0- z_frac[:,0]


    mask= np.random.choice(a=[False, True], size=(N, ), p=[1-f , f])
    sel = np.flatnonzero(mask).astype(np.int32)

    if F == DataByTri:
        F(data_tri,bc_cords, n_cell,nz_cell, z_frac,out,sel)
        check_sum=  out[sel,:].sum()
        t= time_numba_code(F,data_tri,bc_cords, n_cell,nz_cell, z_frac,out,sel,number=reps )

    elif F == DataByTriPlus:
        F(data_tri2,bc_cords, n_cell,nz_cell, z_frac,out,sel)
        check_sum=  out[sel,:].sum()
        t= time_numba_code(F,data_tri2,bc_cords, n_cell,nz_cell, z_frac,out,sel,number=reps )
    else:
        F(data,triangles,bc_cords, n_cell,nz_cell, z_frac,out,sel)
        check_sum=  out[sel,:].sum()
        t= time_numba_code(F,data,triangles,bc_cords, n_cell,nz_cell, z_frac,out,sel,number=reps )

    return t,check_sum

def sel_fraction(N,frac=0.5):
    mask= np.random.choice(a=[False, True], size=(N, ), p=[1-frac , frac])
    sel = np.flatnonzero(mask).astype(np.int32)
    return sel,mask

@njit
def CurrentFunc(data, triangles, bc_cords, n_cell,nz_cell, z_fraction, out, sel):
    # 3D vector
     for n in sel:
         nodes = triangles[n_cell[n], :]
         for n_comp in range(3): out[n, n_comp] = 0.

         for m in range(3):
             for n_comp in range(3):
                temp = z_fraction[n,0]* data[nodes[m],nz_cell[n],n_comp]+z_fraction[n, 1]* data[nodes[m],nz_cell[n]+1,n_comp]
                out[n,n_comp] += bc_cords[n,m] *temp
@njit
def CurrentFuncPlus(data, triangles, bc_cords, n_cell,nz_cell, z_fraction, out, sel):

     for n in sel:
         nodes = triangles[n_cell[n], :]
         for n_comp in range(3): out[n, n_comp] = 0.

         for m in range(3):
             d = data[nodes[m],nz_cell[n]:nz_cell[n]+2,:] # 20% faster as alows more optimixation of below by fixing sizes
             for n_comp in range(3):
                temp = z_fraction[n, 0] * d[0,n_comp]
                temp +=z_fraction[n, 1] * d[1,n_comp]
                out[n,n_comp] += bc_cords[n,m] *temp

@njit
def DataByTri(data_tri,bc_cords, n_cell,nz_cell, z_fraction,out,sel):
    for n in sel:
        nc  = n_cell[n]
        for n_comp in range(3): out[n, n_comp] = 0.
        d = data_tri[nc,nz_cell[n]:nz_cell[n]+2,:,:]
        for m in range(3):
            for n_comp in range(3):
                temp = z_fraction[n,0]* d[0,m, n_comp]+z_fraction[n, 1]* d[1,m,n_comp]
                out[n,n_comp] += bc_cords[n, m] * temp


@njit
def DataByTriPlus(data_tri,bc_cords, n_cell,nz_cell, z_fraction,out,sel):
    for n in sel:
        nc  = n_cell[n]
        d = data_tri[nc,nz_cell[n]:nz_cell[n]+2,:,:]
        for n_comp in range(3):
            out[n, n_comp] = 0.
            for m in range(3):
                temp = z_fraction[n,0]* d[0, n_comp,m]+z_fraction[n, 1]* d[1,n_comp,m]
                out[n,n_comp] += bc_cords[n, m] * temp


@njit
def DataByTriPlusV_slow(data_tri,bc_cords, n_cell,nz_cell, z_fraction,out,sel):
    dd =np.reshape(data_tri,(data_tri.shape[0],data_tri.shape[1],9))

    temp = np.full((3,),0.,dtype=data_tri.dtype)
    i_all = np.arange(9).astype(np.int32)
    n_comp_all= i_all // 3
    m_all = i_all-3*n_comp_all

    for n in sel:
        nc  = n_cell[n]
        for n_comp in range(3): out[n, n_comp] = 0.
        d = dd[nc,nz_cell[n]:nz_cell[n]+2,:]
        for i in range(9):
            temp =  z_fraction[n, 0]* d[0,i] + z_fraction[n, 1]* d[1,i]
            out[n,n_comp_all[i]] += bc_cords[n, m_all[i]] * temp

@njit()
def D():
    N=10**6
    a = np.full((N,),0.,dtype=np.float32)
    b = np.full((N,),0.,dtype=np.float32)
    out= np.empty_like(a)
    for n in range(a.shape[0]):
        out[n] = a[n]*b[n]
@njit()
def D2():
    N=10**6
    a = np.full((N,3),0.,dtype=np.float32)
    b = np.full((N,3),0.,dtype=np.float32)
    out= np.empty_like(a)
    for n in range(a.shape[0]):
        for m in range(3):
            out[n,m] = a[n,m]*b[n,m]

if __name__ == "__main__":
    Nodes= 10**5 +1

    N=10**7
    Nz=20
    M=3
    reps = 10
    dt=np.float32
    data=np. random.random((Nodes,Nz,3)).astype(dt) # 3D vector
    x = np. random.random((Nodes,2)).astype(dt)
    DT= Delaunay(x)
    triangles=DT.simplices
    data_tri = np.asarray(np.transpose(data[triangles,:,:],(0,2,1,3)),order='c')
    data_tri2 = np.asarray(np.transpose(data[triangles,:,:],(0,2,3,1)),order='c')
    out=np.zeros((N,data.shape[1]))

    frac= np.arange(.05,1,.025)
    mask= np.random.choice(a=[False, True], size=(N, ), p=[1-frac[1] , frac[1]])
    sel = np.flatnonzero(mask).astype(np.int32)




    t= np.full((4,frac.size),0.)
    check_sum= np.full((4,),0.)

    for n, f in enumerate(frac):
        mask= np.random.choice(a=[False, True], size=(N, ), p=[1-f , f])
        sel = np.flatnonzero(mask).astype(np.int32)

        t[0,n],check_sum[0] =run_code(CurrentFunc,  reps=reps)
        t[1,n],check_sum[1]= run_code(CurrentFuncPlus,reps=reps)
        t[2,n],check_sum[2] =run_code(DataByTri,reps=reps )
        t[3,n],check_sum[3] =run_code(DataByTriPlus,reps=reps )

    # lok at smid code
    D() # 1D function
    D2()
    comp = compare_simd((CurrentFunc, CurrentFuncPlus,DataByTri,DataByTriPlus,  D,D2))

    print('times', t[:,-1])
    print('relative times', t[1:,-1]/t[0,-1])
    print('check sums', check_sum)

    plt.plot(frac,t[0,:],label=CurrentFunc.__name__)
    plt.plot(frac,t[1,:],label=CurrentFuncPlus.__name__)
    plt.plot(frac,t[2,:],label=DataByTri.__name__)
    plt.plot(frac,t[3,:],label=DataByTriPlus.__name__)


    plt.ylabel('Time per call')
    plt.legend()
    plt.show(block=True)

    plt.plot(frac,t[1,:]/t[0,:],label=CurrentFuncPlus.__name__)
    plt.plot(frac,t[2,:]/t[0,:],label=DataByTri.__name__)
    plt.plot(frac,t[3,:]/t[0,:],label=DataByTriPlus.__name__)

    plt.plot([0,1],[1,1],'k--')
    plt.ylabel('Time relative to nodal vals')
    plt.legend()
    plt.ylim([0, 2])
    plt.show()

