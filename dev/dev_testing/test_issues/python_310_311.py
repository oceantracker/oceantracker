from numba import  njit
import  numba
import numpy as np
from time import perf_counter
import sys
import cProfile, pstats
import llvmlite


def add(x,out):
    # do minimal work on array to emphasize dispatch time
    # do same opertion on  all dim sizes

    x2= x.reshape(-1,1)
    out2=out.reshape(-1,1)
    for n in range(x2.shape[0]):
       out2[n,0] = x2[n,0]

profiler = cProfile.Profile()

ndims = np.arange(6)
N= 10*5
times=np.full((ndims.size,),0.)
compile_times=np.full((ndims.size,),0.)

n_reps = 100000

profiler.enable()

for nt, n in enumerate(ndims):
    x= np.random.random((N,)+(n+1)*(1,))

    out= x.copy()



    # compile here to ensure only one signature to match
    t0 = perf_counter()
    F=njit(add)
    F(x,out) # compile code
    compile_times[nt] = perf_counter() - t0

    # run repetions
    t0 = perf_counter()

    for reps in range(n_reps):
        sum = F(x, out)
    times[nt] = perf_counter()-t0

profiler.disable()


v=  sys.version_info
print('python ver=',  f'{v.major}.{v.minor}.{v.micro}', 'numba ver=', numba.__version__, ' llvmlite ver=', llvmlite.__version__)


print('\t run time for diff array dims, 1-6',times)
print('')
print('\t compile  time for diff array dims, 1-6',compile_times)
print('')
# print profiling results
print('------------------------------')
print('python ver=',  f'{v.major}.{v.minor}.{v.micro}', 'numba ver=', numba.__version__, '   llvmlite ver=', llvmlite.__version__)
print('------------------------------')
profiler.dump_stats('temp.prof')  # Save results to a file
ps = pstats.Stats('temp.prof')
ps.sort_stats('tottime')
ps.print_stats(5)


