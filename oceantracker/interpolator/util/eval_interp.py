import numpy as np
from numba import njit, float64, int32, float32, int8, int64, boolean, uint8
from oceantracker.util import  basic_util
from oceantracker.util.profiling_util import function_profiler


@njit()
def time_independent_2Dfield(F_out, F_data, grid, part_prop,  active, step_info):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time independent  2D fields, eg water_depth
    F = F_data[0, :, 0, :]
    n_comp = F.shape[1]  # time step of data is always [node,z,comp] even in 2D
    # loop over active particles and vector components

    for n in active:
        # loop over each node in triangle
        for i in range(n_comp): F_out[n, i] = 0.  # zero out for summing

        for m in range(3):
            n_node = grid['triangles'][part_prop['n_cell'][n], m]
            bc = part_prop['bc_cords'][n, m]
            # loop over vector components
            for c in range(n_comp):
                F_out[n, c] += bc * F[n_node, c]

@njit()
def time_dependent_2Dfield( F_out, F_data, grid, part_prop,  active, step_info):
    # do interpolation in place, ie write directly to F_interp for isActive particles
    # time dependent  fields from two time slices in hindcast

    # loop over active particles and vector components
    for n in active:
        _kernal_time_dependent_2Dfield(F_out[n, :], F_data, grid, part_prop, step_info, n)

@njit()
def _kernal_time_dependent_2Dfield(F_out, F_data, grid, part_prop, step_info, n):
    n_comp = F_data.shape[3]  # time step of data is always [node,z,comp] even in 2D

    F1 = F_data[step_info['nb'][0], :, 0, :]
    F2 = F_data[step_info['nb'][1], :, 0, :]
    # loop over isActive particles and vector components
    for i in range(n_comp): F_out[i] = 0. # zero out for summing

    # loop over each node in triangle
    for m in range(3):
        n_node = grid['triangles'][part_prop['n_cell'][n], m]
        bc = part_prop['bc_cords'][n, m]
        # loop over vector components
        for c in range(n_comp):
            F_out[c] += bc * (step_info['fractional_time_steps'][1] * F1[n_node, c]
                               + step_info['fractional_time_steps'][0] * F2[n_node, c])

# do 3D interp evaluation
@njit()
def time_independent_3Dfield(F_out, F_data, grid, part_prop,  active, step_info):
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
#@function_profiler(__name__)
@njit()
def time_dependent_3Dfield(F_out, F_data, grid, part_prop,  active, step_info):
    #  time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles

    n_comp = F_data.shape[3]  # time step of data is always [nb, node,z,comp] even in 2D

    # create views to remove redundant dim at current and next time step, improves speed?
    F1 = F_data[step_info['nb'][0]  , :, :, :]
    F2 = F_data[step_info['nb'][1], :, :, :]

    # loop over active particles and vector components
    for n in active:
        for i in range(n_comp): F_out[n, i] = 0. # zero out for summing
        zf = part_prop['z_fraction_bottom_layer'][n]
        zf1 = 1. - zf
        nz = part_prop['nz_cell'][n]

        # loop over each vertex in triangle
        for m in range(3):
            n_node = grid['triangles'][part_prop['n_cell'][n], m]

            # for LSC grid need to get highest node of nz or bottom at each triangle vertex
            nzb =  grid['bottom_cell_index'][n_node]  # bottom node at this vertex
            nz_below = max(nzb, nz    )
            nz_above = max(nzb, nz + 1)
            # loop over vector components
            for c in range(n_comp):
                # add contributions from layer above and below particle, for each spatial component at two time steps
                F_out[n, c] +=     part_prop['bc_cords'][n, m] * (F1[n_node, nz_below, c] * zf1 + F1[n_node, nz_above, c] * zf)*step_info['fractional_time_steps'][1]  \
                                +  part_prop['bc_cords'][n, m] * (F2[n_node, nz_below, c] * zf1 + F2[n_node, nz_above, c] * zf)*step_info['fractional_time_steps'][0]  # second time step

@njit
def eval_water_velocity_3D(V_out, V_data, grid,part_prop,  active, step_info):
    #  special case of interpolating water velocity with log layer in bottom cell, linear z interpolation at other depth cells

    # loop over active particles and vector components
    for n in active:
        _kernal_eval_water_velocity_3D(V_out[n, :], V_data, grid, part_prop, step_info, n)

@njit()
def _kernal_eval_water_velocity_3D(V_out, V_data, grid, part_prop, step_info, n):
    # create views to remove redundant dim at current and next time step, improves speed?
    v1, v2 = V_data[step_info['nb'][0], :, :, :], V_data[step_info['nb'][1], :, :, :]

    for i in range(V_out.shape[0]): V_out[i] = 0. # zero out for summing

    nz = part_prop['nz_cell'][n]

    # if in bottom cell adjust fraction to larger value to give log layer interp
    # first time step z_fraction[n, 10, m]
    if part_prop['z_fraction_bottom_layer'][n] >= 0 :
        zf = part_prop['z_fraction_bottom_layer'][n]
    else:
        # fraction =-00 is not on the bottom
        zf = part_prop['z_fraction'][n]

    zf1 = 1.0 - zf

    # loop over each vertex in triangle
    for m in range(3):
        n_node = grid['triangles'][part_prop['n_cell'][n], m]

        # for LSC grid need to get highest node of nz or bottom at each triangle vertex
        nzb =  grid['bottom_cell_index'][n_node]  # bottom node at this vertex
        nz_below = max(nzb, nz    )
        nz_above = max(nzb, nz + 1)
        # loop over vector components
        for c in range(V_out.shape[0]):
            # add contributions from layer above and below particle, for each spatial component at two time steps
            V_out[c] +=  part_prop['bc_cords'][n, m] * (v1[n_node, nz_below, c] * zf1 + v1[n_node, nz_above, c] * zf) * step_info['fractional_time_steps'][1] \
                         +  part_prop['bc_cords'][n, m] * (v2[n_node, nz_below, c] * zf1 + v2[n_node, nz_above, c] * zf) * step_info['fractional_time_steps'][0]   # second time step
            pass

@njit
def update_dry_cell_index( grid, step_info):
    # up date 0-255 dry cell index, used to determine if cell dry at this time
    # uses  reader buffer locations and time step fractions within step info structure
    for n in range(grid['dry_cell_index'].size):
        val  = step_info['fractional_time_steps'][1]*grid['is_dry_cell'][step_info['nb'][0], n]
        val += step_info['fractional_time_steps'][0]*grid['is_dry_cell'][step_info['nb'][1], n]
        grid['dry_cell_index'][n]  = int(255.*val)

# below are development ideas
#_______________________________________________

# todo interpolate 3D feilds at free surface or bottom
def interp_3Dfield_at_surfaces_time_indepenent(F_out, F_data, tri, n_cell, nz_bottom_cell, BCcord, active):
    basic_util.nopass('interp_3Dfield_at_surfaces_time_indepenent not yet implemented')