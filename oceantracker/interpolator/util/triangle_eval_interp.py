import numpy as np
from oceantracker.util import  basic_util
from oceantracker.util.profiling_util import function_profiler
from oceantracker.util.numba_util import njitOT, njitOTparallel
import numba as nb


@njitOTparallel
def time_independent_2D_scalar_field(F_out, F_data, triangles, n_cell, bc_coords, active):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time independent  2D scalar fields , eg water-depth
    F = F_data[0, :, 0, 0]
    for nn in nb.prange(active.size):
        n = active[nn]
        # loop over each node in triangle
        F_out[n] = 0.  # zero out for summing
        n_nodes = triangles[n_cell[n], :]
        for m in range(3):
            F_out[n] += bc_coords[n, m] * F[n_nodes[m]]

@njitOTparallel
def time_independent_2D_vector_field(F_out, F_data, triangles, n_cell, bc_coords, active):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time independent  2D fields, eg water_depth
    # loop over active particles and vector components
    # slighly faster to loop over fixed # components

    # scalar, eg water-depth
    F = F_data[0, :, 0, :]
    for nn in nb.prange(active.size):
        n = active[nn]
        # loop over each node in triangle
        for c in range(2): F_out[n,c] = 0.  # zero out for summing

        n_nodes = triangles[n_cell[n], :]
        for m in range(3):
            node = n_nodes[m]
            for c in range(2):
                F_out[n, c] += bc_coords[n, m] * F[node, c]


@njitOTparallel
def time_dependent_2D_scalar_field(n_buffer, fractional_time_steps, F_out, F_data, triangles, n_cell, bc_coords, active):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time dependent  fields from two time slices in hindcast
    n_comp = F_data.shape[3]  # time step of data is always [node,z,comp] even in 2D
    F1 = F_data[n_buffer[0], :, 0, 0]
    F2 = F_data[n_buffer[1], :, 0, 0]

    # loop over active particles and vector components
    for nn in nb.prange(active.size):
        n = active[nn]
        # loop over isActive particles and vector components
        F_out[n] = 0. # zero out for summing
        n_nodes = triangles[n_cell[n], :]
        bc = bc_coords[n, :]
        # loop over each node in triangle
        for m in range(3):
            # loop over vector components
            F_out[n] += bc[m] * (fractional_time_steps[0] * F1[n_nodes[m]]
                               + fractional_time_steps[1] * F2[n_nodes[m]])

@njitOTparallel
def time_dependent_2D_vector_field(n_buffer, fractional_time_steps, F_out, F_data, triangles, n_cell, bc_coords, active):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time dependent  fields from two time slices in hindcast

    F1 = F_data[n_buffer[0], :, 0, :]
    F2 = F_data[n_buffer[1], :, 0, :]

    # loop over active particles and vector components
    for nn in nb.prange(active.size):
        n = active[nn]
        # loop over isActive particles and vector components
        for i in range(2): F_out[n, i] = 0. # zero out for summing
        n_nodes = triangles[n_cell[n], :]
        bc = bc_coords[n, :]
        # loop over each node in triangle
        for m in range(3):
            # loop over vector components
            for c in range(2):
                F_out[n, c] += bc[m] * (fractional_time_steps[0] * F1[n_nodes[m], c]
                                   + fractional_time_steps[1] * F2[n_nodes[m], c])


# do 3D interp evaluation
@njitOTparallel
def time_dependent_3D_scalar_field_data_in_all_layers(n_buffer, fractional_time_steps, F_data,
                                                      triangles,
                                                      n_cell, bc_coords, nz_cell, z_fraction,
                                                      F_out, active):
    #  time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles
    # create views to remove redundant dim at current and next time step
    F1 = F_data[n_buffer[0], :, :, 0]
    F2 = F_data[n_buffer[1], :, :, 0]

    # loop over active particles and vector components
    for nn in nb.prange(active.size):
        n = active[nn]

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
            F_out[n] += bc_coords[n, m] * temp


