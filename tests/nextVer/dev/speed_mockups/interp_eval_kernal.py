from numba import njit, prange,float64,int32, gdb
from time import perf_counter
import numpy as np


@njit()
def F1(nt,tri, BCcord,n_cell, F, F_out,  sel,tfrac):
    n_comp = F_out.shape[1]
    F1= F[nt,:,:]
    F2 = F[nt+1, :, :]
    for n in sel:

        for i in range(n_comp): F_out[n, i] = 0.  # zero out for summing
        for n_bc in range(3):
            n_node = tri[n_cell[n], n_bc]
            bc = BCcord[n, n_bc]
            for c in range(n_comp):
                F_out[n, c] += bc * ((1.0-tfrac)*F1[n_node, c] +tfrac*F2[n_node, c])


@njit()
def F2(nt, tri, BCcord,n_cell, F, F_out,  sel,tfrac):
    n_comp =F_out.shape[1]
    F1= F[nt,:,:]
    F2 = F[nt+1, :, :]

    for n in sel:
        out = F_out[n, :]
        t = tri[n_cell[n], :]
        for i in range(n_comp): F_out[n, i] = 0.  # zero out for summing
        for n_bc in range(3):
            n_node = t[n_bc]
            bc = BCcord[n, n_bc]
            for c in range(n_comp):
                out[c] += bc * ((1.0-tfrac)*F1[n_node, c] +tfrac*F2[n_node, c])

@njit()
def F3(nt,tri, BCcord,n_cell, F, F_out,  sel,tfrac):
    F1= F[nt,:,:]
    F2 = F[nt+1, :, :]
    for n in sel:
        K(tri[n_cell[n], :], BCcord[n, :],  F1, F2, F_out[n,:],tfrac)

@njit(inline='always')
def K(tri, bcc, f1,f2, f_out,tfrac):
    for c in range(f_out.shape[0]): f_out[c] = 0.  # zero out for summing
    for n_bc in range(3):
        n_node = tri[n_bc]
        for c in range(f_out.shape[0]):
            f_out[c] += bcc[n_bc] *  ((1.0-tfrac)*f1[n_node, c] +tfrac*f2[n_node, c])


@njit(inline='always')
def NodeVals1(tri, f1,f2,tfrac, f_nodes):
    if f_nodes.shape[0] == 0:
        NodeValsScaler(tri, f1,f2,tfrac, f_nodes)
    else:
        NodeValsVector(tri, f1,f2,tfrac, f_nodes)

@njit(inline='always')
def NodeValsVector(tri, f1,f2,tfrac, f_nodes):
    for n_bc in range(3):
        n_node = tri[n_bc]
        for c in range(f_nodes.shape[0]):
            f_nodes[n_bc, c] = (1.0-tfrac)*f1[n_node, c] + tfrac*f2[n_node, c]

@njit(inline='always')
def NodeValsScaler(tri, f1,f2,tfrac, f_nodes):
    for n_bc in range(3):
        n_node = tri[n_bc]
        f_nodes[n_bc, 0] = (1.0-tfrac)*f1[n_node, 0] + tfrac*f2[n_node, 0]


@njit(inline='always')
def BCinterp1(bc, f_nodes, fout):
    if fout.shape[0] == 0:
        BCinterpScaler(bc, f_nodes, fout)
    else:
        BCinterpVector(bc, f_nodes, fout)

@njit(inline='always')
def BCinterp(bc, f_nodes, fout):
    if fout.shape[0]==0:
        fout[0] = 0.
        for m in range(3):
            fout[0] += bc[m] * f_nodes[m, 0]
    else:
        for c in range(fout.shape[0]):
            fout[c] = 0.
            for m in range(3):
                fout[c] += bc[m] * f_nodes[m, c]

@njit(inline='always')
def BCinterpVector(bc, f_nodes, fout):
    for c in range(fout.shape[0]):
        fout[c] = 0.
        for m in range(3):
            fout[c] += bc[m]*f_nodes[m,c]

