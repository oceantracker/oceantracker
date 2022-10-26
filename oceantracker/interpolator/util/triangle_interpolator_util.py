import numpy as np
from numba import njit
from oceantracker.util import  basic_util
from oceantracker.common_info_default_param_dict_templates import particle_info
# flags for bc walk status

too_manySteps   = -4
cord_nan = -9

status_outside_open_boundary = int(particle_info['status_flags']['outside_open_boundary'])
status_dead = int(particle_info['status_flags']['dead'])
status_bad_cord = int(particle_info['status_flags']['bad_cord'])
status_cell_search_failed = int(particle_info['status_flags']['cell_search_failed'])

# below need to be outside class as called by other numba code

#________ Barycentric triangle walk________
@njit
def BCwalk_with_move_backs_numba(xq, x_old, status, n_cell, BC, BCtransform, triNeighbours, current_dry_cell_index, block_dry_cells, tol, max_BC_walk_steps, has_open_boundary, active):
   # Barycentric walk across triangles to find cells

    n_total_walking_steps=0
    n_max_steps=0
    bc = np.full((3,), 0.)

    # loop over active particles in place
    for n in active:

        n_tri =n_cell[n]  # starting triangle
        # do BC walk
        n_steps=0
        if np.any(~np.isfinite(xq[n,:])):
            if np.all(np.isfinite(x_old[n,:])):
                for i in range(2) : xq[n,i] = x_old[n, i]
            else:
                status[n] = status_bad_cord
                continue

        while n_steps < max_BC_walk_steps:

            n_min, n_max= _get_single_BC_cord_numba(xq[n, :2], BCtransform[n_tri, :, :], bc)

            if bc[n_max] < 1. + tol and bc[n_min] > -tol:
                # are now inside triangle, leave particle status as is
                # found cell in time, and interior point, so update cell
                n_cell[n] = n_tri
                for i in range(3): BC[n, i] = bc[i]
                break

            n_steps +=1
            # move to neighbour triangle at face with smallest bc then test bc cord again
            n_tri = triNeighbours[n_tri,n_min]  # n_min is the face num in  tri to move across

            if n_tri < 0:
                # if no new adjacent triangle, then are trying to exit domain at a boundary triangle,
                # keep n_cell, bc  unchanged
                if has_open_boundary and n_tri == -2: # outside domain
                    # leave bc, cell, location  unchanged as outside
                    status[n] = status_outside_open_boundary
                    break
                else: # n_tri == -1 outside domain and any future -ve face types, attempt to move back to last good position
                    # solid boundary, so just move back
                    if np.all(np.isfinite(x_old[n, :])):
                        for i in range(2): xq[n, i] = x_old[n, i]
                    else:
                        status[n] = status_bad_cord
                    break

            # check for dry cell
            if block_dry_cells:
                if  current_dry_cell_index[n_tri] > 128:
                    # treats dry cell like a lateral boundary
                    # move back and keep triangle the same
                    if np.all(np.isfinite(x_old[n, :])):
                        for i in range(2): xq[n, i] = x_old[n, i]
                    else:
                        status[n] = status_bad_cord
                    break

        # not found in given number of search steps
        if n_steps >= max_BC_walk_steps: # dont update cell
            status[n] = status_cell_search_failed

        # step count stats
        n_total_walking_steps += n_steps
        # record max number of steps
        if n_steps> n_max_steps:
            n_max_steps = n_steps

    return n_total_walking_steps, n_max_steps  # return total number of steps for calculating step stats

