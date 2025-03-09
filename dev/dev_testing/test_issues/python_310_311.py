from numba import  njit
import  numba
import numpy as np
from time import perf_counter
import sys
from glob import glob
import llvmlite
from matplotlib import pyplot as plt
import pickle

def add(x,out):
    # do minimal work on array to emphasize dispatch time
    # do same opertion on  all dim sizes

    x2= x.reshape(-1,1)
    out2=out.reshape(-1,1)
    for n in range(x2.shape[0]):
       out2[n] = x2[n] # only copy first column


ndims = np.arange(7)
Ns= [10**4, 10**5]

compile_times=np.full((ndims.size,),0.)

n_reps = 10000


for N in Ns:
    results=dict(ndims=ndims,n_reps = n_reps,N=N,
                 python= sys.version.split()[0],
                 numba =  numba.__version__,
                 llvmlite= llvmlite.__version__,
                 run_times=np.full((ndims.size,),0.),
                compile_times=np.full((ndims.size,),0.)  )
    for nt, m in enumerate(ndims):
        x= np.random.random((N,)+(m+1)*(1,)) # n by n array

        out= x.copy()

        # njit function here to ensure only one signature to match
        t0 = perf_counter()
        F = njit(add)
        # compile code
        F(x,out)
        results['compile_times'][nt] = perf_counter() - t0

        # run repetitions
        t0 = perf_counter()

        for reps in range(n_reps):
            sum = F(x, out)
        results['run_times'][nt] = perf_counter()-t0
        print(F.signatures)

    fn = f"array_results_{results['N']}_{results['python']}_{ results['numba']}_{results['llvmlite']}.pkl"
    print(' versions=', results['python'], 'numba ver=', results['numba'], ' llvmlite ver=', results['llvmlite'], 'N=',N)

    with open(fn, 'wb') as f:
        pickle.dump(results, f)

# plot all pickled result
fig, axes= plt.subplots(2,1)
for fn in sorted(glob('array_results*.pkl')):
    with open(fn, 'rb') as file:
        results = pickle.load(file)

    axes[0].plot(results['ndims'], results['run_times'],
            label=f"Python={results['python']} Numba= { results['numba']} llvmlite={results['llvmlite']} N={results['N']}")

    axes[1].plot(results['ndims'], results['compile_times'],
                 label=f"Python={results['python']} Numba= {results['numba']} llvmlite={results['llvmlite']} N={results['N']}")

for n, ax in enumerate(axes):
    ax.legend(fontsize=8)

    ax.set_ylabel(f"Time,ssec, reps ={results['n_reps']}")
    ax.set_title( 'Computation time, ' if n==0 else 'Compile time' + f"array size = {results['n_reps']}")
axes[1].set_xlabel('array Dimension')
plt.show()





