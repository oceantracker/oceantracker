# utils for particle tracking
import numpy as np
from time import sleep
from os import path
from pathlib import Path as pathlib_Path
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



def nopass(msg=''):
    raise Exception("Missing method, base method must be overwritten" +msg)


def dummy_fuction(): pass
def atLeast_Nby1(y):
    # create a view of output with at least one vector component
    if y.ndim == 1:
        return  y.reshape((-1, 1))
    else:
        return y


def fillvalue(dtype:str):
    '''value to fill array '''

    if dtype in ['float64','float32', 'int64', 'int32','int16']:
        v = -32768
    elif dtype in ['int8','bool']:
        v = -128
    else:
        CodingError('Need to add another numpy dtype  as string', hint=f'got type {dtype}')
    return v

def CodingError(message='-no error message given',hint=None, info=None):
    # Call the base class constructor with the parameters it needs
    msg= f'Coding error >> {message} \n hint= {hint} \n info= {info}'
    sleep(.5)
    raise Exception(msg)

def get_file_list(root_dir,mask):
    file_list = []
    for fn in pathlib_Path(root_dir).rglob(mask):
        file_list.append(path.abspath(fn))

    return file_list
def IDmapToArray(IDmap:dict, select_keys:list=None):
    # converts a dict mapping names to integer IDs to a numpy array of integers
    # for given keys of dictionary, eg convert particle status
    # where array is used in numba code to check if status is one of given status values

    keys= list(IDmap.keys()) if select_keys is None else select_keys
    IDs =np.full((len(keys),),-32000, dtype=np.int32)
    for n, key in enumerate(keys):
        IDs[n] = IDmap[key]

    return IDs
