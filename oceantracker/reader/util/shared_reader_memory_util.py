import numpy as np


def create_shared_arrayy(sm_map= None, values=None, shape= None, dtype=np.float64, fill_value=None,read_only=False):
    # wrapper for shared memory class, only imports if using shared memory, which requires python >= 3.8
    #from oceantracker.util.shared_memory_util import  SharedMemArray
    #todo shared reading disable until its fully implented
    sm = SharedMemArray(sm_map= sm_map, values=values,
                        shape= shape, dtype=dtype, fill_value=fill_value,read_only=read_only)
    return sm


