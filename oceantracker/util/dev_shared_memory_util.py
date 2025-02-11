import numpy as np
from multiprocessing import shared_memory

class SharedMemArray():
    def __init__(self, sm_map= None, values=None, shape= None, dtype=np.float64, fill_value=None,read_only=False):
        # build share memory from existing values or given shape and type
        self.sm = None
        if sm_map is not None:
            self._connect(sm_map,read_only=read_only)
        elif values is None:
            self._create(shape= shape, dtype= dtype, fill_value=fill_value)
        else:
            self._create_from_values(values)

    def _create(self, shape, dtype, fill_value=None):
        # create and empty shared variable
        nbytes = int(np.prod(shape)) if dtype == bool else int(np.prod(shape)*dtype.itemsize)

        self.sm = shared_memory.SharedMemory(create=True, size= nbytes)
        self.data = np.ndarray(shape, dtype=dtype, buffer=self.sm.buf)

        if fill_value is not None:
            self.data[:] = fill_value

        self.map={'shared_mem_name': self.sm.name,
                'shape': self.data.shape,
                'dtype': self.data.dtype.name,
                }

    def _create_from_values(self,values):
        self._create(values.shape, values.dtype, fill_value=None)
        np.copyto(self.data, values)

    def _connect(self, sm_dict_map,read_only=False):
        self.sm   = shared_memory.SharedMemory(sm_dict_map['shared_mem_name'], create=False)
        self.data = np.ndarray(sm_dict_map['shape'], dtype=sm_dict_map['dtype'], buffer=self.sm.buf)
        if read_only: self.data.setflags(write=False)
        self.map = sm_dict_map
        #print('connecting', sm_dict_map)

    def get_shared_mem_map(self): return self.map

    def disconnect(self):
        #print('Diconnected from  shared memory variable', self.map['var_name'], self.map['shared_mem_name'])
        self.sm.close()
        del self.data

    def delete(self):
        if hasattr(self,'sm') and self.sm is not None:
            self.sm.close()
            self.sm.unlink()
            del self.sm
            del self.data