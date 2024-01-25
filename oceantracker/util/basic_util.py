# utils for particle tracking
from  copy import deepcopy, copy
import time
import numpy as np
import platform
from psutil import  cpu_count, cpu_freq


from numba import njit
from oceantracker.util.numba_util import njitOT

class OceanTrackerDummyClass(object): pass

def deep_dict_update(d, d_updates):
    # recursively update dictionary tree d, ie a dictionary which may contain dictionaries with d_updates or listes of dictionaries
    # with corressponding key values in dictionary d_updates, d_updates may be a dictionary of dictionaries
    # note this is dumb, will just add new keys in any nested dictionary or change existing key in any nested dictionary based on d_update

    for key, item in d_updates.items():
        #print(key,type(item))
        if type(item) is dict:
            # if item itself is a dictionary
            if key not in  d: d[key]={}   # add and empty dictoary in d_updates not yet in d
            # recursively call update on this dictionary
            d[key] = deep_dict_update(d[key], item)

        elif type(item) is list and len(item)> 0 and type(item[0]) is dict:
            # case of a list of dictionaries
            if key not in d : d[key] = [] # empty list to fill with  dictionaries

            # list of dictionaries
            for n,d2 in enumerate(item):
                if n  >= len(d[key]) : d[key].append({})# add empty dictionary to d list to update
                d[key][n]= deep_dict_update(d[key][n], d2)
                #print(key,case, d2)
        else:
            # not a dictionary or list of dictionaries
            #print(key,item)
            d[key] = item
    return d


def is_substring_in_list(sub_str,str_list):
    out= False
    for s in str_list:
        if sub_str in s: out = True
    return out



def nopass(msg=''):
    raise Exception("Missing method, base method must be overwritten" +msg)



def atLeast_Nby1(y):
    # create a view of output with at least one vector component
    if y.ndim == 1:
        return  y.reshape((-1, 1))
    else:
        return y



@njitOT
def testNumbaRangeChecking():
    x= np.full((10,1),0.)
    x[x.shape[0]] = 1. # out of bounds test
