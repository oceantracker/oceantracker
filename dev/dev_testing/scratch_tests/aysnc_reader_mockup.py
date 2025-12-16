import numpy as np
from multiprocessing import shared_memory, pool, Process
from time import sleep,perf_counter
from oceantracker.util import json_util
import json
from os import remove,path
sleep_duration =.1
comp_speed_ratio=50
def convert_array_to_shared_memory(array):

    #nbytes = int(np.prod(shape)) if dtype == bool else int(np.prod(shape) * dtype.itemsize)
    nbytes =  int(np.prod(array.shape) * array.dtype.itemsize)
    sm = shared_memory.SharedMemory(create=True, size=nbytes)

    info = dict(shared_memoryID=sm.name, shape=array.shape,
                dtype=array.dtype.name,nbytes=nbytes,)

    # copy array to shared memory and discard
    array_sm = np.ndarray(array.shape, dtype= array.dtype, buffer=sm.buf)
    np.copyto(array_sm, array)

    print('setup',array_sm[:3])
    # need to return sm to maintain reference to avoid garbage collection
    return info, array_sm, sm

def connect_to_shared_memory_array(info, readonly=False):
    #sm = shared_memory.SharedMemory(info['shared_memoryID'], create=False)
    sm=shared_memory.SharedMemory(name= info['shared_memoryID'])
    array = np.ndarray(info['shape'], dtype=info['dtype'], buffer=sm.buf)
    if readonly: array.setflags
    return array,sm

def unpack_control_array(control_info):
    control,sm = connect_to_shared_memory_array(control_info, readonly=False)
    reader_states=dict(not_started=-1,read_config=0, set_up_buffers=1)
    runner_states=dict(not_started=-1, set_up_buffers=0, time_stepping=1, finished_time_stepping=10)
    d = dict(run_time_step=control[:1],
                reader_state=control[1:2],
                nt1=control[2:3], # first and last time step in nbuffer
                nt2=control[3:4],
                runner_state=control[4:5],
                runner_time_step=control[5:6],
                control_array=control,
                async_reader_states=reader_states,
                runner_states=runner_states,
               shared_mem=sm)
    return d

def async_reader(control_info):

    c = unpack_control_array(control_info)
    asr = c['async_reader_states']
    rs  = c['runner_states']
    
    sleep(sleep_duration)
    t0 =  perf_counter()
    while c['reader_state'] < asr['read_config']:
        try:
            with open('setup.json', 'r') as file:
                d = json.load(file)
            c['reader_state'][:] = asr['read_config']
        except Exception as e:
            print('async_reader:waiting for setup file for ',f'{perf_counter()-t0:3.0f} sec')
            sleep(sleep_duration)

    # connect to arrays based on setup file
    print('async_reader: connecting to variable buffers')
    vars=dict()
    for name, i in d.items():
        print(f'{name}: {i}')
        v, sm = connect_to_shared_memory_array(i)
        vars[name] = dict(data=v,sm=sm)
    c['reader_state'][:] = asr['set_up_buffers'] # variable buffers set up
    print('async_reader: buffers set up', vars.keys())

    # loop until runner finished
    buffer_size = v.size
    c['nt1'][:] = -1
    while c['runner_state'] < rs['finished_time_stepping'] :
        # get current val for operations
        nt_runner = int(c['runner_time_step'][0])
        c['nt1'][:] = nt_runner
        #print(' async_reader: checking buffers',  c['runner_time_step'] , c['nt1'], c['nt1'])

        while  c['nt2'] < nt_runner + buffer_size :

            nt2 = int(c['nt2'][0])
            #read data
            data = nt2
            buffer_index = nt2 % buffer_size
            vars['time_step']['data'][buffer_index] = data
            c['nt2'][:] += 1
            print('async_reader: filled buffers', nt_runner, c['nt1'], c['nt2'],'data',data)

            sleep(sleep_duration)

    

def runner(control_info):
    c = unpack_control_array(control_info)
    asr = c['async_reader_states']
    rs = c['runner_states']

    # buffer array to share
    time_step= np.zeros((24,), dtype=np.int32)
    time_step_info, time_step, xsm = convert_array_to_shared_memory(time_step)


    i=dict(time_step=time_step_info)
    with open('setup.json', 'w') as file:
        json.dump(i, file)
    c['runner_state'][:] = asr['set_up_buffers']

    t0 = perf_counter()
    while c['reader_state'] < asr['set_up_buffers']:
        print('runner:waiting for  reader to setup its  arrays', f'{perf_counter() - t0:3.0f} sec')
        sleep(sleep_duration)
    print('reader loaded variables')

    for nt in range(100):
        c['runner_time_step'][:] = nt
        # wait until time steps in buffer
        while not   c['nt1'] <= nt < c['nt2']:
            print('runner: waiting for reader', nt,'buffer steps',c['nt1'] ,c['nt2'])
            sleep(sleep_duration)

        print('\t runner: completed time step', nt,', buffer', c['nt1'] ,c['nt2'])
        sleep(comp_speed_ratio*sleep_duration)

    c['runner_state'][:]=  rs['finished_time_stepping']


    pass

if __name__ == '__main__':

    if path.isfile('setup.json'):
        remove('setup.json')
    A = np.full((6,),-1,dtype= np.int32)
    i, A,sm = convert_array_to_shared_memory(A)


    if True:
        p1 = Process(target=async_reader, args=(i,))
        p2 = Process(target=runner, args=(i,))

        p1.start()
        p2.start()

        p1.join()
        p2.join()

        p1.close()
        p2.close()

        print('close', A[:3],)
