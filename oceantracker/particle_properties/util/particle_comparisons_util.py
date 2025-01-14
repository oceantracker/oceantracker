# in place comparisons/misc of particle properties
# returns indies for which test is true in a view of int32 array

import numpy as np
from oceantracker.util.numba_util import njitOT, njitOTparallel, _merge_thread_index_buffers
import numba as nb
from oceantracker.shared_info import shared_info as si

@njitOT
def is_eq(a, b): return a == b
@njitOT
def is_noteq(a, b): return a != b
@njitOT
def is_lt(a, b): return a < b
@njitOT
def is_lteq(a, b): return a <= b
@njitOT
def is_gt(a, b): return a > b
@njitOT
def is_gteq(a, b): return a >= b

@njitOT
def is_inrange(a, a1 ,a2): return  a1 <=a <= a2

comparison_function_map= {  'eq'  : is_eq,
                            'noteq': is_noteq,
                            'gt'   : is_gt,
                            'gteq' : is_gteq,
                            'lt'   : is_lt,
                            'lteq' : is_lteq}

def _get_comparison(test):
    # set up test
    if test not in comparison_function_map:
        raise Exception('_get_comparison: invalid particle property comparison test  "' + test + '", must one of ' + str(comparison_function_map.keys()))
    return comparison_function_map[test]

def setup_shared_comparison_IndexBuffer(current_particle_buffer_size, n_threads):
    # this gives array to store intermediate results of comparioson
    # for particle_comparisons_util._prop_compared_to_value() to use

    global _shared_comparison_IndexBuffer, _number_found_in_each_thread
    _shared_comparison_IndexBuffer = np.full((n_threads, current_particle_buffer_size), False, dtype=np.int32)
    _number_found_in_each_thread = np.zeros((n_threads,), dtype=np.int32)


def compared_prop_to_value(part_prop_data, test, value, out=None):
    # return a view of indices where  part_prop (test) value, is true

    comp = _get_comparison(test)

    return _prop_compared_to_value(part_prop_data, comp, value, out)
    # test of threaded version
    #_prop_compared_to_value(part_prop,comp , value,
     #              si.thread_index_buffer['buffer'], si.thread_index_buffer['indicies_per_thread'], out)
    #return _merge_thread_index_buffers(si.thread_index_buffer['buffer'], si.thread_index_buffer['indicies_per_thread'], out)

@njitOT
def _prop_compared_to_value(part_prop_data, comparison_func, value, out):
    #return a view of indices where   part_prop (test) is true fro all particles
   # now search for those where test is true

    nfound = 0
    for nn in range(part_prop_data.shape[0]):
        # branchless recording of index if comparison true
        ok = comparison_func(part_prop_data[nn], value)
        out[nfound] = nn
        nfound += ok

    return out[:nfound]

# test of thread safe version
@njitOTparallel
def _prop_compared_to_value_not_used(part_prop_data, comparison_func, value,
                                     thread_index_buffer, indicies_per_thread, out):
    #return a view of indices where   part_prop (test) is true for all particles

    # zero count for each thread
    for i in range(nb.get_num_threads()): indicies_per_thread[i] = 0

    # do find  using threads
    for nn in nb.prange(part_prop_data.shape[0]):
        if comparison_func(part_prop_data[nn], value):
            nthread = nb.get_thread_id()
            thread_index_buffer[nthread, indicies_per_thread[nthread]] = nn
            indicies_per_thread[nthread] += 1

    return _merge_thread_index_buffers(si.thread_index_buffer['buffer'], si.thread_index_buffer['indicies_per_thread'], out)

def prop_subset_compared_to_value(active, part_prop, test, value, out):
    # return a view of  indices where  part_prop (test) value, is true for active particles
    if out is None: out = np.full((part_prop.shape[0],), -127, np.int32)

    return _prop_subset_compared_to_value(active, part_prop, _get_comparison(test), value, out)
    #return _prop_subset_compared_to_value_not_used(active, part_prop, _get_comparison(test),
    #                                      value,_shared_comparison_IndexBuffer, _number_found_in_each_thread,out)

@njitOT
def _prop_subset_compared_to_value(active, part_prop,comparison_func,value, out):
    #return a view of indices where   part_prop (test) is true
   # now search for those where test is true
    nfound = 0
    for n in active:
        if comparison_func(part_prop[n],value):
            out[nfound] = n
            nfound += 1
    return out[:nfound]

@njitOTparallel
def _prop_subset_compared_to_value_not_used(active, part_prop,comparison_func,value,
                                   thread_index_buffer, indicies_per_thread ,out):
    #return a view of indices where   part_prop (test) is true
   # now search for those where test is true

    # do search split into threads
    for threadID in range(nb.get_num_threads()): indicies_per_thread[threadID] = 0

    for nn in nb.prange(active.size):
        n = active[nn]
        if comparison_func(part_prop[n],value):
            threadID = nb.get_thread_id()
            thread_index_buffer[threadID, indicies_per_thread[threadID]] = n
            indicies_per_thread[threadID] += 1


    # combine results from each thread
    nfound = 0
    for threadID in range(nb.get_num_threads()):
        for nn in range(number_found_in_each_thread[threadID]):
            out[nfound] = shared_comparison_IndexBuffer[threadID, nn]
            nfound += 1

    return out[:nfound]

@njitOT
def random_selection(active, probability_of_selection, out):
    # from and array of active indices randomly select some indices
    # with probability of choosing any individual index of probability_of_selection
    found = 0
    for n in active:
        if np.random.rand() <= probability_of_selection:
            out[found] = n
            found += 1
    return out[:found]

# dual comparisons
@njitOT
def _find_all_in_range(part_prop, prop_value1, propvalue2, out):
    nfound = 0
    for n in range(part_prop.shape[0]):
        if prop_value1 <= part_prop[n] <= propvalue2:
            out[nfound] = n
            nfound += 1
    return out[:nfound]
