from numba import njit
import numpy as np
from time import perf_counter
import timeit
from oceantracker.util import numpy_util


@njit()
def A0(out):
    return out
@njit()
def A1(a, out):
    out[0,0] = a[0,0]
    return out
@njit()
def A2(a,b):
    v =0.
    for n in range(a.shape[0]):
        v += a[n,0] + b[n,0]
    return v

@njit()
def A2_aos(s):
    v = 0.
    for n in range(a.shape[0]):
        v += s['a'][n, 0] + s['b'][n, 0]
    return v



@njit()
def A5(a,b,c,d,e):
    v = 0.
    for n in range(a.shape[0]):
        v += a[n, 0] + b[n, 0] + c[n, 0] + d[n, 0] + e[n, 0]
    return v
@njit()
def A5_aos(s):
    v=0.
    for ss in s:
        v += ss['a'][0] + ss['b'][0]  + ss['c'][0] + ss['d'][0] + ss['e'][0]
    return v

@njit()
def A5_soa(s):
    a,b,c,d,e = (np.asarray(s[0]['a']), np.asarray(s[0]['b']),np.asarray(s[0]['c']),
                 np.asarray(s[0]['d']),np.asarray(s[0]['e']))
    v=0.
    for n in range(a.shape[0]):
        v += a[n,0] + b[n,0]  + c[n,0] + d[n,0] + e[n,0]
    return v

def numpy_structure_of_arrays_from_dict(d):
    # return a array of numpy sturcture with fields give by dict keys and copy of  from dictionary
    # array is  based on first dimension, which must be the same

    # wont transoher dattime64, str, dict etc
    dtype=[]
    shape0=[]
    for key,val in d.items():
        if type(val) == np.ndarray:
            shape0.append(val.shape[0])
            dtype.append((key,val.dtype,val.shape))
    print(dtype)
    if np.unique(np.asarray(shape0)).size >1:
        raise Exception('numpy_array_of_structures_from_dict all dict items must be arrays and have the same first dime ' )
    # check if too big for numpy indexing limit
    S = np.zeros((1,),dtype=dtype)

    #copy dictionary data and point dict at structure's data
    for name in S.dtype.names:
        S[name][:] = np.copy(d[name])

        pass

    return S

N=10**6
a = np.random.rand(N,3)
out=a.copy()

s2_aos= numpy_util.numpy_array_of_structures_from_dict(dict(a=a, b=2 * a))
s2_soa= numpy_structure_of_arrays_from_dict(dict(a=a, b=2 * a))
s5_aos= numpy_util.numpy_array_of_structures_from_dict( dict(a=a,b=2*a,c=2*a, d=2*a,e=2*a))
s5_soa= numpy_structure_of_arrays_from_dict( dict(a=a,b=2*a,c=2*a, d=2*a,e=2*a))

reps=1000
print('msec /call')


print(f'{A0.__name__}   \t', timeit.timeit(stmt= lambda : A0(out), setup= lambda : A0(out), number=reps) * 1000 / reps)

print(f'{A1.__name__}   \t', timeit.timeit(stmt= lambda : A1(a,out), setup= lambda : A1(a,out), number=reps) * 1000 / reps)

print(f'{A2.__name__}   \t', timeit.timeit(stmt= lambda : A2(a,a), setup= lambda : A2(a,a), number=reps) * 1000 / reps)
print(f'{A2_aos.__name__}\t', timeit.timeit(stmt= lambda : A2_aos(s2_aos), setup= lambda : A2_aos(s2_aos), number=reps) * 1000 / reps)

print(f'{A5.__name__}    \t', timeit.timeit(stmt= lambda : A5(a,a,a,a,a), setup= lambda : A5(a,a,a,a,a), number=reps) * 1000 / reps)
print(f'{A5_aos.__name__}\t', timeit.timeit(stmt= lambda : A5_aos(s5_aos), setup= lambda : A5_aos(s5_aos), number=reps) * 1000 / reps)
print(f'{A5_soa.__name__}\t', timeit.timeit(stmt= lambda : A5_soa(s5_soa), setup= lambda : A5_soa(s5_soa), number=reps) * 1000 / reps)
