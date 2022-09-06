import numpy as np
from numba import njit

@njit()
def get_values_at_bottom(field_data4D, bottom_cell_index, out=None):
    # get values from bottom cell of LSC grid from a 3D time dependent field, (ie 4D with time)
    if out is None:
        s=field_data4D.shape
        out = np.full(s[:2]+(s[3],), np.nan)

    for n in range(field_data4D.shape[1]):
        out[:,n,:] = field_data4D[:, :, bottom_cell_index[n], :]
    return out



@njit
def depth_aver_SlayerLSC_in4D(data, zlevel, first_cell_offset, out=None):
    # depth average time varying reader 4D data dim(time, node, depth, components) and return for LSC vertical grid
    # return as 4D variable dim(time, node, 1, components)

    # set up with depth dim
    if out is None:
        s = data.shape
        out = np.zeros((s[0], s[1], 1, min(s[3], 2)), dtype=data.dtype)

    for nt in range(out.shape[0]):  # time
        for n in range(out.shape[1]):  # loop over node

            n0 = first_cell_offset[n]
            h = zlevel[nt, n, -1] - zlevel[nt, n, n0]
            if h <= 0:
                out[nt, n, 0, :] = 0.0
                continue
            for m in range(out.shape[3]):  # loop over vector components
                d = 0.
                for nz in range(n0, data.shape[2] - 1):
                    d += 0.5 * (data[nt, n, nz, m] + data[nt, n, nz + 1, m]) * (zlevel[nt, n, nz + 1] - zlevel[nt, n, nz])
                out[nt, n, 0, m] = d / h
    return out


@njit()
def get_time_dependent_triangle_water_depth_from_total_water_depth_at_nodes(total_water_depth_at_nodes, buffer_index, triangles, out):
    # get total time dependent water for grid triangles for use in calc like depth averaged concentrations
    # not used at the moment
    for nt in buffer_index:
        for m in range(triangles.shape[0]):
            out[nt, m] = 0.
            for v in range(3):
                out[nt,m] += total_water_depth_at_nodes[nt, triangles[m,v]] / 3.0  # todo use simple average, but better way?




