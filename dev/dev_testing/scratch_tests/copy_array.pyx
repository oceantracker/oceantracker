import numpy as np
cimport numpy as cnp
from  cython import  parallel, boundscheck, wraparound

@boundscheck(False)
@wraparound(False)
def FnD_4_copy_cython(  cnp.ndarray[cnp.float64_t, ndim=2] x,
                    cnp.ndarray[cnp.float64_t, ndim=2] y,
                    cnp.ndarray[cnp.int32_t, ndim=1] index,
                  ):
    cdef int nn, n,m
    with nogil:
        for nn in parallel.prange(index.shape[0]) :
        #for nn in parallel.prange(index.shape[0]):
            n = index[nn]
            for  m in range(x.shape[1]) :
                y[n,m] = x[n,m]