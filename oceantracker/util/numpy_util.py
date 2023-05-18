import numpy as np


def numpy_structure_from_dict(d):
    # return a numpy sturcture with fields give by dict keys and copy of  from dictionary

    # used to pass many arguments to numba functions efficiently as attributes of one class variable
    # will ignore any dict within the given dict
    # build class signature
    dtype=[]
    for key,val in d.items():
        if type(val) != dict:
            if type(val) == np.ndarray:
                i = (key,val.dtype,val.shape)
            else:
                i = (key, type(val))
            dtype.append(i)
    S = np.zeros((1,),dtype=dtype)[0]

    #copy dictionary data anf point dict at structure' data
    for name in S.dtype.names:
        S[name] = np.copy(d[name])
        d[name] = S[name]

    return S




