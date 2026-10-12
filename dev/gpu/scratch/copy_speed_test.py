# compare array copy on cpu and gpu
from numba import njit, prange
import numpy as np
from timeit import  timeit
from time import perf_counter
import os

os.environ['CUDA_HOME'] = r"C:\ProgramData\miniconda3\envs\oceantracker-dev\Library\bin"
# For Windows (adjust to your actual CUDA toolkit version folder)
os.environ["CUDA_PATH"] = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2"
os.environ["PATH"] += os.pathsep + r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2\bin"

from numba import cuda
cuda.detect()
#os.environ['CUDA_HOME'] = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"

para=True

@njit(parallel=para)
def F2D_numba_0(x, y, index):
    for nn in prange(index.size):
        n = index[nn]
        for m in range(2):
            y[n,m] = x[n,m]

@cuda.jit
def F2D_cuda_0(x, y, mask):
    idx = cuda.grid(1)
    if idx < mask.size and mask[idx]:
        for m in range(2):
            y[idx, m] = x[idx, m]

reps=1
N= 10**7
mask =np.random.rand(N) > .1
index = np.flatnonzero(mask).astype(np.int32)

dt =np.float64
x = np.random.rand(N, 2).astype(dt)
y = np.random.rand(N, 2).astype(dt)
Fs=[F2D_cuda_0,F2D_numba_0 ]

for f in Fs:
    tcopy1 = 0.
    tcopy2 =0.
    xx,yy = x.copy(),y.copy()

    if 'cuda' in f.__name__:
        t0=perf_counter()
        xc = cuda.to_device(xx)
        yc = cuda.to_device(yy)
        maskc = cuda.to_device(mask)
        tcopy1 =  perf_counter()-t0

        threads_per_block = 256
        blocks_per_grid = (x.shape[0] + (threads_per_block - 1)) // threads_per_block

        f[blocks_per_grid, threads_per_block](xc,yc, maskc)
        t0 = perf_counter()
        for m in range(reps):
            f[blocks_per_grid, threads_per_block](xc,yc, maskc)
        t =  perf_counter()-t0

        t0=perf_counter()
        ygpu =yc.copy_to_host()
        tcopy2 =  perf_counter()-t0

    else:

        t = timeit(lambda: f(xx, yy, index), setup=lambda: f(xx, yy, index), number=reps)

    print(f'N={N:,},  {t:6.3f} sec  {(t/reps)*1000:7.3f} ms/rep  \t {f.__name__}, gpu copy {tcopy1*1000:5.2f} ms, read {tcopy2*1000:5.2f}')

print( 'compare answers, max diff:', np.abs((yy-ygpu).max()))