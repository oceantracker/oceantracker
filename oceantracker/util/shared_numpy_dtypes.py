import numpy as np
# create and hold numpy types, and allow acces as attribute of this module
dtypes= {}

def create_shared_dtype(name, dtype_list):
    # add named dtype to make it assesable
    dtypes[name] = np.dtype(dtype_list)

