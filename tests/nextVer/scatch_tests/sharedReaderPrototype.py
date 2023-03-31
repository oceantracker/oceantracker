import multiprocessing as mp
from multiprocessing import Pool
import traceback
import time, random


import numpy as np
from copy import deepcopy, copy

class SharedMemArray():
    def __init__(self, sm_map= None, var_name=None, values=None, shape= None, dtype=np.float64, fill_value=None):
        # build share memory from existing values or given shape and type

        if sm_map is not None:
            self._connect(sm_map)
        else:
            self._create(var_name, values=values, shape= shape, dtype= dtype, fill_value=fill_value)

    def _create(self,var_name, values, shape, dtype, fill_value):
        # create, and copy in values if given
        if values is None:
            # avoid making a new values array, get bytes from data type
            # there is no longer an np.bool, just bool
             nbytes = int(np.prod(shape)) if dtype == bool else int(np.prod(shape)*dtype().itemsize)
        else:
            # override given shape to match values
            shape=  values.shape
            dtype = values.dtype
            nbytes= values.nbytes

        self.sm = mp.shared_memory.SharedMemory(create=True, size= nbytes)
        self.data = np.ndarray(shape, dtype=dtype, buffer=self.sm.buf)

        if values is not None :
            np.copyto(self.data, values)
            del values  # free memory from values,which is now self.data
        elif fill_value is not None:
            self.data[:] = fill_value

        self.map={'var_name': var_name,
                'shared_mem_name': self.sm.name,
                'shape': self.data.shape,
                'dtype': self.data.dtype.name}

    def _connect(self, sm_dict_map):
        self.sm   = mp.shared_memory.SharedMemory(sm_dict_map['shared_mem_name'], create=False)
        self.data = np.ndarray(sm_dict_map['shape'], dtype=sm_dict_map['dtype'], buffer=self.sm.buf)

        self.map = sm_dict_map
        #print('connecting', sm_dict_map)

    def get_shared_mem_map(self): return self.map

    def disconnect(self):
        #print('Diconnected from  shared memory variable', self.map['var_name'], self.map['shared_mem_name'])
        self.sm.close()
        del self.data

    def delete(self):
        print('Deleting shared memory variable-',self.map['var_name'], self.map['shared_mem_name'])
        del self.data
        self.sm.close()
        self.sm.unlink()
        del self.sm


def worker(d):

    workerID= d['processID']

    rm = d['shared_read_build_info']['run_management']

    vars={}
    for s in d['shared_read_build_info']['vars']:
        vars[s['var_name']] =  SharedMemArray(sm_map=s)

    #print('data mapped',n)

    rm['workers_alive'][workerID]= True
    print("Worker alive ", workerID, rm['workers_alive'][workerID])

    nt =0
    while rm['workers_alive'][workerID]:
        if rm['nt_first'].value <= nt <= rm['nt_last'].value :

            print('W:%02.0f- calc' % workerID,nt)
            nt +=1
            time.sleep(.1)
        else:
            print('W:%02.0f-waiting' % workerID, nt)
            time.sleep(.1)

    rm['workers_alive'][workerID] = False
    print('Worker stopped', workerID)

    return (workerID,'done')

class dummy_shared_reader(object):
    def __init__(self):
        self.vars={}
        self.run_management = {'nt_first': mp.Manager().Value(int, -1),
                          'nt_last': mp.Manager().Value(int, -1),
                          'workers_alive': mp.Manager().list(n_workers * [False]),
                          'steps_completed_workers': mp.Manager().list(n_workers * [0])
                          }
        buffer_size = 31
        s = (buffer_size, 30)

        self._add_shared_var('time', (buffer_size,), np.float64, fill_value=np.nan)
        self._add_shared_var('x', (buffer_size,20), np.float64, fill_value=np.nan)
        self._add_shared_var('status', (buffer_size, 20), np.int8, fill_value=-1)

    def _add_shared_var(self,name,shape,data_type,fill_value=None):
          self.vars[name] =  SharedMemArray(var_name=name, shape=shape, dtype=data_type, fill_value=fill_value)

    def get_shared_mem_build_info(self):
        out= {'run_management':self.run_management,'vars': {}}
        out['vars']=[]
        for name, s in self.vars.items():
            out['vars'].append(s.map)

        return out

    def update(self):
        a=1

def run_reader(shared_mem_vars):

    sm={}
    for s in shared_mem_vars['vars']:
        sm[s['var_name']] =  SharedMemArray(sm_map=s)

    rm = shared_mem_vars['run_management']
    b= 24

    for nt in range(100):
        print('reader', nt)
        while np.any(np.array(rm['steps_completed_workers']) <= nt):
            time.sleep(.1)
            print('Reader waiting',nt,str(rm['steps_completed_workers']))
        else:
            print('Reader advance', str(rm['steps_completed_workers']))
            sm['time'].data[nt] = n
            rm['nt_last'] +=1

        print('R1',rm['steps_completed_workers'],sm['time'].data[0], sm['time'].data[nt])
        # range of time steps in buffer
        rm['nt_first'] = n
        rm['nt_last'] = n+b-1

if __name__ == '__main__':


    n_workers= 3

    mp.set_start_method('spawn')

    reader=dummy_shared_reader()
    bi = reader.get_shared_mem_build_info()
    rm=reader.run_management

    tasks=[]
    for n in range(n_workers):
        tasks.append({'processID': n, 'shared_read_build_info' :bi})
    worker_status = rm['workers_alive']

    reader_pool = mp.Pool(1)
    reader_out = reader_pool.apply_async(run_reader,args= (bi,))

    #time.sleep(.5)

    time.sleep(1)
    rm['workers_alive'][0] = False
    print( rm['workers_alive'])

    worker_pool = mp.Pool(n_workers)
    worker_out = worker_pool.map_async(worker, tasks)
    #worker_pool.wait()

    time.sleep(5)
    #worker_pool.close()
    #worker_pool.join()
    #print(worker_out)

    # reader_pool.close()
    # reader_pool.join()
    #for w in worker_status:
    #    w=False



     #clear shared menory
    #for name, v in sm_vars.items():
    #    v.delete()



