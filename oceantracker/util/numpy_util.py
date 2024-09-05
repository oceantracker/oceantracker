import numpy as np

possible_dtypes=['float64','float32','bool',
                 'int32','int16','int8','int64',
                 ]
def ensure_int32_dtype(x, missing_value=None):
    # if array is float dtype,makes it integer dtype
    # replacing  nans  with missing value
    if not isinstance(x,np.integer):
        missing_value= np.iinfo(np.int16).min if missing_value is None else missing_value
        x[np.isnan(x)] = missing_value
        x = x.astype(np.int32)
    return x

def numpy_structure_from_dict(d):
    # return a numpy sturcture with fields give by dict keys and copy of  from dictionary

    # used to pass many arguments to numba functions efficiently as attributes of one class variable
    # will ignore any dict within the given dict
    # build class signature
    # wont transoher dattime64, str, dict etc
    dtype=[]
    for key,val in d.items():
        if val is not None and type(val) != dict and type(val) != str:
            if type(val) == np.ndarray:
                if not np.issubdtype(val.dtype,np.datetime64) and not np.issubdtype(val.dtype,np.timedelta64):
                    dtype.append((key,val.dtype,val.shape))
            else:
                dtype.append((key, type(val)))

    # check if too big for numpy indexing limit
    S = np.zeros((1,),dtype=dtype)[0]

    #copy dictionary data and point dict at structure's data
    for name in S.dtype.names:
        S[name] = np.copy(d[name])

    return S

def numpy_array_of_structures_from_dict(d):
    # return a array of numpy sturcture with fields give by dict keys and copy of  from dictionary
    # array is  based on first dimension, which must be the same

    # wont transoher dattime64, str, dict etc
    dtype=[]
    shape0=[]
    for key,val in d.items():
        if type(val) == np.ndarray:
            shape0.append(val.shape[0])
            dtype.append((key,val.dtype,val.shape[1:]))
    if np.unique(np.asarray(shape0)).size >1:
        raise Exception('numpy_array_of_structures_from_dict all dict items must be arrays and have the same first dime ' )
    # check if too big for numpy indexing limit
    S = np.zeros((shape0[0],),dtype=dtype)

    #copy dictionary data and point dict at structure's data
    for name in S.dtype.names:
        S[name] = np.copy(d[name])
        d[name]= S[name]
        #print('xx', name,  d[name].data, S[name] .data,np.may_share_memory(d[name],S[name]))
        pass

    return S



