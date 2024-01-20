import numpy as np
from numba import types as nbt,jit,  njit, typeof, typed
from numba.experimental import jitclass
import os
from time import perf_counter

@njit
def seed_numba_random(a):
    np.random.seed(a)

#def set_caching(b):
#   os.environ['oceantracker_numba_caching'] =str(1 if b else 0)
#def is_caching():
#    return  os.environ['oceantracker_numba_caching'] =='1'

numba_func_info={}
def njitOT(func):
    # add abity to inspect the functions after compllation
    key = func.__module__ +'.' + func.__name__
    numba_func_info[key]=func
    return njit(func, cache=os.environ['oceantracker_numba_caching'] == '1')



def find_simd_code(func, sig=0, limit=20, show=False):

    count = 0
    simd_lines=[]
    keywords = ['addp', 'subp','andp','andnp','vmulp']
    keywords+=['ADDPS', 'SUBPS', 'MULPS', 'DIVPS', 'RCPPS', 'SQRTPS', 'MAXPS', 'MINPS', 'RSQRTPS']
    keywords= [k.lower() for k in keywords]

    if not hasattr(func,'inspect_asm'):
        ll = 'Nested fuction no serate code'
        simd_lines.append(ll)
        if show:
            print(func.__name__, ll)
        return simd_lines

    for l in func.inspect_asm(func.signatures[sig]).split('\n'):

        if any([(v in l.lower()) for v in keywords]):
            count += 1
            ll= l.replace('\t',' ')
            simd_lines.append(ll)
            if show:
                print(func.__name__,ll )
            if count >= limit:
                break
    if count == 0:
        ll = 'No SIMD instructions found'
        simd_lines.append(ll)
        if show:
            print(func.__name__,ll )
    return simd_lines

def time_numba_code(fun,*args, number=10):

    # compile if neded
    fun(*args)

    t0 = perf_counter()
    for n in range(number):
        fun(*args)
    return (perf_counter()-t0)/number

# below not used

def numba_class_from_dict(d):
    # return a numba class instance with attributes given by dict keys
    # used to pass many arguments to numba functions efficiently as attributes of one class variable
    # will ignore any dict within the given dict
    # build class signature
    sig=[]
    for key,val in d.items():
        if type(val) != dict:
            sig.append((key,typeof(val)))

    @jitclass(sig)
    class ContainerHolder(object):
        def __init__(self): pass

    C = ContainerHolder()
    # set values of attributes to those in the dict
    for key, t in sig:
        setattr(C, key, d[key])
    return C