@njitOTparallel
def time_dependent_3D_vector_field_data_in_all_layers(n_buffer, fractional_time_steps, F_data,
                                                      triangles,
                                                      n_cell, bc_coords, nz_cell, z_fraction,
                                                      F_out, active):
    #  time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles

    # create views to remove redundant dim at current and next time step, improves speed?
    F1 = F_data[n_buffer[0], :, :, :]
    F2 = F_data[n_buffer[1], :, :, :]
    frac0, frac1 = fractional_time_steps[0],fractional_time_steps[1]

    # loop over active particles and vector components
    for nn in nb.prange(active.size):
        n = active[nn]
        zf2 = z_fraction[n]
        zf1 = 1. - zf2
        nz = nz_cell[n]

        # loop over each vertex in triangle
        for c in range(3): F_out[n, c] = 0. # zero out for summing

        for m in range(3):
            # loop vertex of tri
            node = triangles[n_cell[n], m]
            for c in range(3):
                # add contributions from layer above and below particle, for each spatial component at two time steps
                # slightly faster with temp variable, as allows more LLVM optimisations?
                temp  = (F1[node, nz, c] * zf1 + F1[node, nz + 1, c] * zf2)*frac0
                temp += (F2[node, nz, c] * zf1 + F2[node, nz + 1, c] * zf2)*frac1 # second time step
                F_out[n, c] += bc_coords[n, m] * temp

@njitOTparallel
def time_dependent_3D_scalar_field_ragged_bottom(n_buffer, fractional_time_steps, F_data,
                                            triangles, bottom_interface_index,
                                            n_cell, bc_coords, nz_cell, z_fraction,
                                            F_out, active):
    #  time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles
    #todo ncomp is always 1 for a scalar??
    n_comp = F_data.shape[3]  # time step of data is always [n_buffer, node,z,comp] even in 2D

    # create views of scalar data
    F1 = F_data[n_buffer[0], :, :, 0]
    F2 = F_data[n_buffer[1], :, :, 0]

    # loop over active particles and vector components
    for nn in nb.prange(active.size):
        n = active[nn]
        F_out[n] = 0. # zero out for summing
        zf = z_fraction[n]
        zf1 = 1. - zf
        nz = nz_cell[n]

        # loop over each vertex in triangle
        for m in range(3):
            n_node = triangles[n_cell[n], m]

            # for LSC grid need to get the highest node of nz or bottom at each triangle vertex
            nzb =  bottom_interface_index[n_node]  # bottom node at this vertex
            nz_below = max(nzb, nz)
            nz_above = max(nzb, nz + 1)
            # add contributions from layer above and below particle, for each spatial component at two time steps
            F_out[n] += bc_coords[n, m] * (F1[n_node, nz_below] * zf1 + F1[n_node, nz_above] * zf) * fractional_time_steps[0] \
                      + bc_coords[n, m] * (F2[n_node, nz_below] * zf1 + F2[n_node, nz_above] * zf) * fractional_time_steps[1]  # second time step


@njitOTparallel
def time_dependent_3D_vector_field_ragged_bottom(n_buffer, fractional_time_steps, F_data,
                                                 triangles, bottom_interface_index,
                                                 n_cell, bc_coords, nz_cell, z_fraction,
                                                 F_out, active):
    #  time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles
    # create views to remove redundant dim at current and next time step, improves speed?
    F1 = F_data[n_buffer[0], :, :, :]
    F2 = F_data[n_buffer[1], :, :, :]

    # loop over active particles and vector components
    for nn in nb.prange(active.size):
        n = active[nn]
        for i in range(3): F_out[n, i] = 0. # zero out for summing
        zf = z_fraction[n]
        zf1 = 1. - zf
        nz = nz_cell[n]

        # loop over each vertex in triangle
        for m in range(3):
            n_node = triangles[n_cell[n], m]

            # for LSC grid need to get the highest node of nz or bottom at each triangle vertex
            nzb =  bottom_interface_index[n_node]  # bottom node at this vertex
            nz_below = max(nzb, nz)
            nz_above = max(nzb, nz + 1)
            # loop over vector components
            for c in range(3):
                # add contributions from layer above and below particle, for each spatial component at two time steps
                F_out[n, c] +=    bc_coords[n, m] * (F1[n_node, nz_below, c] * zf1 + F1[n_node, nz_above, c] * zf)*fractional_time_steps[0]  \
                                + bc_coords[n, m] * (F2[n_node, nz_below, c] * zf1 + F2[n_node, nz_above, c] * zf)*fractional_time_steps[1]  # second time step
                pass
            pass
        pass
    pass

# below are development ideas
#_______________________________________________

# todo interpolate 3D fields at free surface or bottom
def interp_3Dfield_at_surfaces_time_indepenent(F_out, F_data, tri, n_cell, nz_bottom_cell, BCcord, active):
    basic_util.nopass('interp_3Dfield_at_surfaces_time_indepenent not yet implemented')