import numpy as np
from numba import njit, float64, int32, float32, int8, int64, boolean, uint8
from oceantracker.util import  basic_util
from oceantracker.util.profiling_util import function_profiler
from oceantracker.util.numba_util import njitOT

@njitOT
def time_independent_2Dfield_scalar(F_out, F_data, triangles, n_cell, bc_cords,  active):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time independent  2D fields, eg water_depth
    # scalar, eg water-depth
    # slighly faster to loop over fixed # components
    F = F_data[0, :, 0, 0]
    for n in active:
        # loop over each node in triangle
        F_out[n] = 0.  # zero out for summing
        n_nodes = triangles[n_cell[n], :]
        for m in range(3):
            F_out[n] += bc_cords[n, m] * F[n_nodes[m]]

@njitOT
def time_independent_2Dfield_vector(F_out, F_data, triangles, n_cell, bc_cords,  active):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time independent  2D fields, eg water_depth
    # loop over active particles and vector components
    # slighly faster to loop over fixed # components

    # scalar, eg water-depth
    F = F_data[0, :, 0, :]
    for n in active:
        # loop over each node in triangle
        F_out[n] = 0.  # zero out for summing
        n_nodes = triangles[n_cell[n], :]
        for m in range(3):
            F_out[n] += bc_cords[n, m] * F[n_nodes[m]]


@njitOT
def time_dependent_2Dfield_scalar(nb, fractional_time_steps, F_out, F_data, triangles, n_cell, bc_cords,  active):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time dependent  fields from two time slices in hindcast
    n_comp = F_data.shape[3]  # time step of data is always [node,z,comp] even in 2D
    F1 = F_data[nb[0], :, 0, 0]
    F2 = F_data[nb[1], :, 0, 0]

    # loop over active particles and vector components
    for n in active:
        # loop over isActive particles and vector components
        F_out[n] = 0. # zero out for summing
        n_nodes = triangles[n_cell[n], :]
        bc = bc_cords[n, :]
        # loop over each node in triangle
        for m in range(3):
            # loop over vector components
            F_out[n] += bc[m] * (fractional_time_steps[0] * F1[n_nodes[m]]
                                   + fractional_time_steps[1] * F2[n_nodes[m]])

@njitOT
def time_dependent_2Dfield_vector(nb, fractional_time_steps, F_out, F_data, triangles, n_cell, bc_cords,  active):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time dependent  fields from two time slices in hindcast
    n_comp = F_data.shape[3]  # time step of data is always [node,z,comp] even in 2D
    F1 = F_data[nb[0], :, 0, :]
    F2 = F_data[nb[1], :, 0, :]

    # loop over active particles and vector components
    for n in active:
        # loop over isActive particles and vector components
        for i in range(2): F_out[n, i] = 0. # zero out for summing
        n_nodes = triangles[n_cell[n], :]
        bc = bc_cords[n, :]
        # loop over each node in triangle
        for m in range(3):
            # loop over vector components
            for c in range(2):
                F_out[n, c] += bc[m] * (fractional_time_steps[0] * F1[n_nodes[m], c]
                                   + fractional_time_steps[1] * F2[n_nodes[m], c])


# do 3D interp evaluation
@njitOT
def time_dependent_3Dfield_scalar_sigma_grid(nb,fractional_time_steps, F_data,
                            triangles,
                            n_cell, bc_cords, nz_cell, z_fraction,
                            F_out, active):
    #  time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles
    # create views to remove redundant dim at current and next time step
    F1 = F_data[nb[0], :, :, 0]
    F2 = F_data[nb[1], :, :, 0]

    # loop over active particles and vector components
    for n in active:

        zf2 = z_fraction[n]
        zf1 = 1. - zf2
        nz = nz_cell[n]

        # loop over each vertex in triangle
        F_out[n] = 0.
        n_nodes = triangles[n_cell[n], :]
        for m in range(3):
            # add contributions from layer above and below particle, at two time steps
            temp  = (F1[n_nodes[m], nz] * zf1 + F1[n_nodes[m], nz + 1] * zf2) * fractional_time_steps[0]
            temp += (F2[n_nodes[m], nz] * zf1 + F2[n_nodes[m], nz + 1] * zf2) * fractional_time_steps[1]# second time step
            F_out[n] += bc_cords[n, m] * temp

