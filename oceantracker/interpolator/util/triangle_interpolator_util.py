import numpy as np
from numba import njit,prange, types as nbt, typeof, from_dtype
from oceantracker.util.profiling_util import function_profiler
from oceantracker.common_info_default_param_dict_templates import particle_info
# record variable to hold walk info/counts
# to reduce number of args required in numba functions and be morr readable

# globals
# todo make numpy structure?
status_moving = int(particle_info['status_flags']['moving'])
status_on_bottom = int(particle_info['status_flags']['on_bottom'])
status_stranded_by_tide = int(particle_info['status_flags']['stranded_by_tide'])

status_outside_open_boundary = int(particle_info['status_flags']['outside_open_boundary'])
status_dead = int(particle_info['status_flags']['dead'])
status_bad_cord = int(particle_info['status_flags']['bad_cord'])
status_cell_search_failed = int(particle_info['status_flags']['cell_search_failed'])

#below is called by another numba function which will work out signature on first call
@njit(inline='always')
def _get_single_BC_cord_numba(x, BCtransform, bc):
    # get BC cord of x for one triangle from DT transform matrix inverse, see scipy.spatial.Delaunay
    # also return index the smallest BC for walk and largest
    # returns n_min the index of smallest bc used to choose next triangle
    # bc is (3,) pre-allocated working scale, used to return BC's

    # do (2x2) matrix multiplication of  bc[:2]=BCtransform[:2,:2]*(x-transform[:,2]
    # for i in range(2): bc[i] = 0.
    for i in range(2):
        # for j in range(2):
        #  bc[i] +=  BCtransform[i,j]*(x[j]-BCtransform[2,j])
        # replace loop with faster explicit adds, as no need to zero bc[:] above
        bc[i] = BCtransform[i, 0] * (x[0] - BCtransform[2, 0]) + BCtransform[i, 1] * (x[1] - BCtransform[2, 1])

    bc[2] = 1.0 - bc[0] - bc[1]

    return np.argmin(bc), np.argmax(bc)

# ________ Barycentric triangle walk________
@njit()
def BCwalk_with_move_backs(xq,
                           tri_walk_AOS, dry_cell_index,
                           x_last_good, n_cell,status,bc_cords,
                            walk_counts,
                           max_triangle_walk_steps, bc_walk_tol, open_boundary_type, block_dry_cells,
                           active):
    # Barycentric walk across triangles to find cells

    bc = np.zeros((3,), dtype=np.float64) # working space
    # shortcuts needed to use prange


    # loop over active particles in place
    for nn in prange(active.size):
        n= active[nn]

        if np.isnan(xq[n, 0]) or np.isnan(xq[n, 1]):
            # if any is nan copy all and move on
            _move_back(xq[n,:], x_last_good[n, :])
            walk_counts[3] += 1  # count nans
            continue

        n_tri = n_cell[n]  # starting triangle
        # do BC walk
        n_steps = 0
        move_back = False

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
                if open_boundary_type > 0 and next_tri == -2:  # outside domain
                    # leave x, bc, cell, location  unchanged as outside
                    status[n] = status_outside_open_boundary
                    break
                else:  # n_tri == -1 outside domain and any future
                    # solid boundary, so just move back
                    move_back = True
                    break

            # check for dry cell
            if block_dry_cells:  # is faster split into 2 ifs, not sure why
                if dry_cell_index[next_tri] > 128:
                    # treats dry cell like a lateral boundary,  move back and keep triangle the same
                    move_back = True
                    break

            n_tri = next_tri

        # not found in given number of search steps
        if n_steps >= max_triangle_walk_steps:  # dont update cell
            status[n] = status_cell_search_failed
            # move_back = True# todo shoul it just move back, not retyr?do move back externally

        if move_back:
            # move back dont update
            _move_back(xq[n,:], x_last_good[n, :])
        else:
            # update cell anc BC for new triangle
            n_cell[n] = n_tri
            for i in range(3): bc_cords[n, i] = bc[i]

        walk_counts[0] += 1  # particles walked
        walk_counts[1] += n_steps  # steps taken
        walk_counts[2] = max(n_steps,  walk_counts[2])  # longest walk

