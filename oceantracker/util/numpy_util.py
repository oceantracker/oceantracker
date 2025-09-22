import numpy as np

possible_dtypes=['float64','float32','bool',
                 'int32','int16','int8','int64',
                 ]





def smallest_value(dtype:np.dtype):
    if np.issubdtype(dtype, np.floating):
        fill_value = np.nan
    elif np.issubdtype(dtype, np.integer):
        fill_value = np.iinfo(dtype).min
    else:
        fill_value = None
    return fill_value

class ArrayBytesBuffer():
    '''
     manages a buffer of bytes to take different dtypes
     so that same memory can be used as buffer by multiple
     arrays
     - dev not working
    '''
    def __init__(self):

        self._byte_buffer  = np.zeros([1_000,],dtype=np.byte)

    #def get_buffer

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
        pass

    return S



