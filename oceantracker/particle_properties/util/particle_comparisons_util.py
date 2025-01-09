# in place comparisons/misc of particle properties
# returns indies for which test is true in a view of int32 array

import numpy as np
from numba import njit, get_thread_id, get_num_threads
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange

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

def compared_prop_to_value(part_prop, test, value, out=None):
    # return a view of indices where  part_prop (test) value, is true

    if out is None: out = np.full((part_prop.shape[0],), -127, np.int32)
    comp= _get_comparison(test)

    return _prop_compared_to_value(part_prop,comp , value, out)
    #return _prop_compared_to_value(part_prop,comp , value,_shared_comparison_IndexBuffer, out)


@njitOT
def _prop_compared_to_value(part_prop, comparison_func, value, out):
    #return a view of indices where   part_prop (test) is true fro all particles
   # now search for those where test is true

    nfound = 0
    for nn in range(part_prop.shape[0]):
        if comparison_func(part_prop[nn], value):
            out[nfound] = nn
            nfound += 1

    return out[:nfound]

@njitOT
def _prop_compared_to_valueV2(part_prop, comparison_func, value,shared_comparison_IndexBuffer, out):
    #return a view of indices where   part_prop (test) is true fro all particles
   # now search for those where test is true

    # do find  using threads
    for nn in prange(part_prop.shape[0]):
        shared_comparison_IndexBuffer[nn] = comparison_func(part_prop[nn], value)

    nfound = 0
    for nn in range(part_prop.shape[0]):
        if shared_comparison_IndexBuffer[nn]:
            out[nfound] = nn
            nfound += 1

    return out[:nfound]

def prop_subset_compared_to_value(active, part_prop, test, value, out):
    # return a view of  indices where  part_prop (test) value, is true for active particles
    if out is None: out = np.full((part_prop.shape[0],), -127, np.int32)

    #return _prop_subset_compared_to_value(active, part_prop, _get_comparison(test), value, out)
    return _prop_subset_compared_to_value(active, part_prop, _get_comparison(test),
                                          value,_shared_comparison_IndexBuffer, _number_found_in_each_thread,out)

@njitOT
def _prop_subset_compared_to_valueV1_not_threaded(active, part_prop,comparison_func,value, out):
    #return a view of indices where   part_prop (test) is true
   # now search for those where test is true
    nfound = 0
    for n in active:
        if comparison_func(part_prop[n],value):
            out[nfound] = n
            nfound += 1
    return out[:nfound]

@njitOT
def _prop_subset_compared_to_value(active, part_prop,comparison_func,value,
                                   shared_comparison_IndexBuffer, number_found_in_each_thread,out):
    #return a view of indices where   part_prop (test) is true
   # now search for those where test is true

    # do search split into threads
    for threadID in range(get_num_threads()): number_found_in_each_thread[threadID] = 0

    for nn in prange(active.size):
        n = active[nn]
        if comparison_func(part_prop[n],value):
            threadID = get_thread_id()
            shared_comparison_IndexBuffer[threadID, number_found_in_each_thread[threadID]] = n
            number_found_in_each_thread[threadID] += 1


    # combine results from each thread
    nfound = 0
    for threadID in range(get_num_threads()):
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
