from numba import njit
import numpy as np
from oceantracker.util.numba_util import time_numba_code
from interp_varients import find_simd_code,catalog_simd_code
@njit
def Fboth(x,out, sel):

    if x.ndim == 1:
        for n in sel:
            out[n]=  np.sqrt(x[n])

    elif x.ndim == 2:
        for n in sel:
            out[n] =0.
            for m in range(3):
                out[n] =  np.sqrt(x[n,m])

@njit
def F1(x,out,sel):
    for n in sel:
            out[n] =  np.sqrt(x[n] )

@njit
def F2(x,out, sel):
    for n in sel:
        out[n] =0.
        for m in range(3):
            out[n]= np.sqrt(x[n,m])

N=10**6
sel = np.random.randint(0,N, int(.9*N))
x1= np.random.random((N,))
x2= np.random.random((N,3))
out=np.empty_like(x1)

t1a= time_numba_code(F1, x1,out, sel, number=10)
t1 = time_numba_code(Fboth, x1, out,sel, number=10)

t2 = time_numba_code(Fboth, x2,out, sel, number=10)
t2a= time_numba_code(F2, x2, out, sel, number=10)

print(t1/t1a,t2/t2a)

with open('F1_1.asm','w') as f:
    f.write(Fboth.inspect_asm(Fboth.signatures[0]))
    
with open('F1_2.asm','w') as f:
    f.write(Fboth.inspect_asm(Fboth.signatures[1]))

