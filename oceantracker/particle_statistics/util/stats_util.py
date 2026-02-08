import numpy as np
from oceantracker.util.numba_util import njitOT
from oceantracker.shared_info import shared_info as si

# compile this constant into numba cod
status_notReleased= int(si.particle_status_flags.notReleased)

def get_dim_names(dims_dict): return [key for key in dims_dict.keys()]


@njitOT
def _sel_status_waterdepth(status, x, water_depth, statuses_to_count_map,  water_depth_range, num_in_buffer, out):
    n_found = 0
    for n in range(num_in_buffer):
        if statuses_to_count_map[status[n]-status_notReleased] and water_depth_range[0] <= water_depth[n] <= water_depth_range[1]:
            out[n_found] = n
            n_found += 1
    return out[:n_found]

@njitOT
def _sel_z_range(x, z_range, sel, out):
    # put subset of those found back into start of sel array
    n_found = 0
    for n in sel:
        if z_range[0] <= x[n, 2] <= z_range[1]:
            out[n_found] = n
            n_found += 1
    return out[:n_found]
@njitOT
def _sel_z_near_seabed(x, water_depth, dz, sel, out):
    # put subset of those found back into start of sel array
    n_found = 0
    for n in sel:
        if x[n, 2] <= -water_depth[n] + dz: # water depth is +ve
            out[n_found] = n
            n_found += 1
    return out[:n_found]

@njitOT
def _sel_z_near_seasurface(x, tide, dz, sel, out):
    # put subset of those found back into start of sel array
    n_found = 0
    for n in sel:
        if x[n, 2] >= tide[n] - dz:
            out[n_found] = n
            n_found += 1
    return out[:n_found]


@njitOT
def _get_age_bin(age, age_bin_edges):
    return  int(np.floor((age - age_bin_edges[0]) / (age_bin_edges[1]- age_bin_edges[0])))