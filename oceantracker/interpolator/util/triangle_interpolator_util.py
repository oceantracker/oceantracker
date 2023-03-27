import numpy as np
from numba import njit,typeof, float64, int32, float32, int8, int64, boolean, uint8
from oceantracker.util import basic_util
from oceantracker.common_info_default_param_dict_templates import particle_info

# flags for bc walk status


walk_stats = np.dtype([('particles_located', np.int64), ('total_steps', np.int64), ('longest_walk', np.int32), ('failed_walks', np.int32), ('histogram', np.int64, (30,))])

# globals
status_moving = int(particle_info['status_flags']['moving'])
status_on_bottom = int(particle_info['status_flags']['on_bottom'])
status_stranded_by_tide = int(particle_info['status_flags']['stranded_by_tide'])

status_outside_open_boundary = int(particle_info['status_flags']['outside_open_boundary'])
status_dead = int(particle_info['status_flags']['dead'])
status_bad_cord = int(particle_info['status_flags']['bad_cord'])
status_cell_search_failed = int(particle_info['status_flags']['cell_search_failed'])


@njit(typeof((1,1))(float64[:], float64[:, :], float64[:]))
def _get_single_BC_cord_numba(x, BCtransform, bc):
    # get BC cord of x for one triangle from DT transform matrix inverse, see scipy.spatial.Delaunay
    # also return index smallest BC for walk and largest
    # returns n_min the index of smallest bc used to choose next triangle
    # bc is (3,) preallocated working scale, used to return BC's

    n_min = 0
    n_max = 0

    # do (2x2) matrix multiplication of  bc[:2]=BCtransform[:2,:2]*(x-transform[:,2]
    # for i in range(2): bc[i] = 0.
    for i in range(2):
        # for j in range(2):
        #  bc[i] +=  BCtransform[i,j]*(x[j]-BCtransform[2,j])
        # replace loop with faster explicit adds, as no need to zero bc[:] above
        bc[i] = BCtransform[i, 0] * (x[0] - BCtransform[2, 0])
        bc[i] += BCtransform[i, 1] * (x[1] - BCtransform[2, 1])

        # record smallest BC of first two
        if bc[i] < bc[n_min]: n_min = i
        if bc[i] > bc[n_max]: n_max = i

    bc[2] = 1.0 - bc[0] - bc[1]

    # see if last one is smaller, or largest
    if bc[2] < bc[n_min]: n_min = 2
    if bc[2] > bc[n_max]: n_max = 2
    return n_min, n_max

# ________ Barycentric triangle walk________
#@profile
@njit
def BCwalk_with_move_backs_numba2D(xq, x_old, status, BC, BCtransform, triNeighbours, current_dry_cell_index, block_dry_cells,
                                   tol, max_BC_walk_steps, has_open_boundary, active, walk_stats, n_cell):
    # Barycentric walk across triangles to find cells

    bc = np.full((3,), 0.)
    n_dim = xq.shape[1]
    n_min_max= np.full((2,),-1,np.int8)
    # loop over active particles in place
    for n in active:

        n_tri = n_cell[n]  # starting triangle
        # do BC walk
        n_steps = 0
        for nn in range(n_dim):
            if xq[n, nn] == np.nan:
                # if any is nan copy all and move on
                for i in range(n_dim): xq[n, i] = x_old[n, i]
                break

        move_back = False

        while n_steps < max_BC_walk_steps:
            # update barcentric cords of xq
            n_min, n_max =_get_single_BC_cord_numba(xq[n, :2], BCtransform[n_tri, :, :], bc)

            if bc[n_max] < 1. + tol and tol and bc[n_min] > -tol:
                # are now inside triangle, leave particle status as is
                break

            n_steps += 1
            # move to neighbour triangle at face with smallest bc then test bc cord again
            next_tri = triNeighbours[n_tri, n_min]  # n_min is the face num in  tri to move across

            if next_tri < 0:
                # if no new adjacent triangle, then are trying to exit domain at a boundary triangle,
                # keep n_cell, bc  unchanged
                if has_open_boundary and next_tri == -2:  # outside domain
                    # leave x, bc, cell, location  unchanged as outside
                    status[n] = status_outside_open_boundary
                    break
                else:  # n_tri == -1 outside domain and any future
                    # solid boundary, so just move back
                    move_back = True
                    break

            # check for dry cell
            if block_dry_cells:  # is faster split into 2 ifs, not sure why
                if current_dry_cell_index[next_tri] > 128:
                    # treats dry cell like a lateral boundary,  move back and keep triangle the same
                    move_back = True
                    break

            n_tri = next_tri

        # not found in given number of search steps
        if n_steps >= max_BC_walk_steps:  # dont update cell
            status[n] = status_cell_search_failed
            walk_stats['failed_walks'] += 1
            move_back = True

        if move_back:
            # move back dont update
            for i in range(xq.shape[1]): xq[n, i] = x_old[n, i]
        else:
            # update cell anc BC for new triangle
            n_cell[n] = n_tri
            for i in range(3): BC[n, i] = bc[i]

        # step count stats
        if  False:
            walk_stats['particles_located'] += 1
            walk_stats['total_steps'] += n_steps

            # record max number of steps
            if n_steps > walk_stats['longest_walk']:
                walk_stats['longest_walk'] = n_steps + 1

            walk_stats['histogram'][min(n_steps, walk_stats['histogram'].shape[0] - 1)] += 1


