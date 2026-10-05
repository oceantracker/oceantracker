import numpy as np
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange
from oceantracker.shared_info import shared_info as si

# compile this constant into numba cod
status_notReleased= int(si.particle_status_flags.notReleased)
status_dead= int(si.particle_status_flags.dead)

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

@njitOT
def _sel_below_max_count(counting_events, max_count, sel, out):
    # Select particles from sel where counting_events[n] < max_count
    n_found = 0
    for n in sel:
        if counting_events[n] < max_count:
            out[n_found] = n
            n_found += 1
    return out[:n_found]

@njitOTparallel
def _update_times_count_and_kill_if_requested(counting_events_prop, status,
                                              kill_when_max_counted, max_count_per_particle, sel):
    # update the number of times each particles is count and kill particle if requested and max count exceeded
    for nn in prange(sel.size):
        n = sel[nn]
        counting_events_prop[n] += 1
        if kill_when_max_counted and counting_events_prop[n] >= max_count_per_particle:
            status[n] = status_dead


