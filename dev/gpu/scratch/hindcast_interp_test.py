# compare array copy on cpu and gpu
from numba import njit, prange
import numpy as np
from timeit import  timeit
from time import perf_counter
import os
from oceantracker.util import ncdf_util
os.environ['CUDA_HOME'] = r"C:\ProgramData\miniconda3\envs\oceantracker-dev\Library\bin"
# For Windows (adjust to your actual CUDA toolkit version folder)
os.environ["CUDA_PATH"] = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2"
os.environ["PATH"] += os.pathsep + r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2\bin"

from numba import cuda
cuda.detect()
#os.environ['CUDA_HOME'] = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"

para=True

@njit(parallel=para)
def Finterp_numba_0(v1,v2, dt_frac,nz_frac,n_cell, nz_cell, tri,vout, index):
    for nn in prange(index.size):
        n = index[nn]
        for nc in range(3): vout[n, nc] = 0.
        nz = nz_cell[n]
        for m in range(3): # loop over nodes
            node = tri[n_cell[n], m]
            for nc in range(3):
                vout[n,nc] += v1[node, nz,nc]*(1-dt_frac) +  v2[node, nz+1,nc]*dt_frac

@cuda.jit
def F2D_cuda_0(v1,v2, dt_frac,nz_frac,n_cell,nz_cell, tri,vout, mask):
    idx = cuda.grid(1)
    if idx < mask.size and mask[idx]:
        #for nc in range(3): vout[idx, nc] = 0.
        h_cell= n_cell[idx]
        nz = nz_cell[idx]

        for nc in range(3):
            tmp = 0.
            for m in range(3):  # loop over nodes
                node = tri[h_cell, m]
                tmp += v1[node, nz, nc] * (1 - dt_frac) + v2[node, nz + 1, nc] * dt_frac
        vout[idx, nc] = tmp

nc= ncdf_util.NetCDFhandler(r'Z:\Hindcasts\NZ_region\2024_OceanNumNZ-2022-06-20\2010\01\NZfinite20100101_01z.nc')
v = nc.read_variable('hvel').data
w = nc.read_variable('vertical_velocity').data
v = np.concatenate((v,w[...,np.newaxis]), axis=3)
nz_bot= nc.read_variable('node_bottom_index').data
tri = nc.read_variable('SCHISM_hgrid_face_nodes').data[:,:3].astype(np.int32)-1

n_steps = 2
N= 10**6
mask =np.random.rand(N) > .1
index = np.flatnonzero(mask).astype(np.int32)
n_cell = np.int32(np.random.randint(0, nz_bot.size, size= N))
nz_cell =np.int32(np.random.randint(nz_bot.min(), nz_bot.size-1, size= N))
nz_frac =np.random.rand(N)

Fs=[F2D_cuda_0, Finterp_numba_0 ]
nt=0

for f in Fs:
    tcopy1 = 0.
    tcopy2 =0.
    v1,v2 = v[nt,...],v[nt+1,...]
    vout1 = np.full((N,3),0., dtype=np.float64)
    vout2 =  vout1.copy()
    dt_frac = 0.

    if 'cuda' in f.__name__:
        t0=perf_counter()
        maskc = cuda.to_device(mask)
        v1c = cuda.to_device(v1)
        v2c = cuda.to_device(v2)
        nz_botc = cuda.to_device(nz_bot)
        tric = cuda.to_device(tri)
        vout1c = cuda.to_device(vout1)
        n_cellc = cuda.to_device(n_cell)
        nz_cellc = cuda.to_device(nz_cell)

        tcopy1 =  perf_counter()-t0

        threads_per_block = 256
        blocks_per_grid = (mask.shape[0] + (threads_per_block - 1)) // threads_per_block

        f[blocks_per_grid, threads_per_block](v1c,v2c, dt_frac,nz_frac,n_cellc,nz_cellc, tric,vout1c, maskc)

        t0 = perf_counter()
        for ns in range(n_steps+1):
            dt_frac = ns / n_steps
            f[blocks_per_grid, threads_per_block](v1c,v2c, dt_frac,nz_frac,n_cellc,nz_cellc,tric,vout1c, maskc)
        t =  perf_counter()-t0

        t0=perf_counter()
        vout1 = vout1c.copy_to_host()
        tcopy2 =  perf_counter()-t0

    else:
        Finterp_numba_0(v1, v2, dt_frac, nz_frac, n_cell,nz_cell, tri, vout2, index)
        t0 = perf_counter()
        for ns in range(n_steps+1):
            dt_frac=ns/n_steps
            Finterp_numba_0(v1, v2, dt_frac, nz_frac, n_cell,nz_cell, tri, vout2, index)
        t =  perf_counter()-t0

    print(f'N={N:,},  {t:6.3f} sec  {(t/n_steps)*1000:7.3f} ms/rep  \t {f.__name__}, gpu copy {tcopy1*1000:5.2f} ms, read {tcopy2*1000:5.2f}')

print( 'compare answers, max diff:', np.abs((vout1-vout2).max()))