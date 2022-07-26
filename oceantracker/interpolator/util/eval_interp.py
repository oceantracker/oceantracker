import numpy as np
from numba import njit
from oceantracker.util import  basic_util


@njit
def time_independent_2Dfield(F_out, F_data, tri, n_cell, BCcord, active):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time independent  2D fields, eg water_depth
    F = F_data[0, :, 0, :]
    n_comp = F.shape[1]  # time step of data is always [node,z,comp] even in 2D
    # loop over active particles and vector components

    for n in active:
        # loop over each node in triangle
        for i in range(n_comp): F_out[n, i] = 0.  # zero out for summing

        for n_bc in range(3):
            n_node = tri[n_cell[n], n_bc]
            bc = BCcord[n, n_bc]
            # loop over vector components
            for c in range(n_comp):
                F_out[n, c] += bc * F[n_node, c]

@njit
def time_dependent_2Dfield(F_out, F_data, nb, step_dt_fraction, tri, n_cell, BCcord, active):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time dependent  fields from two time slices in hindcast

    n_comp = F_data.shape[3]  # time step of data is always [node,z,comp] even in 2D
    tf2 = 1. - step_dt_fraction
    F1 = F_data[nb  , :, 0, :]
    F2 = F_data[nb+1, :, 0, :]
    # loop over isActive particles and vector components
    for n in active:
        for i in range(n_comp): F_out[n, i] = 0. # zero out for summing
        # loop over each node in triangle
        for n_bc in range(3):
            n_node = tri[n_cell[n], n_bc]
            bc = BCcord[n, n_bc]
            # loop over vector components
            for c in range(n_comp):
                F_out[n, c] += bc * (tf2 * F1[ n_node, c] + step_dt_fraction * F2[n_node, c])

# do 3D interp evaluation
@njit
def time_independent_3Dfield(F_out, F_data, tri, n_cell, nz_node, z_fraction, BCcord, active):
    #  non-time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles
    # todo do not used yet?
    n_comp = F_data.shape[2]  # time step of data is always [node,z,comp] even in 2D
    F=  F_data[0, :, :, :]

    # loop over isActive particles and vector components
    for n in active:
        # loop over each node in triangle
        for i in range(n_comp): F_out[n, i] = 0. # zero out for summing

        # loop over each node in triangle
        for n_bc in range(3):
            n_node = tri[n_cell[n], n_bc]
            bc = BCcord[n, n_bc]

            nz = nz_node[n, n_bc]
            zf = z_fraction[n, n_bc]
            zf1 = 1. - zf
            # loop over vector components
            for c in range(n_comp):
                # add contributions from layer above and below particle, for each spatial component
                F_out[n, c] += bc * (F[n_node, nz, c] * zf1 + F[n_node, nz + 1, c] * zf)
@njit
def time_dependent_3Dfield(F_out, F_data, nb, step_dt_fraction, tri,  n_cell, nz_nodes, z_fraction, BCcord,  active):
    #  time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles

    n_comp = F_data.shape[3]  # time step of data is always [nb, node,z,comp] even in 2D

    # create views to remove redundant dim at current and next time step, improves speed?
    F1 = F_data[nb  , :, :, :]
    F2 = F_data[nb+1, :, :, :]

    dt1 = 1.0 - step_dt_fraction


    # loop over active particles and vector components
    for n in active:
        for i in range(n_comp): F_out[n, i] = 0. # zero out for summing
        zf = z_fraction[n]
        zf1 = 1. - zf

        nodes = tri[n_cell[n],:]

        nz_below = nz_nodes[n, 0, :]
        nz_above = nz_nodes[n, 1, :]

        # loop over each node in triangle
        for m in range(3):
            n_node = nodes[m]


            # loop over vector components
            for c in range(n_comp):
                # add contributions from layer above and below particle, for each spatial component at two time steps
                F_out[n, c] +=     BCcord[n, m] * (F1[n_node, nz_below[m], c] * zf1 + F1[n_node, nz_above[m], c] * zf)*dt1  \
                                +  BCcord[n, m] * (F2[n_node, nz_below[m], c] * zf1 + F2[n_node, nz_above[m], c] * zf)*step_dt_fraction  # second time step

@njit
def eval_water_velocity_3D(V_out, V_data, nb, step_dt_fraction, tri, n_cell,
                           nz_cell,nz_nodes, z_fraction, z_fraction_bottom_layer, is_in_bottom_layer, BCcord, z0, active):
    #  special case of interpolating water velocity with log layer in bottom cell, linear z interpolation at other depth cells

    n_comp = V_data.shape[3]  # time step of data is always [node,z,comp] even in 2D

    # create views to remove redundant dim at current and next time step, improves speed?
    v1,     v2       = V_data[nb  , :, :, :], V_data[nb + 1, :, :, :]

    dt1= 1.0-step_dt_fraction

    # loop over active particles and vector components
    for n in active:
        for i in range(n_comp): V_out[n, i] = 0. # zero out for summing

        nz_below = nz_nodes[n, 0, :]
        nz_above = nz_nodes[n, 1, :]

        # if in bottom cell adjust fraction to larger value to give log layer interp
        # first time step z_fraction[n, 10, m]
        if is_in_bottom_layer[n] == 1:
            zf = z_fraction_bottom_layer[n]
        else:
            zf = z_fraction[n]

        zf1 = 1.0 - zf

        # loop over each node in triangle
        for m in range(3):
            n_node = tri[n_cell[n], m]
            # loop over vector components
            for c in range(n_comp):
                # add contributions from layer above and below particle, for each spatial component at two time steps
                V_out[n, c] +=  BCcord[n, m] * (v1[n_node, nz_below[m], c] * zf1 + v1[n_node, nz_above[m], c] * zf) * dt1 \
                             +  BCcord[n, m] * (v2[n_node, nz_below[m], c] * zf1 + v2[n_node, nz_above[m], c] * zf) * step_dt_fraction  # second time step

# below are development ideas
#_______________________________________________

# todo interpolate 3D feilds at free surface or bottom
def interp_3Dfield_at_surfaces_time_indepenent(F_out, F_data, tri, n_cell, nz_bottom_cell, BCcord, active):
    basic_util.nopass('interp_3Dfield_at_surfaces_time_indepenent not yet implemented')