@njit
def get_BC_cords_numba(x, n_cells, BCtransform, bc):
    # get BC cords of set of points x inside given cells and return in bc
    for n in range(x.shape[0]):
        _get_single_BC_cord_numba(x[n, :], BCtransform[n_cells[n], :, :], bc[n, :])


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


#@profile
@njit
def get_depth_cell_time_varying_Slayer_or_LSCgrid(zq, nb, step_dt_fraction, z_level_at_nodes, tri, n_cell,
                                                  nz_with_bottom, BCcord, status,
                                                  nz_cell, nz_nodes, z_fraction,
                                                  z_fraction_bottom_layer, is_in_bottom_layer,
                                                  z0, active, walk_stats):
    # find the zlayer for each node of cell containing each particl eand at two time slices of hindcast  between nz_bottom and number of z levels
    # LSC grid means must track vertical nodes for each particle
    # nz_with_bottom is lowest cell in grid, is 0 for slayer vertical grids, but may be > 0 for LSC grids
    # nz_with_bottom must be time independent

    tf2 = 1. - step_dt_fraction

    top_nz_cell = z_level_at_nodes.shape[2] - 2
    top_zlevel3 = np.full((3,), top_nz_cell, dtype=np.int32)

    for n in active:  # loop over active particles
        nodes = tri[n_cell[n], :]  # nodes for the particle's cell
        bottom_nz_nodes = nz_with_bottom[nodes]
        nz_below = nz_nodes[n, 0, :]
        nz_above = nz_nodes[n, 1, :]

        n_vertical_steps = 0

        # current cell number
        bottom_nz_cell = np.min(bottom_nz_nodes)  # cell at bottom

        # preserve status if stranded by tide
        if status[n] == status_stranded_by_tide:
            nz_cell[n] = bottom_nz_cell
            # update nodes above and below
            z_below = _eval_z_at_nz_cell(nb, bottom_nz_cell, z_level_at_nodes, bottom_nz_nodes, BCcord[n, :], step_dt_fraction, tf2, nodes, nz_below)
            z_above = _eval_z_at_nz_cell(nb, bottom_nz_cell + 1, z_level_at_nodes, bottom_nz_nodes, BCcord[n, :], step_dt_fraction, tf2, nodes, nz_above)
            zq[n] = z_below
            z_fraction[n] = 0.0
            continue

        # make any already on bottom active, may be flagged on bottom if found on bottom, below
        if status[n] == status_on_bottom:   status[n] = status_moving

        # find zlevel above and below  current vertical cell
        z_below = _eval_z_at_nz_cell(nb, nz_cell[n], z_level_at_nodes, bottom_nz_nodes, BCcord[n, :], step_dt_fraction, tf2, nodes, nz_below)
        z_above = _eval_z_at_nz_cell(nb, nz_cell[n] + 1, z_level_at_nodes, bottom_nz_nodes, BCcord[n, :], step_dt_fraction, tf2, nodes, nz_above)

        if zq[n] >= z_below:
            # search upwards, do nothing if z_above > zq[n] > z_below, ie current nodes are correct
            if zq[n] > z_above:
                while nz_cell[n] < top_nz_cell:
                    n_vertical_steps += 1
                    nz_cell[n] += 1
                    z_below = z_above
                    nz_below[:] = nz_above.copy()
                    z_above = _eval_z_at_nz_cell(nb, nz_cell[n], z_level_at_nodes, bottom_nz_nodes, BCcord[n, :], step_dt_fraction, tf2, nodes, nz_above)
                    if zq[n] <= z_above: break
        else:
            # search downwards
            while nz_cell[n] > bottom_nz_cell:
                n_vertical_steps += 1
                nz_cell[n] -= 1
                z_above = z_below
                nz_above[:] = nz_below.copy()
                z_below = _eval_z_at_nz_cell(nb, nz_cell[n], z_level_at_nodes, bottom_nz_nodes, BCcord[n, :], step_dt_fraction, tf2, nodes, nz_below)
                if zq[n] >= z_below: break  # found cell

        # clip zq to be in bounds before calc. z_fraction
        z_bot = _eval_z_at_nz_nodes(nb, z_level_at_nodes, BCcord[n, :], step_dt_fraction, tf2, nodes, bottom_nz_nodes)
        if zq[n] < z_bot + z0:
            zq[n] = z_bot
            status[n] = status_on_bottom
        else:
            # clip to surface only if not below bottom
            z_surf = _eval_z_at_nz_nodes(nb, z_level_at_nodes, BCcord[n, :], step_dt_fraction, tf2, nodes, top_zlevel3)
            if zq[n] >= z_surf:
                zq[n] = z_surf

        # get z fraction
        dz = z_above - z_below
        if dz < z0:
            z_fraction[n] = 0.0
        else:
            z_fraction[n] = (zq[n] - z_below) / dz

        if nz_cell[n] == bottom_nz_cell:
            is_in_bottom_layer[n] = 1
            if dz < z0:
                z_fraction_bottom_layer[n] = 0.0
            else:
                # adjust z fraction so that linear interp acts like log layer
                z0p = z0 / dz
                z_fraction_bottom_layer[n] = (np.log(z_fraction[n] + z0p) - np.log(z0p)) / (np.log(1. + z0p) - np.log(z0p))

        # record number of vertical search steps made for this particle
        # step count stats, tidal stranded particles are not counted
        walk_stats['particles_located'] += 1
        walk_stats['total_steps'] += n_vertical_steps
        # record max number of steps
        if n_vertical_steps > walk_stats['longest_walk']:
            walk_stats['longest_walk'] = n_vertical_steps + 1

        walk_stats['histogram'][min(n_vertical_steps, walk_stats['histogram'].shape[0] - 1)] += 1


