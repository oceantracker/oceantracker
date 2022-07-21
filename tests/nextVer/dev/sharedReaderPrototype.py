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
                'mem_block_name': self.sm.name,
                'shape': self.data.shape,
                'dtype': self.data.dtype.name}

    def _connect(self, sm_dict_map):
        self.sm   = mp.shared_memory.SharedMemory(sm_dict_map['mem_block_name'], create=False)
        self.data = np.ndarray(sm_dict_map['shape'], dtype=sm_dict_map['dtype'], buffer=self.sm.buf)

        self.map = sm_dict_map
        print('connecting', sm_dict_map)

    def get_shared_mem_map(self): return self.map

    def disconnect(self):
        #print('Diconnected from  shared memory variable', self.map['var_name'], self.map['mem_block_name'])
        self.sm.close()
        del self.data

    def delete(self):
        print('Deleting shared memory variable-',self.map['var_name'], self.map['mem_block_name'])
        del self.data
        self.sm.close()
        self.sm.unlink()
        del self.sm


def worker(d):
    work(d)
    #try :

    #except Exception:
    #    print(traceback.format_exc())
def work(d):
    workerID= d['processor_number']

    rm = d['run_management']

    vars={}
    for sm_map in d['shared_arrays']:
        v = SharedMemArray(sm_map=sm_map)
        vars[v.map['var_name']] = v

    #print('data mapped',n)

    rm['workers_alive'][workerID]= True
    print("Worker alive ", workerID, rm['workers_alive'][workerID])
    last_msg = time.perf_counter()
    while rm['workers_alive'][workerID]:

        if rm['buffer_filled'].get() ==0 or rm['steps_completed_workers'][workerID] == rm['buffer_filled'].get():
            # wait on reader
            if time.perf_counter()- last_msg > 1:
                print('  worker ', workerID, ' waiting on reader or other workers, steps completed=', rm['buffer_filled'].get())
                last_msg = time.perf_counter()
            time.sleep(.1)
        else:
            # do work on buffer
            for nb in range(rm['buffer_filled'].get()):
                vars['a0'].data[nb, 1] += 2
                time.sleep(.2 * np.random.random())
                rm['steps_completed_workers'][workerID] += 1

            print('Worker', workerID, '  steps completed ', rm['steps_completed_workers'][workerID])

    print('Worker stopped', workerID)

    for name, v in vars.items():   v.disconnect()

    return (workerID,'done')


if __name__ == '__main__':
    n_workers= 3

    mp.set_start_method('spawn')
    pool = mp.Pool(6)

    run_management= {'buffer_filled': mp.Manager().Value(int, -1),
                     'nt_start_buffer': mp.Manager().Value(int, -1),
                    'workers_alive': mp.Manager().list(n_workers * [False]),
                    'steps_completed_workers': mp.Manager().list(n_workers * [0])
                     }
    buffer_size=31
    s=(buffer_size,2)

    sm_vars= {}
    sm_maps = []
    dtypes=[np.float64, np.float32, np.int32, bool,  np.int8]
    for n in range(len(dtypes)):
        vn='a'+str(n)
        sm_vars[vn] = SharedMemArray(var_name=vn, shape=s, dtype=dtypes[n], fill_value=8)
        sm_maps.append(sm_vars[vn].get_shared_mem_map())

    tasks=[]
    for n in range(n_workers):
        tasks.append({'processor_number': n, 'shared_arrays': sm_maps,
                      'run_management': run_management})


    # test call
    #worker(tasks[0])
    out =  pool.map_async(worker,tasks)

    print('running')
    # watch for end
    #time.slep(3)

    # wake up workers
    rm=run_management

    tstart =time.perf_counter()
    nt0=10
    time_chunking =11

    nt_first =0
    nt_last= 300
    n_chunk =0
    nt=21+np.arange(121) # time steps to rin

    while nt.shape[0] >1 :

        rm['buffer_filled'].set(0)
        # read block

        print('Reader filled buffer, chunk', n_chunk,'time step', nt[0])
        time.sleep(.1*np.random.random())
        ntb0=rm['nt_start_buffer'].get()
        buffer_index = nt[:time_chunking] % buffer_size

        sm_vars['a0'].data[buffer_index, 0] = buffer_index
        n_chunk += 1
        # tell workers buffer is full
        # first set next buffer step to be proces to zero for all workers
        for n in range(len(rm['steps_completed_workers'])): rm['steps_completed_workers'][n] = 0
        rm['nt_start_buffer'].set(nt[0])
        rm['buffer_filled'].set(20)

        # wait for workers to catch  up to end of buffer
        t0 =time.perf_counter()
        last_msg = time.perf_counter()

        while not all([ (x == rm['buffer_filled'].get()) for x in rm['steps_completed_workers']]):
            # get current state of workers

            worker_steps_completed = [n for n in rm['steps_completed_workers']]
            #print('master',worker_steps_completed)
            time.sleep(.01)
            #print(int(time.perf_counter()-t0),t_warning)
            if time.perf_counter() - last_msg > 1:
                print('  master block time step', nt[0], ' waiting',time.perf_counter()-t0,
                      'buffer has filled ',  rm['buffer_filled'].get() ,
                      'Worker step range', min(worker_steps_completed),'-', max(worker_steps_completed),
                      ', workers are at steps ',worker_steps_completed)
                last_msg = time.perf_counter()

            if tstart - time.perf_counter() > 60:
                print('engine break')
                break

        nt = nt[time_chunking:]

        if tstart - time.perf_counter() > 60:
            print('engine break')
            break
    # stop all workers
    for n in range(n_workers) : run_management['workers_alive'][n] = False
    time.sleep(1)

    pool.close()
    pool.terminate()
    pool.join()

     #clear shared menory
    for name, v in sm_vars.items():
        v.delete()