@njit(inline='always')
def BCinterpScaler(bc, f_nodes, fout):
    fout[0] = 0.
    for m in range(3):
        fout[0] += bc[m]*f_nodes[m,0]

#@njit((int32[:,:], float64[:,:], int32[:], float64[:,:], float64[:,:], int32[:]))
@njit()
def F4(nt, tri, BCcord,n_cell, F, F_out,  sel,tfrac):
    F1= F[nt,:,:]
    F2 = F[nt+1, :, :]
    f_nodes = np.full((3,F.shape[2]),0.)


    for n in sel:
        #NodeValsScaler(tri[n_cell[n], :], F1, F2, tfrac, f_nodes)
        #NodeVals1(tri[n_cell[n], :],   F1, F2 , tfrac, f_nodes)
        NodeValsVector(tri[n_cell[n], :], F1, F2, tfrac, f_nodes)
        BCinterpVector(BCcord[n, :], f_nodes, F_out[n, :])
        #BCinterp1(BCcord[n, :], f_nodes, F_out[n, :])
        #BCinterpScaler(BCcord[n, :], f_nodes, F_out[n, :])
@njit()
def F4s(nt, tri, BCcord,n_cell, F, F_out,  sel,tfrac):
    F1= F[nt,:,:]
    F2 = F[nt+1, :, :]
    f_nodes = np.full((3,F.shape[2]),0.)


    for n in sel:
        NodeValsScaler(tri[n_cell[n], :], F1, F2, tfrac, f_nodes)
        BCinterpScaler(BCcord[n, :], f_nodes, F_out[n, :])


if __name__ == '__main__':
    dt=np.float64
    Nodes = 10**5

    M = 3
    NT = 20  # time steps
    F= np.random.rand(NT + 1, Nodes, M)

    Npart = 10**6
    v =  np.random.rand(Npart,M).astype(dt)
    tri=np.random.randint(0,high=Nodes,size=(2*Nodes,3))

    n_cell = np.random.randint(0, high=Nodes, size=(Npart, ))
    #n_cell.sort()
    BCcord = np.random.rand(Npart, 3).astype(dt)
    F_out = np.random.rand(Npart,M).astype(dt)


    tfrac=0.4
    sel= np.random.choice(Npart,size=int(Npart*.7), replace=False)
    sel = np.sort(sel)

    #print('start Basic')
    F1(0,tri, BCcord,n_cell, F, F_out,  sel,tfrac)
    t0 = perf_counter()
    for n in range(NT):
        F1(n,tri, BCcord, n_cell, F, F_out, sel,tfrac)
    print('Basic',perf_counter() - t0)
    F_out_check = F_out.copy()

    #print('start Views')
    F2(0,tri, BCcord,n_cell, F, F_out,  sel,tfrac)
    t0 = perf_counter()
    for n in range(NT):
        F2(n,tri, BCcord, n_cell, F, F_out, sel,tfrac)
    print('Views', perf_counter() - t0, np.max(np.abs(F_out - F_out_check)))

    F3(0, tri, BCcord,n_cell, F, F_out,  sel,tfrac)
    t0 = perf_counter()
    for n in range(NT):
        F3(n,tri, BCcord, n_cell, F, F_out, sel,tfrac)
    print('Kernal', perf_counter() - t0, np.max(np.abs(F_out - F_out_check)))



    F4(0,tri, BCcord,n_cell, F, F_out,  sel,tfrac)
    F4s(0, tri, BCcord, n_cell, F, F_out, sel, tfrac)
    t0 = perf_counter()
    if M > 1:
        for n in range(NT):
            F4(n,tri, BCcord, n_cell, F, F_out, sel,tfrac)
    else:
        for n in range(NT):
            F4s(n, tri, BCcord, n_cell, F, F_out, sel, tfrac)
    print('Two kernals', perf_counter() - t0, np.max(np.abs(F_out - F_out_check)))


