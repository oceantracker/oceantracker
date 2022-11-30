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
def time_dependent_3Dfield(F_out, F_data, nb, step_dt_fraction, tri, n_cell, nz_node, z_fraction, BCcord, active):
    #  time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles

    n_comp = F_data.shape[3]  # time step of data is always [nb, node,z,comp] even in 2D

    # create views to remove redundant dim at current and next time step, improves speed?
    F1 = F_data[nb  , :, :, :]
    F2 = F_data[nb+1, :, :, :]

    nz_node1 = nz_node[:, 0, :]
    nz_node2 = nz_node[:, 1, :]

    z_fraction1 = z_fraction[:, 0, :]
    z_fraction2 = z_fraction[:, 1, :]

    dtm1 = 1. - step_dt_fraction
    # loop over isActive particles and vector components
    for n in active:
        for i in range(n_comp): F_out[n, i] = 0. # zero out for summing

        # loop over each node in triangle
        for m in range(3):
            n_node = tri[n_cell[n], m]
            bc = BCcord[n, m]

            # depth cell and zfraction is required for each time slice of the field
            nz1 = nz_node1[n, m]
            nz2 = nz_node2[n, m]

            zf1 = z_fraction1[n, m]
            zf2 = z_fraction2[n,  m]

            zf1m1 = 1. - zf1
            zf2m1 = 1. - zf2

            # loop over vector components
            for c in range(n_comp):
                # add contributions from layer above and below particle, for each spatial component at two time steps
                F_out[n, c] += bc * (F1[n_node, nz1, c] * zf1m1 + F1[n_node, nz1 + 1, c] * zf1)*dtm1  # first time step
                F_out[n, c] += bc * (F2[n_node, nz2, c] * zf2m1 + F2[n_node, nz2 + 1, c] * zf2)*step_dt_fraction  # second time step

@njit
def eval_water_velocity_3D(V_out, V_data, nb, step_dt_fraction, tri, n_cell, nz_node, z_fraction, BCcord, zlevel, nz_bottom, z0, active):
    #  special case of interpolating water velocity with log layer in bottom cell, linear z interpolation at other depth cells

    n_comp = V_data.shape[3]  # time step of data is always [node,z,comp] even in 2D

    # create views to remove redundant dim at current and next time step, improves speed?
    v1,     v2       = V_data[nb  , :, :, :], V_data[nb + 1, :, :, :]
    zlevel1,zlevel2  = zlevel[nb  , :, :],    zlevel[nb + 1, :, :]

    nz_node1 = nz_node[:, 0, :]
    nz_node2 = nz_node[:, 1, :]

    z_fraction1 = z_fraction[:, 0, :]
    z_fraction2 = z_fraction[:, 1, :]

    dtm1 = 1. - step_dt_fraction

    # loop over active particles and vector components
    for n in active:
        for i in range(n_comp): V_out[n, i] = 0. # zero out for summing

        # loop over each node in triangle
        for m in range(3):
            n_node = tri[n_cell[n], m]
            bc = BCcord[n, m]

            # depth cell and zfraction is required for each time slice of the field
            nz1 = nz_node1[n, m]
            nz2 = nz_node2[n, m]

            # if in bottom cell adjust fraction to larger value to give log layer interp
            # first time step z_fraction[n, 10, m]
            nzb = nz_bottom[n_node]
            if nz1 == nzb:
                dz = zlevel1[n_node, nzb+1]- zlevel1[n_node, nzb]
                if dz < z0:
                    zf1 = 0.0
                else:
                    # adjust z fraction so that linear interp acts like log layer
                    z0p = z0/dz
                    zf1 = (np.log(z_fraction1[n, m] + z0p) - np.log(z0p))/ (np.log(1.+ z0p) - np.log(z0p))
            else:
                zf1 = z_fraction1[n, m]

            # second time step z_fraction[n, 1, m]
            if nz2 == nzb:
                dz = zlevel2[n_node, nzb+1]- zlevel2[n_node, nzb]
                if dz < z0:
                    zf2 = 0.0
                else:
                    # adjust z fraction so that linear interp acts like log layer
                    z0p = z0/dz
                    zf2 = (np.log(z_fraction2[n, m] + z0p) - np.log(z0p))/ (np.log(1.+ z0p) - np.log(z0p))
            else:
                zf2 = z_fraction2[n, m]

            zf1m1, zf2m1  = 1. - zf1, 1. - zf2

            # loop over vector components
            for c in range(n_comp):
                # add contributions from layer above and below particle, for each spatial component at two time steps
                V_out[n, c] += bc * (v1[n_node, nz1, c] * zf1m1 + v1[n_node, nz1 + 1, c] * zf1) * dtm1 \
                             + bc * (v2[n_node, nz2, c] * zf2m1 + v2[n_node, nz2 + 1, c] * zf2) * step_dt_fraction  # second time step