@njit([(int64, float32[:, :, :], float64[:], float64, float64, int32[:], int32[:])])
def _eval_z_at_nz_nodes(nb, z_level_at_nodes, BCcord, tf, tf2, nodes, nz_nodes):
    # eval a at given zlevel given nodes
    z = 0.
    for m in range(3):
        node_nn = nodes[m]
        z += z_level_at_nodes[nb, node_nn, nz_nodes[m]] * BCcord[m] * tf2 \
             + z_level_at_nodes[nb + 1, node_nn, nz_nodes[m]] * BCcord[m] * tf
    return z


@njit([(int64, int32, float32[:, :, :], int32[:], float64[:], float64, float64, int32[:], int32[:])])
def _eval_z_at_nz_cell(nb, nz_cell, z_level_at_nodes, bottom_nodes, BCcord, tf, tf2, nodes, nz_nodes):
    # eval zlevel at particle location and depth cell, return z and nodes required for evaluation
    z = 0.
    for m in range(3):
        nz_nodes[m] = max(nz_cell, bottom_nodes[m])
        z += z_level_at_nodes[nb, nodes[m], nz_nodes[m]] * BCcord[m] * tf2 \
             + z_level_at_nodes[nb + 1, nodes[m], nz_nodes[m]] * BCcord[m] * tf
    return z


#________ old versions