@njit(inline='always')
def _get_single_BC_cord_numba(x, BCtransform, bc):
    # get BC cord of x for one triangle from DT transform matrix inverse, see scipy.spatial.Delaunay
    # also return index smallest BC for walk and largest
    # returns n_min the index of smallest bc used to choose next triangle
    # bc is (3,) preallocated working scale, used to return BC's

    n_min = 0
    n_max = 0

    # do (2x2) matrix multiplication of  bc[:2]=BCtransform[:2,:2]*(x-transform[:,2]
    #for i in range(2): bc[i] = 0.
    for i in range(2):
        #for j in range(2):
        #  bc[i] +=  BCtransform[i,j]*(x[j]-BCtransform[2,j])
        # replace loop with faster explicit adds, as no need to zero bc[:] above
        bc[i]  = BCtransform[i, 0] * (x[0] - BCtransform[2, 0])
        bc[i] += BCtransform[i, 1] * (x[1] - BCtransform[2, 1])

       # record smallest BC of first two
        if bc[i] < bc[n_min]: n_min = i
        if bc[i] > bc[n_max]: n_max = i

    bc[2]= 1.0 - bc[0] - bc[1]

    # see if last one is smaller, or largest
    if bc[2] < bc[n_min]: n_min = 2
    if bc[2] > bc[n_max]: n_max = 2
    return n_min,n_max

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

    ndim = 2 # onluy works on 2D triangles
    nsimplex = simplices.shape[0]

    T = np.empty((ndim, ndim), dtype=np.double)
    Tinvs = np.zeros((nsimplex, ndim + 1, ndim), dtype=np.double)

    for isimplex in range(nsimplex):
        for i in range(ndim):
            Tinvs[isimplex, ndim, i] = points[simplices[isimplex, ndim], i] # puts cords of last point as extra column, ie r_n vector
            for j in range(ndim):
                T[i, j] = (points[simplices[isimplex, j], i] - Tinvs[isimplex, ndim, i])
            Tinvs[isimplex, i, i] = np.nan

        # form inverse of 2 by 2, https://mathworld.wolfram.com/MatrixInverse.html
        # compute matrix determinate of 2 by 2
        det =  T[0, 0]*T[1, 1]-T[0, 1]*T[1, 0]

        # inverse  matrix term by term
        Tinvs[isimplex, 0, 0] =  T[1, 1] / det
        Tinvs[isimplex, 1, 1] =  T[0, 0] / det
        Tinvs[isimplex, 0, 1] = -T[0, 1] / det
        Tinvs[isimplex, 1, 0] = -T[1, 0] / det

    return Tinvs

@njit
def get_depth_cell_time_varying_Slayer_or_LSCgrid(zq, nb, step_dt_fraction, z_level_at_nodes, tri, n_cell,
                                                 nz_with_bottom, BCcord, status,
                                                 part_status_onBottom, part_status_Active, part_stranded_by_tide,
                                                 nz_nodes_particle, z_fraction_nodes_particle, active,
                                                 vertical_search_steps_histogram):
    # find the zlayer for each node of cell containing each particleand at two time slices of hindcast  between nz_bottom and number of z levels
    # nz_with_bottom is lowest cell in grid, is 0 for slayer vertical grids, but may be > 0 for LSC grids
    # must be at least two layer  ie, nz_bottom >=1 and zlevel with at least two layers in last dim
    # nz_with_bottom must be time independent

    tf2 = 1. - step_dt_fraction
    z_tol =0.005
    z_tol2 = z_tol /2.
    count_maybe_below_bottom = 0
    count_maybe_above_surface = 0
    top_zlevel = z_level_at_nodes.shape[2] - 2

    for n_part in active:  # loop over active particles
        nodes = tri[n_cell[n_part], :]  # nodes for the particle's cell

        # preserve status if stranded by tide
        if status[n_part] == part_stranded_by_tide:
            z_fraction_nodes_particle[n_part, :, :] = 0.
            nz_nodes_particle[n_part, :, :] = nz_with_bottom[nodes]
            continue

        # make any already on bottom active, may be flagged on bottom if found on bottom, below
        if status[n_part] == part_status_onBottom:   status[n_part] = part_status_Active

        maybe_below_bottom = False
        maybe_above_surface= False
        n_vertical_searches = 0

        for nt_step in range(2):

            for m in range(3):  # loop over each node of containing triangle
                # short cuts
                node_m = nodes[m]
                nz_bottom_node = nz_with_bottom[node_m]
                zlevels = z_level_at_nodes[nb + nt_step, node_m ,:]  # view of zlevel profile at this node of cell containing this particle

                # for zq  guess its depth layer nz for this node and hindcast time slice
                if nt_step ==0:
                    nz= nz_nodes_particle[n_part, 0, 0]  # guess is current nz for first node, but once found is  guess for nodes 2 and 3
                else:
                    nz = nz_nodes_particle[n_part, 0, m] # for second slice use nz from first time slice as guess

                nz = min(max(nz, nz_bottom_node), top_zlevel) # clip nz into bounds
                nz0 = nz # starying nz for histogram data

                # clip cells out of bounds
                if zq[n_part] < zlevels[nz_bottom_node] + z_tol:
                    nz = nz_bottom_node  # clip this node to nz_bottom_cell
                    zfrac = 0.
                    maybe_below_bottom = True

                elif zq[n_part] > zlevels[-1] - z_tol:
                    nz = top_zlevel  # clip into top cell
                    zfrac = 1.
                    maybe_above_surface = True

                elif zq[n_part] >= zlevels[nz]:
                    # search upwards
                    while zq[n_part] > zlevels[nz + 1] and nz < top_zlevel :
                        nz += 1
                        n_vertical_searches += 1

                    if abs((zlevels[nz + 1] - zlevels[nz])) < z_tol:
                        zfrac = 0.0
                    else:
                        zfrac = (zq[n_part] - zlevels[nz]) / (zlevels[nz + 1] - zlevels[nz])

                elif zq[n_part] < zlevels[nz]:
                    # search downwards
                    while zlevels[nz] > zq[n_part] and nz > nz_bottom_node:
                        nz -= 1
                        n_vertical_searches += 1
                    if abs((zlevels[nz + 1] - zlevels[nz])) < z_tol:
                        zfrac = 0.0
                    else:
                        zfrac = (zq[n_part] - zlevels[nz]) / (zlevels[nz + 1] - zlevels[nz])

                else:
                    # missing case zq is nan??
                    # todo need better solution for non finite xq/zq?
                    nz = nz_bottom_node
                    zfrac = 0.0


                # record cell and fraction from search
                # NOTE: ensured nz OK by having used debugger to see if any z frac > 1 or < 0
                z_fraction_nodes_particle[n_part, nt_step, m] = zfrac
                nz_nodes_particle[n_part, nt_step, m] = nz

        # record number of vertical search steps made for this particle
        vertical_search_steps_histogram[abs(nz-nz0)] += n_vertical_searches

        # check if this zq[n] is out of bounds and clip if needed
        if maybe_below_bottom:
            #  zq[n] is below one of the three nodes, so maybe below bottom,
            #  check if below bottom and clip zq[n] if needed
            # get z_bottom at particle location from interpolation using Barycentric  cords to interpolate
            z_particle_bottom = 0.
            for nn in range(3):
                node_nn = nodes[nn]
                z_particle_bottom += z_level_at_nodes[nb    , node_nn, nz_with_bottom[node_nn]] * BCcord[n_part, nn] * tf2
                z_particle_bottom += z_level_at_nodes[nb + 1, node_nn, nz_with_bottom[node_nn]] * BCcord[n_part, nn] * step_dt_fraction

            count_maybe_below_bottom += 1
            if zq[n_part] <= z_particle_bottom + z_tol:
                zq[n_part] = z_particle_bottom + z_tol2
                status[n_part] = part_status_onBottom


        if maybe_above_surface:
            #  zq[n] is above one of the three nodes, so maybe above free surface
            #  check if below bottom and clip zq[n] if needed
            # get z_surface at particle location from interpolation using Barycentric  cords to interpolate
            z_particle_freeSurface = 0.
            for nn in range(3):
                node_nn = nodes[nn]
                z_particle_freeSurface += z_level_at_nodes[nb    , node_nn, -1] * BCcord[n_part, nn] * tf2
                z_particle_freeSurface += z_level_at_nodes[nb + 1, node_nn, -1] * BCcord[n_part, nn] * step_dt_fraction

            count_maybe_above_surface += 1
            if zq[n_part] >= z_particle_freeSurface - z_tol:
                zq[n_part] = z_particle_freeSurface - z_tol2

    return count_maybe_below_bottom, count_maybe_above_surface