@njit()
def _move_back(x, x_old):
    for i in range(x.shape[0]): x[i] = x_old[i]

@njit
def get_BC_cords_numba(x, n_cells, BCtransform, bc):
    # get BC cords of set of points x inside given cells and return in bc

    for n in range(x.shape[0]):
        _get_single_BC_cord_numba(x[n, :], BCtransform[n_cells[n], :, :], bc[n, :])

@njit
def check_if_point_inside_triangle_connected_to_node(x, node, node_to_tri_map,tri_per_node, BCtransform, bc_walk_tol):
    # get BC cords of set of points x inside given cells and return in bc
    bc = np.zeros((3,), dtype=np.float64)  # working space
    n_cell = np.full((x.shape[0],),-1, np.int32)
    for n in range(x.shape[0]):
        nn = node[n]
        # loop over tri attached to node
        for m in range(tri_per_node[nn]):
            n_tri = node_to_tri_map[nn, m]
            n_min,n_max= _get_single_BC_cord_numba(x[n, :2], BCtransform[n_tri, :, :], bc)
            if    bc[n_min] > -bc_walk_tol and bc[n_max] < 1. + bc_walk_tol:
                # found triangle
                n_cell[n] = n_tri
                continue
    return n_cell

@njit
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

@njit(inline='always')
def _eval_z_at_nz_cell_v2(tf, nz3, zlevel1, zlevel2, BCcord, zout):
    # eval zlevel at particle location and depth cell, return z and nodes required for evaluation
    for nz_inc in range(2):
        zout[nz_inc] = 0.
        for m in range(3):
            nz = nz3[m] + nz_inc # move up to bottom, so not out of range
            zout[nz_inc] += BCcord[m] * (zlevel1[nz, m] *  tf[1] + zlevel2[nz, m] * tf[0])


@njit()
def get_depth_cell_time_varying_Slayer_or_LSCgrid_v2(xq,
                                                  triangles, zlevel_vertex, bottom_cell_index, z0,
                                                  n_cell, status, bc_cords, nz_cell, z_fraction, z_fraction_bottom_layer,
                                                  current_buffer_steps, current_fractional_time_steps,
                                                  walk_counts,
                                                  active):
    # find the zlayer for each node of cell containing each particle and at two time slices of hindcast  between nz_bottom and number of z levels
    # LSC grid means must track vertical nodes for each particle
    # nz_with_bottom is the lowest cell in grid, is 0 for slayer vertical grids, but may be > 0 for LSC grids
    # nz_with_bottom must be time independent
    # vertical walk to search for a particle's layer in the grid, nz_cell

    nz_top_cell = zlevel_vertex.shape[2] - 2
    zlevel1 = zlevel_vertex[current_buffer_steps[0], ...]
    zlevel2 = zlevel_vertex[current_buffer_steps[1], ...]
    nz3= np.zeros((3,),dtype=np.int32)
    z_out = np.zeros((2,), dtype=np.float64)

    for nn in prange(active.size):  # loop over active particles
        n = active[nn]
        bc = bc_cords[n, :]
        nc = n_cell[n]

        nodes = triangles[nc, :]  # nodes for the particle's cell
        bottom_nz_nodes = bottom_cell_index[nodes]
        bottom_nz_cell = np.min(bottom_nz_nodes)  # cell at bottom is smallest of those in triangle
        zl1 = zlevel1[nc,...]
        zl2 = zlevel2[nc, ...]

        # preserve status if stranded by tide
        if status[n] == status_stranded_by_tide:
            nz_cell[n] = bottom_nz_cell
            # update nodes above and below
            _eval_z_at_nz_cell(current_fractional_time_steps, bottom_nz_nodes, zl1, zl2, bc,z_out)
            xq[n, 2] = z_out[0]
            z_fraction[n] = 0.0
            continue

        # make any already on bottom active, may be flagged on bottom if found on bottom, below
        if status[n] == status_on_bottom: status[n] = status_moving
        zq = xq[n, 2]

        # walk up from bottom on each vertex
        n_vertical_steps = 0
        for m in range(3):
            for nz in range(bottom_nz_nodes[m], zlevel_vertex.shape[2]-1):
                nz3[m] = nz
                if zl1[nz+1,m] > xq[n,2]: break

        nz = np.min(nz3) # only from first time step

        _eval_z_at_nz_cell(current_fractional_time_steps, nz3, zl1, zl2, bc, z_out)

        zq = min(zq, z_out[1])  # clip to surface
        zq = max(zq, z_out[0]) # clip to bottom

        # nz now holds required cell
        dz = z_out[1] - z_out[0]
        # get z linear z_fraction
        if dz < z0:
            z_fraction[n] = 0.0
        else:
            z_fraction[n] = (zq - z_out[0]) / dz

        # extra work if in bottom cell
        z_fraction_bottom_layer[n] = -999.  # flag as not in bottom layer, will become >= 0 if in layer
        if nz == bottom_nz_cell:
            # set status if on the bottom set status
            if zq < z_out[0] + z0:
                status[n] = status_on_bottom
                zq = z_out[0]

            # get z_fraction for log layer
            if dz < z0:
                z_fraction_bottom_layer[n] = 0.0
            else:
                # adjust z fraction so that linear interp acts like log layer
                z0p = z0 / dz
                z_fraction_bottom_layer[n] = (np.log(z_fraction[n] + z0p) - np.log(z0p)) / (np.log(1. + z0p) - np.log(z0p))

        # record new depth cell
        nz_cell[n] = nz
        xq[n, 2] = zq
        # step count stats, tidal stranded particles are not counted
        walk_counts[6] += n_vertical_steps
        walk_counts[7] = max(walk_counts[7], n_vertical_steps)  # record max number of steps