@njitOT
def time_dependent_3Dfield_vector_sigma_grid(nb,fractional_time_steps, F_data,
                            triangles,
                            n_cell, bc_cords, nz_cell, z_fraction,
                            F_out, active):
    #  time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles

    # create views to remove redundant dim at current and next time step, improves speed?
    F1 = F_data[nb[0], :, :, :]
    F2 = F_data[nb[1], :, :, :]

    # loop over active particles and vector components
    for n in active:

        zf2 = z_fraction[n]
        zf1 = 1. - zf2
        nz = nz_cell[n]

        # loop over each vertex in triangle
        for i in range(3): F_out[n, i] = 0. # zero out for summing
        n_nodes = triangles[n_cell[n], :]
        for m in range(3):
            # loop over vector components
            for c in range(3):
                # add contributions from layer above and below particle, for each spatial component at two time steps
                # slightly faster with temp variable, as allows more LLVM optimisations?
                temp  = (F1[n_nodes[m], nz, c] * zf1 + F1[n_nodes[m], nz + 1, c] * zf2)*fractional_time_steps[0]
                temp += (F2[n_nodes[m], nz, c] * zf1 + F2[n_nodes[m], nz + 1, c] * zf2)*fractional_time_steps[1]
                F_out[n, c] += bc_cords[n, m] * temp
                #F_out[n, c] += bc_cords[n, m] * (F1[n_nodes[m], nz, c] * zf1 + F1[n_nodes[m], nz + 1, c] * zf2)*fractional_time_steps[0]  \
                #            +  bc_cords[n, m] * (F2[n_nodes[m], nz, c] * zf1 + F2[n_nodes[m], nz + 1, c] * zf2)*fractional_time_steps[1]  # second time step


#@function_profiler(__name__)
@njitOT
def time_dependent_3Dfield_LSC_grid(nb ,fractional_time_steps, F_data,
                            triangles,bottom_cell_index,
                            n_cell, bc_cords, nz_cell, z_fraction,
                            F_out, active):
    #  time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles

    n_comp = F_data.shape[3]  # time step of data is always [nb, node,z,comp] even in 2D

    # create views to remove redundant dim at current and next time step, improves speed?
    F1 = F_data[nb[0], :, :, :]
    F2 = F_data[nb[1], :, :, :]

    # loop over active particles and vector components
    for n in active:
        for i in range(n_comp): F_out[n, i] = 0. # zero out for summing
        zf = z_fraction[n]
        zf1 = 1. - zf
        nz = nz_cell[n]

        # loop over each vertex in triangle
        for m in range(3):
            n_node = triangles[n_cell[n], m]

            # for LSC grid need to get highest node of nz or bottom at each triangle vertex
            nzb =  bottom_cell_index[n_node]  # bottom node at this vertex
            nz_below = max(nzb, nz    )
            nz_above = max(nzb, nz + 1)
            # loop over vector components
            for c in range(n_comp):
                # add contributions from layer above and below particle, for each spatial component at two time steps
                F_out[n, c] +=     bc_cords[n, m] * (F1[n_node, nz_below, c] * zf1 + F1[n_node, nz_above, c] * zf)*fractional_time_steps[0]  \
                                +  bc_cords[n, m] * (F2[n_node, nz_below, c] * zf1 + F2[n_node, nz_above, c] * zf)*fractional_time_steps[1]  # second time step

@njitOT
def update_dry_cell_index(is_dry_cell,dry_cell_index, current_buffer_steps,fractional_time_steps):
    # update 0-255 dry cell index, used to determine if cell dry at this time
    # uses  reader buffer locations and time step fractions within step info structure
    # vals > 127 are dry, vals <= 127 are wet
    for n in range(dry_cell_index.size):
        val  = fractional_time_steps[0]*is_dry_cell[current_buffer_steps[0], n]
        val += fractional_time_steps[1]*is_dry_cell[current_buffer_steps[1], n]
        dry_cell_index[n]  = int(255.*val)

# below are development ideas
#_______________________________________________

# todo interpolate 3D fields at free surface or bottom
def interp_3Dfield_at_surfaces_time_indepenent(F_out, F_data, tri, n_cell, nz_bottom_cell, BCcord, active):
    basic_util.nopass('interp_3Dfield_at_surfaces_time_indepenent not yet implemented')