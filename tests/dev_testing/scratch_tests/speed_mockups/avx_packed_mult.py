from numba import njit
from oceantracker.util.numba_util import time_numba_code
from interp_by_tri_nodes import sel_fraction
from oceantracker.util.numba_util import count_simd_intructions,compare_simd
import numpy as np
from matplotlib import pyplot as  plt
@njit()
def f_base(x, y):
    #return  np.sqrt(x * y)
    return  x * y
    #return  x > y
@njit
def F0(x,y,out,sel):
    for n in range(x.shape[0]):
        out[n] = f_base(x[n], y[n])
@njit
def F1(x,y, out,sel):
    for n in sel:
        out[n] = f_base(x[n] , y[n])
@njit
def F2(x,y, out, mask):
    for n in range(x.shape[0]):
        if mask[n]:
            out[n] =f_base(x[n], y[n])
@njit
def F3(x,y, out, mask):
    # branchless masking
    for n in range(x.shape[0]):
        out[n] = mask[n]*f_base(x[n], y[n]) + (not  mask[n])*out[n]
def get_data(N,dtype=np.float32):
    x = np. random.random((N,)).astype(dtype)
    y = np. random.random((N,)).astype(dtype)
    out = np.zeros(x.shape,dtype=x.dtype)
    return x,y,out

def run_code(F,N,frac=.7,reps=10,dtype=np.float32):
    sel,mask= sel_fraction(N,frac=frac)
    x,y,out = get_data(N,dtype=dtype)

    uses_mask = F in [F2,F3]
    s = mask if uses_mask else sel
    F(x,y,out,s) # compile code first

    t = 0.
    for n in range(reps):
        # make new selec to avoid branch prediction bias
        sel, mask= sel_fraction(N,frac= frac)
        # use new data each time to minimise cache effect
        x,y,out = get_data(N,dtype=dtype)
        s = mask if uses_mask else sel
        t += time_numba_code(F,x,y,out,s,number=1)
    return t

N= 10**6
Fs=(F0,F1,F2,F3)
dt =np.float32

# check if the same result
sel,mask= sel_fraction(N,frac=.5)
x,y,out = get_data(N,dtype=dt)
for F in Fs:
    s = mask if F in [F2,F3] else sel
    out[:]= 0.
    F(x,y,out,s)
    print(F.__name__,out.sum()) # check results

reps=10
fracs= np.arange(.001,1.,.025)
t= np.zeros((len(Fs),fracs.size),dtype=np.float64,)

for m, frac in enumerate(fracs):
     for n,f in enumerate(Fs):
        t[n,m] = run_code(f,N,reps=reps,frac=frac,dtype=dt)

a=compare_simd(Fs)
print('times',t[:,-1])
print('ratios',t[1:,-1]/t[0,-1])

for n, f in enumerate(Fs):
    plt.plot(fracs,t[n,:],label=f.__name__)

plt.legend()
plt.show()

for n, f in enumerate(Fs[1:]):
    plt.plot(fracs,t[n+1,:]/t[0,:],label=f.__name__)

plt.legend()
plt.ylabel('time relative to doing all')
plt.show()