@njit(inline='always')
def _eval_z_at_nz_cell(tf, nz_cell, zlevel1, zlevel2, nz_bottom_nodes, nz_top_cell, BCcord):
    # eval zlevel at particle location and depth cell, return z and nodes required for evaluation
    z = 0.
    for m in range(3):
        nz = max(min(nz_cell, nz_top_cell+1), nz_bottom_nodes[m]) # move up to bottom, so not out of range
        z += BCcord[m] * (zlevel1[nz, m] *  tf[1] + zlevel2[nz, m] * tf[0])
    return z

@njit()
def get_depth_cell_time_varying_Slayer_or_LSCgrid(xq,
                                                  triangles, zlevel_vertex, bottom_cell_index, z0,
                                                  n_cell, status, bc_cords, nz_cell, z_fraction, z_fraction_bottom_layer,
                                                  current_buffer_steps, current_fractional_time_steps,
                                                  walk_counts,
                                                  active):
    # find the zlayer for each node of cell containing each particle and at two time slices of hindcast  between nz_bottom and number of z levels
    # LSC grid means must track vertical nodes for each particle
    # nz_with_bottom is the lowest cell in grid, is 0 for slayer vertical grids, but may be > 0 for LSC grids
    # nz_with_bottom must be time independent
    # vertical walk to search for a particle's layer in the grid, nz_cell

    nz_top_cell = zlevel_vertex.shape[2] - 2
    zlevel1 = zlevel_vertex[current_buffer_steps[0], ...]
    zlevel2 = zlevel_vertex[current_buffer_steps[1], ...]

    for nn in prange(active.size):  # loop over active particles
        n = active[nn]
        bc = bc_cords[n, :]
        nc = n_cell[n]

        nodes = triangles[nc, :]  # nodes for the particle's cell
        bottom_nz_nodes = bottom_cell_index[nodes]
        bottom_nz_cell = np.min(bottom_nz_nodes)  # cell at bottom is smallest of those in triangle
        zl1 = zlevel1[nc,...]
        zl2 = zlevel2[nc, ...]

        # preserve status if stranded by tide
        if status[n] == status_stranded_by_tide:
            nz_cell[n] = bottom_nz_cell
            # update nodes above and below
            z_below = _eval_z_at_nz_cell(current_fractional_time_steps, bottom_nz_cell, zl1, zl2, bottom_nz_nodes,nz_top_cell, bc)
            xq[n, 2] = z_below
            z_fraction[n] = 0.0
            continue

        n_vertical_steps = 0
        zq = xq[n, 2]

        # make any already on bottom active, may be flagged on bottom if found on bottom, below
        if status[n] == status_on_bottom: status[n] = status_moving

        # find zlevel above and below  current vertical cell
        nz = nz_cell[n]
        z_below = _eval_z_at_nz_cell(current_fractional_time_steps, nz, zl1, zl2, bottom_nz_nodes,nz_top_cell, bc)

        if zq >= z_below:
             # search upwards, do nothing if z_above > zq[n] > z_below, ie current nodes are correct
            z_above = _eval_z_at_nz_cell(current_fractional_time_steps, nz + 1, zl1, zl2, bottom_nz_nodes,nz_top_cell, bc)

            while zq > z_above and nz < nz_top_cell:
                nz += 1
                n_vertical_steps += 1
                z_below = z_above
                z_above = _eval_z_at_nz_cell(current_fractional_time_steps, nz + 1, zl1, zl2, bottom_nz_nodes, nz_top_cell, bc)
            # clip to free surface height
            if zq > z_above:
                zq = z_above
                nz = nz_top_cell
        else:
            # search downwards, move down
            nz = max(nz - 1, bottom_nz_cell) # take one step down to start
            z_above = z_below
            z_below = _eval_z_at_nz_cell(current_fractional_time_steps, nz, zl1, zl2, bottom_nz_nodes,nz_top_cell, bc)

            while zq < z_below and nz > bottom_nz_cell:
                nz -= 1
                n_vertical_steps += 1
                z_above = z_below  # retain for dz calc.
                z_below = _eval_z_at_nz_cell(current_fractional_time_steps, nz, zl1, zl2, bottom_nz_nodes,nz_top_cell, bc)

            # clip to bottom
            if zq < z_below:
                zq = z_below
                nz = bottom_nz_cell

        # nz now holds required cell
        dz = z_above - z_below
        # get z linear z_fraction
        if dz < z0:
            z_fraction[n] = 0.0
        else:
            z_fraction[n] = (zq - z_below) / dz

        # extra work if in bottom cell
        z_fraction_bottom_layer[n] = -999.  # flag as not in bottom layer, will become >= 0 if in layer
        if nz == bottom_nz_cell:
            # set status if on the bottom set status
            if zq < z_below + z0:
                status[n] = status_on_bottom
                zq = z_below

            # get z_fraction for log layer
            if dz < z0:
                z_fraction_bottom_layer[n] = 0.0
            else:
                # adjust z fraction so that linear interp acts like log layer
                z0p = z0 / dz
                z_fraction_bottom_layer[n] = (np.log(z_fraction[n] + z0p) - np.log(z0p)) / (np.log(1. + z0p) - np.log(z0p))

        # record new depth cell
        nz_cell[n] = nz
        xq[n, 2] = zq
        # step count stats, tidal stranded particles are not counted
        walk_counts[6] += n_vertical_steps
        walk_counts[7] = max(walk_counts[7], n_vertical_steps)  # record max number of steps

# Below is numpy version of numba BC cord code, now only used as check
#________________________________________________
def get_cell_cords_check(self,x,n_cell):
    # barycentric cords, only for use with non-improved scipy and KDtree for al time steps
    # numba code does this faster
    si = self.shared_info
    grid = si.classes['reader'].grid

    TT = np.take(grid['bc_transform'], n_cell, axis=0,)
    b = np.full((x.shape[0],3), np.nan, order='C')
    b[:,:2] = np.einsum('ijk,ik->ij', TT[:, :2], x[:, :2] - TT[:, 2], order='C')  # Einstein summation
    b[:,2] = 1. - b[:,:2].sum(axis=1)
    return b

#________ old versions

