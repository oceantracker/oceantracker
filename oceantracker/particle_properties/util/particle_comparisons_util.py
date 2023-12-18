# in place comparisons/misc of particle properties
# returns indies for which test is true in a view of int32 array

import numpy as np
from numba import njit
from oceantracker.util.numba_util import njitOT

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

def compared_prop_to_value(part_prop, test, value, out=None):
    # return a view of indices where  part_prop (test) value, is true

    if out is None: out = np.full((part_prop.shape[0],), -127, np.int32)
    comp= _get_comparison(test)

    return _prop_compared_to_value(part_prop,comp , value, out)

@njitOT
def _prop_compared_to_value(part_prop, comparison_func, value, out):
    #return a view of indices where   part_prop (test) is true fro all particles
   # now search for those where test is true

    nfound = 0
    for n in range(part_prop.shape[0]):
        if comparison_func(part_prop[n], value):
            out[nfound] = n
            nfound += 1

    return out[:nfound]

def prop_subset_compared_to_value(active, part_prop, test, value, out):
    # return a view of  indices where  part_prop (test) value, is true for active particles
    if out is None: out = np.full((part_prop.shape[0],), -127, np.int32)

    return _prop_subset_compared_to_value(active, part_prop, _get_comparison(test), value, out)

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

@njitOT
def random_selection(active, probability_of_selection, out):
    # from and array of active indices randomly select some indices
    # with probability of choosing any individual index of probability_of_selection
    nfound = 0
    for n in active:
        if np.random.rand() <= probability_of_selection:
            out[nfound] = n
            nfound += 1
    return out[:nfound]

# dual comparisons
@njitOT
def _find_all_in_range(part_prop, prop_value1, propvalue2, out):
    nfound = 0
    for n in range(part_prop.shape[0]):
        if prop_value1 <= part_prop[n] <= propvalue2:
            out[nfound] = n
            nfound += 1
    return out[:nfound]
