import numpy as np
from numba import types as nbt,jit,  njit, typeof, typed
from numba.experimental import jitclass
import os

@njit
def seed_numba_random(a):
    np.random.seed(a)

def set_caching( b):
   os.environ['oceantracker_numba_caching'] =str( 1 if b else 0)
def is_caching():
    return  os.environ['oceantracker_numba_caching'] =='1'


def njitter(f,signature,return_type=None, parallel=False, nogil=True):

    custom_njit = njit( signature, parallel=parallel,nogil=nogil)
    #return custom_njit(f)
    #return f
    return njit(f) #disabpel signatures


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

