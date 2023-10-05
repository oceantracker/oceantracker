import numpy as np
from numba import njit, float64, int32, float32, int8, int64, boolean, uint8
from oceantracker.util import  basic_util
from oceantracker.util.profiling_util import function_profiler

@njit()
def time_independent_2Dfield(F_out, F_data, triangles, n_cell, bc_cords,  active):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time independent  2D fields, eg water_depth
    F = F_data[0, :, 0, :]
    n_comp = F.shape[1]  # time step of data is always [node,z,comp] even in 2D
    # loop over active particles and vector components

    for n in active:
        # loop over each node in triangle
        for i in range(n_comp): F_out[n, i] = 0.  # zero out for summing

        for m in range(3):
            n_node = triangles[n_cell[n], m]
            bc = bc_cords[n, m]
            # loop over vector components
            for c in range(n_comp):
                F_out[n, c] += bc * F[n_node, c]

@njit()
def time_dependent_2Dfield(nb, fractional_time_steps, F_out, F_data, triangles, n_cell, bc_cords,  active):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time dependent  fields from two time slices in hindcast
    n_comp = F_data.shape[3]  # time step of data is always [node,z,comp] even in 2D
    F1 = F_data[nb[0], :, 0, :]
    F2 = F_data[nb[1], :, 0, :]

    # loop over active particles and vector components
    for n in active:

        # loop over isActive particles and vector components
        for i in range(n_comp): F_out[n, i] = 0. # zero out for summing
        n_node = triangles[n_cell[n], :]
        # loop over each node in triangle
        for m in range(3):
            bc = bc_cords[n, m]
            # loop over vector components
            for c in range(n_comp):
                F_out[n, c] += bc * (fractional_time_steps[0] * F1[n_node[m], c]
                                   + fractional_time_steps[1] * F2[n_node[m], c])

# do 3D interp evaluation
@njit()
def time_independent_3Dfield_LSC_grid(F_out, F_data, grid, part_prop, active, step_info):
    #  non-time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles
    # todo do not used yet?
    raise('time_independent_3Dfield not implented')
    n_comp = F_data.shape[2]  # time step of data is always [node,z,comp] even in 2D
    F=  F_data[0, :, :, :]

    # loop over isActive particles and vector components
    for n in active:
        # loop over each node in triangle
        for i in range(n_comp): F_out[n, i] = 0. # zero out for summing
        zf = part_prop['z_fraction'][n]
        zf1= 1.- -zf
        # loop over each node in triangle
        for m in range(3):
            n_node = grid['triangles'][part_prop['n_cell'][n], m]
            bc = part_prop['bc_cords'][n, m]
            nz = part_prop['nz_cell'][n]
            nzb = grid['bottom_cell_index'][n_node]  # bottom node at this vertex
            nz_below = max(nzb, nz)
            nz_above = max(nzb, nz + 1)

            # loop over vector components
            for c in range(n_comp):
                # add contributions from layer above and below particle, for each spatial component
                F_out[n, c] += bc * (F[n_node, nz_below, c] * zf1 + F[n_node, nz_above, c] * zf)
@njit()
def time_dependent_3Dfield_sigma_grid(nb,fractional_time_steps, F_data,
                            triangles,
                            n_cell, bc_cords, nz_cell, z_fraction,
                            F_out, active):
    #  time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles

    n_comp = F_data.shape[3]  # time step of data is always [nb, node,z,comp] even in 2D

    # create views to remove redundant dim at current and next time step, improves speed?
    F1 = F_data[nb[0], :, :, :]
    F2 = F_data[nb[1], :, :, :]

    # loop over active particles and vector components
    for n in active:

        zf2 = z_fraction[n]
        zf1 = 1. - zf2
        nz = nz_cell[n]

        # loop over each vertex in triangle
        for i in range(n_comp): F_out[n, i] = 0. # zero out for summing

        for m in range(3):
            n_node = triangles[n_cell[n], m]
            # loop over vector components
            for c in range(n_comp):
                # add contributions from layer above and below particle, for each spatial component at two time steps
                F_out[n, c] += bc_cords[n, m] * (F1[n_node, nz, c] * zf1 + F1[n_node, nz + 1, c] * zf2)*fractional_time_steps[0]  \
                            +  bc_cords[n, m] * (F2[n_node, nz, c] * zf1 + F2[n_node, nz + 1, c] * zf2)*fractional_time_steps[1]  # second time step


#@function_profiler(__name__)
@njit()
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

@njit
def update_dry_cell_index(is_dry_cell,dry_cell_index, current_buffer_steps,fractional_time_steps):
    # up date 0-255 dry cell index, used to determine if cell dry at this time
    # uses  reader buffer locations and time step fractions within step info structure
    for n in range(dry_cell_index.size):
        val  = fractional_time_steps[0]*is_dry_cell[current_buffer_steps[0], n]
        val += fractional_time_steps[1]*is_dry_cell[current_buffer_steps[1], n]
        dry_cell_index[n]  = int(255.*val)

# below are development ideas
#_______________________________________________

# todo interpolate 3D feilds at free surface or bottom
def interp_3Dfield_at_surfaces_time_indepenent(F_out, F_data, tri, n_cell, nz_bottom_cell, BCcord, active):
    basic_util.nopass('interp_3Dfield_at_surfaces_time_indepenent not yet implemented')