# in place operations on particle properties which are isActive
# all require working_indices_buffer ,n_active , which hold isActive indices in a fixed sized buffer
# all used numpy arrays as input, or value values., plus interger array of isActive indices/particle numbers to work on
import numpy as np
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange


# set value, add_value and get_values are wrapped by methods of particle properties, so not normallu called directly
def get_values(x1, active):
    # get values of active particles in particle property data  buffer
    # take looks slightly faster than numba
    return np.take(x1,active, axis=0)

@njitOTparallel
def set_value(x1, value, active):
    # set values ,  x1 = value for active
    if x1.ndim == 1:     # 1D
        for nn in prange(active.size):
            n = active[nn]
            x1[n] = value
    else:
        for nn in prange(active.size):
            n = active[nn]
            for m in range(x1.shape[1]):
                x1[n, m] = value

@njitOTparallel
def set_values(x1, values, active):
    # set values of active particles in working buffer,
    # values must be same size as active
    #  values may be scaled
    if x1.ndim ==1:  # 1D
        for nn in prange(active.size):
            n = active[nn]
            x1[n] = values[nn]
    else: #case Dim
        for nn in prange(active.size):
            n = active[nn]
            for m in range(x1.shape[1]):
                x1[n, m] = values[nn, m]

@njitOTparallel
def add_value_to(x1, value, active):
    # x1 += value
    if x1.ndim == 1:  # 1D
        for nn in prange(active.size):
            n = active[nn]
            x1[n] += value
    else:
        for nn in prange(active.size):
            n = active[nn]
            for m in range(x1.shape[1]):
                x1[n, m] += value


@njitOTparallel
def add_values_to(x1, values, active, scale=1.0):
    # x1 += values*scale for active particles,values same size as active
    # this version adds a vector the same size as isActive to x1
    # ie different from add_to above
    if x1.ndim == 1: # 1D
        for nn in prange(active.size):
            n = active[nn]
            x1[n] += values[nn] * scale
    else:
        for nn in range(active.size):
            n = active[nn]
            for m in prange(x1.shape[1]):
                x1[n, m ] += values[nn, m] * scale

@njitOTparallel
def copy(x1, x2, active):
    # x1 = x2 for active particles
    if x1.ndim == 1:  # 1D
        for nn in prange(active.size):
            n = active[nn]
            x1[n] = x2[n]
    # faster if range of 2nd dimension explicit
    elif x1.shape[1] == 2:
        # faster if range of 2nd dimension explicit
        for nn in prange(active.size):
            n = active[nn]
            for m in range(2):
                x1[n, m] = x2[n, m]
    elif x1.shape[1] == 3:
        for nn in prange(active.size):
            n = active[nn]
            for m in range(3):
                x1[n, m] = x2[n, m]
    else:
        for nn in prange(active.size):
            n = active[nn]
            for m in range(x1.shape[1]):
                x1[n, m] = x2[n, m]

# below are currently only called directly using pointers
# but are not used often, mainly in time step of solver
@njitOTparallel
def scale_and_copy(x1, x2, active, scale=1.0):
    # x1 = x2*scale for active particles

    if x1.ndim == 1: # 1D
        for nn in prange(active.size):
            n = active[nn]
            x1[n] = x2[n]*scale
    # faster if range of 2nd dimension explicit
    else:
        for nn in prange(active.size):
            n = active[nn]
            for m in range(x1.shape[1]):
                x1[n, m] = x2[n, m]*scale

@njitOTparallel
def add_to(x1, x2, active, scale=1.0):
    # x1 += x2*scale for active particles, x1 and values same size
    if x1.ndim == 1: # 1D
        for nn in prange(active.size):
            n = active[nn]
            x1[n] += x2[n] * scale
    else:
        for nn in prange(active.size):
            n = active[nn]
            for m in range(x1.shape[1]):
                 x1[n, m]  += x2[n, m]*scale

@njitOTparallel
def set_value_and_add(x1, value, x2, active, scale=1.0):
    # set x1= value, then  x1 += x2*scale for active particles, x1 and x2 same size
    if x1.ndim == 1: # 1D
        for nn in prange(active.size):
            n = active[nn]
            x1[n] = value + x2[n]*scale
    else:
        for nn in prange(active.size):
            n = active[nn]
            for m in range(x1.shape[1]):
                x1[n, m] = value + x2[n,m]*scale


