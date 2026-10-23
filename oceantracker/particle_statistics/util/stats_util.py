import numpy as np
import numba
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

# count/sum arrays with up to this many bins are accumulated in parallel, each thread adding into its own copy,
# larger arrays are accumulated serially, as zeroing and adding up the copies would cost more than is saved
thread_local_max_bins = 4096

@njitOT
def _thread_local_layout(n_bins, n_values):
    # number of threads, size of each thread's copy padded so copies are on separate cache lines, and values per thread
    n_threads = numba.get_num_threads()
    return n_threads, (n_bins // 8 + 2) * 8, (n_values + n_threads - 1) // n_threads

@njitOTparallel
def _count_in_bins(bins, count_flat):
    # add one to flattened count array at each bin, bins < 0 are skipped
    # takes flattened arrays, so only compiled once, not for each number of dimensions
    n_bins = count_flat.size
    if n_bins > thread_local_max_bins:
        for k in range(bins.size):
            if bins[k] >= 0: count_flat[bins[k]] += 1
        return

    n_threads, stride, chunk = _thread_local_layout(n_bins, bins.size)
    local = np.zeros(n_threads * stride, dtype=count_flat.dtype)
    for t in prange(n_threads):
        for k in range(t * chunk, min((t + 1) * chunk, bins.size)):
            if bins[k] >= 0: local[t * stride + bins[k]] += 1
    for t in range(n_threads):
        for i in range(n_bins): count_flat[i] += local[t * stride + i]

@njitOTparallel
def _sum_in_bins(bins, values, IDs, sum_flat):
    # add values[IDs[k]] to flattened sum array at bins[k]
    n_bins = sum_flat.size
    if n_bins > thread_local_max_bins:
        for k in range(bins.size):
            sum_flat[bins[k]] += values[IDs[k]]
        return

    n_threads, stride, chunk = _thread_local_layout(n_bins, bins.size)
    local = np.zeros(n_threads * stride, dtype=sum_flat.dtype)
    for t in prange(n_threads):
        for k in range(t * chunk, min((t + 1) * chunk, bins.size)):
            local[t * stride + bins[k]] += values[IDs[k]]
    for t in range(n_threads):
        for i in range(n_bins): sum_flat[i] += local[t * stride + i]

@njitOT
def _sum_props_in_bins(prop_list, sum_prop_list, counted, counted_bins):
    # add property values of counted particles to the bin each was counted in, as index into flattened count/sum arrays
    # done after counting, as typed list access inside the particle loop is slow, ~50 ms per property per million particles
    for m in range(len(prop_list)):
        _sum_in_bins(counted_bins, prop_list[m], counted, sum_prop_list[m].reshape(-1))  # view, sum arrays are C contiguous

@njitOT
def _accumulate_counted(sel, count, prop_list, sum_prop_list, counted, counted_bins):
    # counted_bins[k] holds flattened bin of particle sel[k], -1 if not counted,
    # put particles counted and their bins at start of counted and counted_bins, in place is ok as k >= n_counted
    n_counted = 0
    for k in range(sel.size):
        if counted_bins[k] >= 0:
            counted[n_counted] = sel[k]
            counted_bins[n_counted] = counted_bins[k]
            n_counted += 1

    _count_in_bins(counted_bins[:n_counted], count.reshape(-1))  # view, count arrays are C contiguous
    _sum_props_in_bins(prop_list, sum_prop_list, counted[:n_counted], counted_bins[:n_counted])
    return counted[:n_counted]

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


