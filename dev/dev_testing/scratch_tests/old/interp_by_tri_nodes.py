from os import  environ

environ['NUMBA_ENABLE_AVX']='0'
import numba
#numba.core.config.ENABLE_AVX=False
#numba.core.config.BOUNDSCHECK=True
#numba.core.config
from numba import njit, guvectorize, vectorize, prange

import numpy as np

from matplotlib import pyplot as plt

from oceantracker.util.numba_util import count_simd_intructions,compare_simd, time_numba_code
from scipy.spatial import Delaunay

from collections import Counter

def run_code(F,data,data_tri,triangles,out,reps=10,masked=False,data_nodes=False):
    # run code with different particle sections

    # randomise which cells are used and their bc_cords
    n_cell =np. random.random((N,)).astype(np.int32)
    bc_cords= np. random.random((N,3)).astype(data.dtype)

    mask= np.random.choice(a=[False, True], size=(N, ), p=[1-f , f])
    sel = np.flatnonzero(mask).astype(np.int32)
    s= mask if masked else sel
    if data_nodes:
        t= time_numba_code(F,data_tri,bc_cords, n_cell,out,s,number=reps )
    else:
        t= time_numba_code(F,data,triangles,bc_cords, n_cell,out,s,number=reps )
    return t

def sel_fraction(N,frac=0.5):
    mask= np.random.choice(a=[False, True], size=(N, ), p=[1-frac , frac])
    sel = np.flatnonzero(mask).astype(np.int32)
    return sel,mask

@njit
def CurrentFunc(data, triangles, bc_cords, n_cell, out, sel):

 for n in sel:
     nodes = triangles[n_cell[n], :]
     out[n] = 0.
     for m in range(3):
        out[n] += bc_cords[n,m] * data[nodes[m]]

@njit
def CurrentFuncSubFunc(data, triangles, bc_cords, n_cell, out, sel):

    for n in sel:
        nodes = triangles[n_cell[n], :]
        out[n] =  CFS(data,bc_cords[n,:],nodes)
@njit(inline='always')
def CFS(data,bc_cords,nodes):
    out = 0.
    for m in range(3):
        out += bc_cords[m] * data[nodes[m]]
    return out

@njit
def DataByTri(data_tri,bc_cords, n_cell,out,sel):
    for n in sel:
        nc  = n_cell[n]
        out[n] = 0.0
        for m in range(3):
            out[n] += bc_cords[n, m] * data_tri[nc, m]

@njit
def DataByTriTemp(data_tri,bc_cords, n_cell,out,sel):

    temp = np.empty((3,),dtype=data_tri.dtype)
    for n in sel:
        nc = n_cell[n]
        for m in range(3):
            temp[m] = bc_cords[n, m] * data_tri[nc,m]

        #out[n] = temp.sum() # has fewer mem requests, but no faster
        out[n] = 0
        for m in range(3):  out[n] +=  temp[m]

@njit
def DataByTriTempMasked(data_tri, bc_cords, n_cell, out, mask):
    temp = np.empty((3,),dtype=data_tri.dtype)
    for n in range(out.size):
        if mask[n]:
            nc = n_cell[n]
            for m in range(3):
                temp[m] = bc_cords[n, m] * data_tri[nc,m]
            out[n] = 0
            for m in range(3):  out[n] +=  temp[m]
@njit()
def DataByTriTempSubFunc(data_tri,bc_cords, n_cell,out,sel):

    temp = np.empty((3,),dtype=data_tri.dtype)
    for n in sel:
        nc = n_cell[n]
        DataByTriTempSubFuncCode(data_tri[nc,:],bc_cords[n,:],temp)
        for m in range(3):  out[n] += temp[m]

@njit()
def DataByTriTempSubFuncCode(data_tri,bc_cords,temp):
    #temp[:] = bc_cords[:] * data_tri[:]
   for m in range(3):
            temp[m] = bc_cords[m] * data_tri[m]
@njit()
def D():
    N=10**6
    a = np.full((N,),0.)
    b = np.full((N,),0.)
    out= np.empty_like(a)
    for n in range(a.shape[0]):
        out[n] = a[n]*b[n]
@njit()
def D2():
    N=10**6
    a = np.full((N,3),0.)
    b = np.full((N,3),0.)
    out= np.empty_like(a)
    for n in range(a.shape[0]):
        for m in range(a.shape[1]):
            out[n,m] = a[n,m]*b[n,m]


