import numpy as np
from oceantracker.util.profiling_util import function_profiler

# record variable to hold walk info/counts
# to reduce number of args required in numba functions and be morr readable
from oceantracker.util.numba_util import  njitOT, njitOTparallel
import numba as nb

import os
from copy import copy
from oceantracker.shared_info import shared_info as si


#below is called by another numba function which will work out signature on first call
@njitOT
def _get_single_BC_cord_numba(x, BCtransform, bc):
    # get BC cord of x for one triangle from DT transform matrix inverse, see scipy.spatial.Delaunay
    # also return index the smallest BC for walk and largest
    # returns n_min the index of smallest bc used to choose next triangle
    # bc is (3,) pre-allocated working scale, used to return BC's

    # do (2x2) matrix multiplication of  bc[:2]=BCtransform[:2,:2]*(x-transform[:,2]
    # for i in range(2): bc[i] = 0.
    for i in range(2):
        #for j in range(2):
        #    bc[i] +=  BCtransform[i,j]*(x[j]-BCtransform[2,j])
        # replace loop with faster explicit adds, as no need to zero bc[:] above
        bc[i] = BCtransform[i, 0] * (x[0] - BCtransform[2, 0]) + BCtransform[i, 1] * (x[1] - BCtransform[2, 1])

    bc[2] = 1.0 - bc[0] - bc[1]

    return np.argmin(bc), np.argmax(bc)


@njitOT
def calc_BC_cords_numba(x, n_cells, BCtransform, bc):
    # get BC cords of set of points x inside given cells and return in bc

    for n in range(x.shape[0]):
        _get_single_BC_cord_numba(x[n, :], BCtransform[n_cells[n], :, :], bc[n, :])

@njitOTparallel
def check_if_point_inside_triangle_connected_to_node(x, node, node_to_tri_map,tri_per_node, BCtransform, bc_walk_tol):
    # get BC cords of set of points x inside given cells and return in bc variable
    N = x.shape[0]
    is_inside_domain= np.full((N,),False)
    bc = np.zeros((N,3), dtype=np.float64)  # working space
    n_cell = np.full((N,),-1, np.int32)

    for n in nb.prange(x.shape[0]):
        nn = node[n]
        # loop over tri attached to node
        for m in range(tri_per_node[nn]):
            n_tri = node_to_tri_map[nn, m]
            n_min, n_max= _get_single_BC_cord_numba(x[n, :2], BCtransform[n_tri, :, :], bc[n,:])
            if bc[n,n_min] > -bc_walk_tol and bc[n, n_max] < 1. + bc_walk_tol:
                # found triangle
                n_cell[n] = n_tri
                is_inside_domain[n]= True
                continue
    return is_inside_domain, n_cell, bc

@njitOT
def get_BC_transform_matrix(points, simplices):
    # pre-build barycectric tranforms for 2D triangles based in scipy spatial qhull as used by scipy.Delauny

    """ from scipy ............
    Compute barycentric affine coordinate transformations for given simplices.
    Returns
    -------
    Tinvs : array, shape (nsimplex, ndim+1, ndim)
        Barycentric transforms for each simplex.
        Tinvs[i,:ndim,:ndim] contains inverse of the matrix ``T``,
        and Tinvs[i,ndim,:] contains the vector ``r_n`` (see below).
    Notes
    -----
    Barycentric transform from ``x`` to ``c`` is defined by::
        T c = x - r_n
    where the ``r_1, ..., r_n`` are the vertices of the simplex.
    The matrix ``T`` is defined by the condition::
        T e_j = r_j - r_n
    where ``e_j`` is the unit axis vector, e.g, ``e_2 = [0,1,0,0,...]``
    This implies that ``T_ij = (r_j - r_n)_i``.
    For the barycentric transforms, we need to compute the inverse
    matrix ``T^-1`` and store the vectors ``r_n`` for each vertex.
    These are stacked into the `Tinvs` returned.
    """

    ndim = 2  # only works on 2D triangles
    nsimplex = simplices.shape[0]

    T = np.empty((ndim, ndim), dtype=np.double)
    Tinvs = np.zeros((nsimplex, ndim + 1, ndim), dtype=np.double)

    for isimplex in range(nsimplex):
        for i in range(ndim):
            Tinvs[isimplex, ndim, i] = points[simplices[isimplex, ndim], i]  # puts cords of last point as extra column, ie r_n vector
            for j in range(ndim):
                T[i, j] = (points[simplices[isimplex, j], i] - Tinvs[isimplex, ndim, i])
            Tinvs[isimplex, i, i] = np.nan

        # form inverse of 2 by 2, https://mathworld.wolfram.com/MatrixInverse.html
        # compute matrix determinate of 2 by 2
        det = T[0, 0] * T[1, 1] - T[0, 1] * T[1, 0]

        # inverse  matrix term by term
        Tinvs[isimplex, 0, 0] = T[1, 1] / det
        Tinvs[isimplex, 1, 1] = T[0, 0] / det
        Tinvs[isimplex, 0, 1] = -T[0, 1] / det
        Tinvs[isimplex, 1, 0] = -T[1, 0] / det

    return Tinvs

# Below is numpy version of numba BC cord code, now only used as check
#________________________________________________
def get_cell_cords_check(bc_transform,x,n_cell):
    # barycentric cords, only for use with non-improved scipy and KDtree for al time steps
    # numba code does this faster
    #print('shapes',bc_transform.shape,x.shape, n_cell.shape)
    TT = np.take(bc_transform, n_cell, axis=0,)
    b = np.full((x.shape[0],3), np.nan, order='C')
    b[:,:2] = np.einsum('ijk,ik->ij', TT[:, :2], x[:, :2] - TT[:, 2], order='C')  # Einstein summation
    b[:,2] = 1. - b[:,:2].sum(axis=1)
    return b



#________ old versions

