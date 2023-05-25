import multiprocessing
from multiprocessing import shared_memory
import numpy as np
import  time



class CreateSharedMemArray():
    def __init__(self, x):
        # build share memory from existing values or given shape and type
        # create shared memory version of given array, and copy in values to self.data

        self.sm = shared_memory.SharedMemory(create=True, size= x.nbytes)
        self.data = np.ndarray( x.shape, dtype=x.dtype, buffer=self.sm.buf)
        np.copyto(self.data, x)
        del x  # free memory from values,which is now self.data

        self.map={'shared_mem_name': self.sm.name,
                'shape': self.data .shape,
                'dtype': self.data .dtype.name}

    def get_shared_mem_map(self): return self.map

    def disconnect(self):
        #print('Diconnected from  shared memory variable', self.map['var_name'], self.map['shared_mem_name'])
        self.sm.close()
        del self.data

    def close(self):
        print('Deleting shared memory variable-', self.map['shared_mem_name'])
        del self.data
        self.sm.close()
        self.sm.unlink()
        del self.sm

class ConnectToSharedMemArray():
    # class to attached to an array given by map
    # class holds reference to memory,
    #   as  must retain a reference to shared memory or it gets garbage collected

    def __init__(self, sm_array_map):
        print('Attempting to shared mem', sm_array_map['shared_mem_name'])
        self.sm  = shared_memory.SharedMemory(sm_array_map['shared_mem_name'], create=False)
        self.data = np.ndarray(sm_array_map['shape'], dtype=sm_array_map['dtype'], buffer=self.sm.buf)

    def close(self):
        # remove link but dont delete/close for all (leave this to shared mem creator)
        self.sm.unlink()


def shared_mem_from_dict_of_arrays(d):
    sm_dic = {}

    for name, a in d.items():
        sm_dic[name] = CreateSharedMemArray(a)

    return  sm_dic


class async_reader_class():
    def __init__(self,shared_mem_maps): 
        self.sm_times_required = ConnectToSharedMemArray(shared_mem_maps['times_required'])
        self.sm_time_buffer = ConnectToSharedMemArray(shared_mem_maps['time_buffer'])

        self.times_required=  self.sm_times_required.data
        self.time_buffer =  self.sm_time_buffer.data
        self.current_buffer_index = 0  # current location of first time step in the buffer
        
 
    
    def close(self):
        self.sm_times_required.close()
        self.sm_time_buffer.close()
        
def run_asyc_reader(**kwargs):
    tag= 'reader>> '
    # link to shared memory
    
    reader = async_reader_class(kwargs['sm_maps'])
    t_req = reader.times_required.data
    t_buffer = reader.time_buffer.data
    
    print( tag+ 'time steps',t_buffer)

    # simulated ring buffer
    n= 0
    while np.isfinite(t_req[0]):

        for tr in t_req:
            if tr not in t_buffer:
                # read time
                t_buffer[n % t_buffer.size] = float(n)
                print(tag + 'read -', tr,'in buffer',t_buffer)
                time.sleep(.01)


    print( tag +'closing async reader ')
    reader.close()
    return True

if __name__ == '__main__':
#if current_process().name == "MainProcess":
    # holder for what time steps are in buffer


    sm_time_buffer= CreateSharedMemArray(np.zeros((3,), dtype = np.float64))
    sm_times_required = CreateSharedMemArray(np.zeros((2,),dtype = np.float64)) # count

    pool = multiprocessing.Pool(processes= 1)
    sm_map  = {'times_required': sm_time_buffer.get_shared_mem_map(),
               'time_buffer': sm_times_required.get_shared_mem_map(),
               }
    result =  pool.apply_async(run_asyc_reader, kwds={'sm_maps': sm_map})

    n_required= 0
    while n_required < 10:
        time.sleep(2)
        n_required += 1
        sm_times_required.data[:] = np.asarray((n_required,n_required+1))
        print('main  >>', n_required,n_required+1, sm_time_buffer.data)

    sm_times_required.data[0]  = np.nan # stop reader
    time.sleep(1) # give time to close reader
    pool.close()
    pool.join()


    sm_time_buffer.close()
    sm_times_required.close()

    #r= reader(d)
    pass