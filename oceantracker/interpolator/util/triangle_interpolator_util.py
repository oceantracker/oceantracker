import numpy as np
from numba import njit,prange, types as nbt, typeof, from_dtype
from oceantracker.util.profiling_util import function_profiler

# record variable to hold walk info/counts
# to reduce number of args required in numba functions and be morr readable
from oceantracker.util.numba_util import  njitOT
import os
from copy import copy
from oceantracker.shared_info import shared_info as si
from oceantracker.definitions import cell_search_status_flags
# globals

# globals to complile into numba to save pass arguments
psf = si.particle_status_flags
status_moving = int(psf['moving'])
status_on_bottom = int(psf['on_bottom'])
status_stranded_by_tide = int(psf['stranded_by_tide'])
status_outside_open_boundary = int(psf['outside_open_boundary'])
status_dead = int(psf['dead'])
status_bad_cord = int(psf['bad_cord'])
status_cell_search_failed = int(psf['cell_search_failed'])

cell_search_ok= int(cell_search_status_flags.ok)
cell_search_domain_edge= int(cell_search_status_flags.domain_edge)
cell_search_open_boundary_edge= int(cell_search_status_flags.open_boundary_edge)
cell_search_dry_cell_edge= int(cell_search_status_flags.dry_cell_edge)

search_bad_cord= int(cell_search_status_flags.bad_cord)

search_failed= int(cell_search_status_flags.failed)


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
def BCwalk(xq, tri_walk_AOS, dry_cell_index,
                n_cell, cell_search_status,bc_cords,
                walk_counts,
                max_triangle_walk_steps, bc_walk_tol, open_boundary_type, block_dry_cells,
                active):
    # Barycentric walk across triangles to find cells

    bc = np.zeros((3,), dtype=np.float64) # working space
    # shortcuts needed to use prange


    # loop over active particles in place
    for nn in prange(active.size):
        n= active[nn]

        # start with good cell search
        cell_search_status[n] = cell_search_ok

        if np.isnan(xq[n, 0]) or np.isnan(xq[n, 1]):
            # if any is nan copy all and move on
            cell_search_status[n]= search_bad_cord
            walk_counts[3] += 1  # count nans
            continue

        n_tri = n_cell[n]  # starting triangle
        # do BC walk
        n_steps = 0

        while n_steps < max_triangle_walk_steps:
            # update barcentric cords of xq

            n_min, n_max = _get_single_BC_cord_numba(xq[n, :], tri_walk_AOS[n_tri]['bc_transform'], bc)

            if bc[n_min] > -bc_walk_tol and bc[n_max] < 1. + bc_walk_tol:
                # are now inside triangle, leave particle status as is
                break  # with current n_tri as found cell

            n_steps += 1
            # move to neighbour triangle at face with smallest bc then test bc cord again
            next_tri = tri_walk_AOS[n_tri]['adjacency'][n_min]  # n_min is the face num in  tri to move across

            if next_tri < 0:
                # if no new adjacent triangle, then are trying to exit domain at a boundary triangle,
                # keep n_cell, bc  unchanged
                if open_boundary_type > 0 and next_tri == cell_search_open_boundary_edge:  # outside domain
                    # leave x, bc, cell, location  unchanged as outside
                    cell_search_status[n] = cell_search_open_boundary_edge
                    break
                else:  # n_tri == -1 outside domain and any future
                    # solid boundary, so just move back
                    cell_search_status[n] = cell_search_domain_edge
                    break

            # check for dry cell
            if block_dry_cells:  # is faster split into 2 ifs, not sure why
                if dry_cell_index[next_tri] > 128:
                    # treats dry cell like a lateral boundary,  move back and keep triangle the same
                    cell_search_status[n] = cell_search_dry_cell_edge
                    break

            n_tri = next_tri

        # not found in given number of search steps
        if n_steps >= max_triangle_walk_steps:  # dont update cell
            cell_search_status[n] = search_failed


        if cell_search_status[n] == cell_search_ok:
            # update cell anc BC for new triangle, if not fixed in solver after full step
            n_cell[n] = n_tri
            for i in range(3): bc_cords[n, i] = bc[i]

        walk_counts[0] += 1  # particles walked
        walk_counts[1] += n_steps  # steps taken
        walk_counts[2] = max(n_steps,  walk_counts[2])  # longest walk

@njitOT
def _move_back(x, x_old):
    for i in range(x.shape[0]): x[i] = x_old[i]

@njitOT
def calc_BC_cords_numba(x, n_cells, BCtransform, bc):
    # get BC cords of set of points x inside given cells and return in bc

    for n in range(x.shape[0]):
        _get_single_BC_cord_numba(x[n, :], BCtransform[n_cells[n], :, :], bc[n, :])

@njitOT
def check_if_point_inside_triangle_connected_to_node(x, node, node_to_tri_map,tri_per_node, BCtransform, bc_walk_tol):
    # get BC cords of set of points x inside given cells and return in bc
    N = x.shape[0]
    is_inside_domain= np.full((N,),False)
    bc = np.zeros((N,3), dtype=np.float64)  # working space
    n_cell = np.full((N,),-1, np.int32)

    for n in range(x.shape[0]):
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

@njit()
def interp2D_kernal_time_independent(data,bc):
    # eval interp from values at triangle nodes
    v = 0.
    for m in range(3):
        v += bc[m] * data[m]
    return v

@njit()
def interp2D_kernal_time_dependent(data,bc,):
    # eval interp from values at triangle nodes
    v = 0.
    for m in range(3):
        v += bc[m] * data[m]
    return v









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