@njit
def eval_water_velocity_3D_v2_usingkernal_is_slower(V_out, V_data, nb, step_dt_fraction, tri, n_cell, nz_node, z_fraction, BCcord, zlevel, nz_bottom, z0, active):
    #  special case of interpolating water velocity with log layer in bottom cell, linear z interpolation at other depth cells
    for n in active:
        _eval_single_water_velocity_3D(V_out[n, :], V_data[nb , :, :, :],V_data[nb+1, :, :, :],
                                       zlevel[nb, :, :], zlevel[nb+1, :, :],
                                       step_dt_fraction, tri, n_cell[n],
                                       nz_node[n,: , :], z_fraction[n,:,:],
                                        BCcord[n, :], nz_bottom, z0)

def _eval_single_water_velocity_3D(V_out, V_data1,V_data2,
                                   zlevel1,zlevel2,
                                   step_dt_fraction, tri, n_cell,
                                   nz_node, z_fraction,
                                   BCcord,  nz_bottom, z0):
    n_comp = V_data1.shape[2]

    dtm1 = 1. - step_dt_fraction
    # zero out for summing over nodes in this triangle
    for i in range(n_comp): V_out[i] = 0.

    # loop over each node in triangle
    for m in range(3):
        n_node = tri[n_cell, m]

        # depth cell and zfraction is required for each time slice of the field
        nz1, nz2 = nz_node[0, m], nz_node[1, m]

        # if in bottom cell adjust fraction to larger value to give log layer interp
        # first time step z_fraction[n, 10, m]
        nzb= nz_bottom[n_node]
        if nz1 == nzb:
            dz = zlevel1[n_node, nzb+1]- zlevel1[n_node, nzb]
            if dz < z0:
                zf1 = 0.0
            else:
                # adjust z fraction so that linear interp acts like log layer
                z0p = z0/dz
                zf1 = (np.log(z_fraction[0, m] + z0p) - np.log(z0p))/ (np.log(1.+ z0p) - np.log(z0p))
        else:
            zf1 = z_fraction[0, m]

        # second time step z_fraction[n, 1, m]
        if nz2 == nzb:
            dz = zlevel2[n_node,nzb+1]- zlevel2[n_node,nzb]
            if dz < z0:
                zf2 = 0.0
            else:
                # adjust z fraction so that linear interp acts like log layer
                z0p = z0/dz
                zf2 = (np.log(z_fraction[1, m] + z0p) - np.log(z0p))/ (np.log(1.+ z0p) - np.log(z0p))
        else:
            zf2 = z_fraction[1, m]

        zf1m1 = 1. - zf1
        zf2m1 = 1. - zf2

        # loop over vector components
        bc = BCcord[m]
        for c in range(n_comp):
            # add contributions from layer above and below particle, for each spatial component at two time steps
            V_out[c] += bc * (V_data1[n_node, nz1, c] * zf1m1 + V_data1[n_node, nz1 + 1, c] * zf1) * dtm1  # first time step
            V_out[c] += bc * (V_data2[n_node, nz2, c] * zf2m1 + V_data2[n_node, nz2 + 1, c] * zf2) * step_dt_fraction  # second time step




# todo interpolate 3D feilds at free surface or bottom
def interp_3Dfield_at_surfaces_time_indepenent(F_out, F_data, tri, n_cell, nz_bottom_cell, BCcord, active):
    basic_util.nopass('interp_3Dfield_at_surfaces_time_indepenent not yet implemented')