if __name__ == "__main__":
    Nodes= 10**5

    N=10**6
    M=3
    reps = 10
    dt=np.float32
    data=np. random.random((Nodes,)).astype(dt)
    x = np. random.random((Nodes,2))
    DT= Delaunay(x)
    triangles=DT.simplices
    data_tri= data[triangles]

    bc_cords= np. random.random((N,3)).astype(dt)
    out=np.zeros((N,))
    n_cell =np. random.random((N,)).astype(np.int32)

    frac= np.arange(.001,1,.1)
    mask= np.random.choice(a=[False, True], size=(N, ), p=[1-frac[1] , frac[1]])
    sel = np.flatnonzero(mask).astype(np.int32)
    # check code
    CurrentFunc(data, triangles, bc_cords, n_cell, out, sel)
    print(CurrentFunc.__name__,out.sum())

    CurrentFuncSubFunc(data, triangles, bc_cords, n_cell, out, sel)
    print(CurrentFuncSubFunc.__name__,out.sum())

    DataByTri(data_tri, bc_cords, n_cell,out,sel)
    print(DataByTri.__name__,out.sum())

    DataByTriTemp(data_tri, bc_cords, n_cell,out,sel)
    print(DataByTriTemp.__name__,out.sum())

    DataByTriTempMasked(data_tri, bc_cords, n_cell, out, mask)
    print(DataByTriTempMasked.__name__,out.sum())

    DataByTriTempSubFunc(data_tri, bc_cords, n_cell,out,sel)
    print(DataByTriTempSubFunc.__name__,out.sum())

    D() # 1D function
    D2()
    comp = compare_simd((CurrentFunc,CurrentFuncSubFunc, DataByTri, DataByTriTemp, DataByTriTempMasked, DataByTriTempSubFunc,D,D2))


    t1=[]
    t2=[]
    t3=[]
    t4=[]
    t5=[]
    t6=[]


    for f in frac:
        mask= np.random.choice(a=[False, True], size=(N, ), p=[1-f , f])
        sel = np.flatnonzero(mask).astype(np.int32)
        bc_cords= np. random.random((N,3)).astype(dt)

        t1.append(run_code(CurrentFunc, data, data_tri, triangles, out, reps=reps))
        t2.append(run_code(DataByTri,data,data_tri,triangles,out,reps=reps,data_nodes=True ))
        t3.append(run_code(DataByTriTemp,data,data_tri,triangles,out,reps=reps,data_nodes=True ))
        t4.append(run_code(DataByTriTempMasked, data, data_tri, triangles, out, reps=reps, data_nodes=True, masked=True))
        t5.append(run_code(DataByTriTempSubFunc,data,data_tri,triangles,out,reps=reps,data_nodes=True ))
        t6.append(run_code(CurrentFuncSubFunc, data, data_tri, triangles, out, reps=reps))
    t1 = np.asarray(t1)
    t2 = np.asarray(t2)
    t3 = np.asarray(t3)
    t4 = np.asarray(t4)
    t5 = np.asarray(t5)
    t6 = np.asarray(t6)


    print('times', t2[-1], t6[-1],t2[-1], t3[-1],t4[-1],t5[-1])


    plt.plot(frac,t1,label=CurrentFunc.__name__)
    plt.plot(frac, t6, label=CurrentFuncSubFunc.__name__)
    plt.plot(frac,t2,label=DataByTri.__name__)
    plt.plot(frac,t3,label=DataByTriTemp.__name__)
    plt.plot(frac,t4,label=DataByTriTempMasked.__name__)
    plt.plot(frac,t5,label=DataByTriTempSubFunc.__name__)

    plt.ylabel('Time per call')
    plt.legend()
    plt.show(block=True)

    plt.plot(frac, t6 / t1, label=CurrentFuncSubFunc.__name__)
    plt.plot(frac,t2/t1,label=DataByTri.__name__)
    plt.plot(frac,t3/t1,label=DataByTriTemp.__name__)
    plt.plot(frac,t4/t1,label=DataByTriTempMasked.__name__)
    plt.plot(frac,t5/t1,label=DataByTriTempSubFunc.__name__)
    plt.plot([0,1],[1,1],'k--')
    plt.ylabel('Time relative to nodal vals')
    plt.legend()
    plt.ylim([0, 2])
    plt.show()