@njit
def find_depth_cell_at_a_node( zq, zlevels,nz_bottom, nz,  z_tol, z_fraction_node, maybe_below_bottom, maybe_above_surface, n_vertical_searches ):
    #todo not used?

    # find depth level just below zq and fraction of layer above this,  within  zlevels_at_node, using guess nz as a start
    # answers returned by reference
    # clip cells out of bounds
    # NOTE: this reprodues the core of the above, but for use in making custom fields, but to use it above takes 50% longer due to function call overhead
    top_zlevel = zlevels.shape[0] - 2

    if zq < zlevels[nz_bottom] + z_tol:
        nz = nz_bottom  # clip this node to nz_bottom_cell
        z_fraction_node = 0.
        maybe_below_bottom = True

    elif zq > zlevels[-1] - z_tol:
        nz = top_zlevel- 2  # clip into top cell
        z_fraction_node = 1.
        maybe_above_surface = True

    elif zq >= zlevels[nz]:
        # search upwards
        while zq > zlevels[nz + 1] and nz < top_zlevel:
            nz += 1
            n_vertical_searches += 1
        z_fraction_node = (zq - zlevels[nz]) / (zlevels[nz + 1] - zlevels[nz])

    elif zq < zlevels[nz]:
        # search downwards
        while zlevels[nz] > zq and nz > nz_bottom:
            nz -= 1
            n_vertical_searches += 1
        z_fraction_node = (zq- zlevels[nz]) / (zlevels[nz + 1] - zlevels[nz])

    else:
        # missing case zq in nan??
        # todo need better solution for non finite xq/zq
        nz = nz_bottom
        z_fraction_node = 0.

    return maybe_below_bottom, maybe_above_surface, n_vertical_searches


