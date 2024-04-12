from time import sleep, perf_counter
import numpy as np
from multiprocessing import shared_memory,Pool
import sys
from  numba import njit
from copy import  deepcopy, copy
import traceback

from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC


class AsyncReaderManager():
    def create_shared_memory(self,grid):

        # below are needed to bulid async reader


        # set up shared memory for arrays vars in dict
        self.shared_var_builder =dict(grid={})
        self.shared_mem_refs= {}# must mainin these to stop garbage collection

        control_data,self.shared_var_builder['control'] =self.make_shared_ndarray('control_array', np.full((5,), 0, dtype=np.int32))
        self.control_array = ControlAsyc(control_data) # class to control interaction

        # make data point to shared memory
        for name, item in grid.items():
            grid[name],self.shared_var_builder['grid'][name] = self.make_shared_ndarray(name, item)

        pass


    def make_shared_ndarray(self, name, x):
        mem_builder = dict(type = type(x),dtype = x.dtype, shape = x.shape,
            order = 'C' if x.flags.c_contiguous else 'F', bytes = x.nbytes)

        sm = shared_memory.SharedMemory(create=True, size=x.nbytes)

        mem_builder['shared_mem_name'] = sm.name
        mem_builder['bytes'] = sm.size

        # make array
        data = np.ndarray(x.shape, dtype=x.dtype, buffer=sm.buf,
                          order='C' if x.flags.c_contiguous else 'F')
        np.copyto(data, x)
        self.shared_mem_refs[sm.name] = sm # reference required to prevent garbage collection

        return data, mem_builder # used to point orignal x at shared data


    def start(self, settings, grid, reader):

        self.info =dict(reader_info= deepcopy(reader.info),
                        reader_params = reader.params,
                        settings=settings)
        info = self.info
        self.create_shared_memory(grid)

        # set up time steps at the start of run


        self.update_attemps = 0
        #asyc_reader_child(self.info,self.shared_var_info)
        self.pool = Pool(processes=1)
        result = self.pool.apply_async(asyc_reader_child, args=(info,self.shared_var_builder,))

            # close the process pool
            #p.close()
            # wait for all tasks to finish
            #p.join()

    def update(self,n_time_step, nt_model):

        ca = self.control_array
        ca.set_current_hydro_step(nt_model)
        # pause if  time steps are not in buffer
        self.update_attemps += 1
        #print('parent- updating attempts', self.update_attemps,'nt_ model'  ,control['nt_hydro_current'], control['nt_hydro_buffer'])
        count = 0
        while not ca.is_hydro_step_in_buffer(nt_model) and  not ca.is_async_running():
            sleep(.01)
            count += 1
            if count % 50 ==0:
                print('parent- waiting for reader to fill',count,
                      ca.get_current_hydro_step(), ca.get_buffer_start(),ca.get_steps_in_buffer())

            self.update_attemps = 0

        print('           check' ,ca.buffer_state())


    def close(self):
        ca = self.control_array
        ca.end()

        # close the process pool
        self.pool.close()
        # wait for all tasks to finish
        self.pool.join()

        # clear shared memory # leave open??
        for name, sm in self.shared_mem_refs.items():
            sm.close()
            sm.unlink()

def asyc_reader_child(info, shared_var_info):
    print('*****  start asyc-reader')
    try:
        _asyc_reader_engine(info, shared_var_info)
    except Exception as e:
        print(e)
        print(traceback.format_exc())

    print('*****  ended asyc-reader')

def _asyc_reader_engine(info, shared_var_info):
    print(shared_var_info)
    shared_refs = {}  # maintian refence
    ml = dummy_msg_logger()
    # map grid variables to share mem
    grid = {}
    for name, item in shared_var_info['grid'].items():
        grid[name]= connect_to_shared_memory(item, shared_refs)
    # wrap contol data in a class
    ca = ControlAsyc(connect_to_shared_memory(shared_var_info['control'], shared_refs))

    # fill buffer
    r = Reader()
    r.params= info['reader_params']
    r.info = info['reader_info']
    bi = r.buffer_info
    r.initial_setup()
    # fill first two time steps
    nt_fill= ca.get_current_hydro_step() + np.arange(2)


    settings = info['settings']
    count = 0
    ca.start_async_running()
    while ca.get_buffer_start() < ca.get_current_hydro_step() and ca.is_async_running():
        sleep(settings['async_pause_interval'])
        # see if time step changed
        count += 1
        #print('child- checking for read, attempt#',count,' , nt_model', nt_model, control['nt_hydro_buffer'])
        t0= perf_counter()
        # get unchanging copies of state
        num_in_buffer= ca.get_steps_in_buffer()

        # retain prevours and next tme step
        nt_required= np.arange(max(0,ca.get_current_hydro_step()),
                              min(ca.get_current_hydro_step()+bi['time_buffer_size'],r.info['hydro_model_time_steps'])
                              )

        # fill one by one to allow comupation to move forward
        if nt_required.size > 0:
            for nt in nt_required :
                nt_read = r.fill_buffers(grid, nt)
                ca.inc_buffer(1)
                count =0
                t0 = perf_counter()
            ml.msg( '     Filled ' + ca.buffer_state())

        if (perf_counter()-t0) > settings['async_progress_warning_interval']:
            ml.msg(f'asyc child reader, has waited {perf_counter()-t0:.00f} secs for  model solver to move forward',
                   warning =True)



class dummy_file():
    def __init__(self):
        self.time =np.arange(0,2*24*3600,3600.)


class Reader(ParameterBaseClass):
    def __init__(self):
        super().__init__()
        self.add_default_params(dict(time_buffer_size=PVC(10, int)
                                 ))

        self.info = {}
        self.buffer_info ={}


    def initial_setup(self):
        grid = dict(time=np.full((self.params['time_buffer_size'],), np.nan))
        f = dummy_file()
        info = self.info
        info['hydro_model_time_step'] =f.time[1] - f.time[0]
        info['hydro_model_time_range'] = np.asarray([f.time[0], f.time[-1]])
        info['hydro_model_time_steps'] = f.time.size

        bi = self.buffer_info
        bi['n_filled'] = 0
        bi['time_buffer_size'] = self.params['time_buffer_size']
        bi['buffer_available'] = bi['time_buffer_size']
        bi['nt_buffer0'] = 0

        return grid

    def read_time(self, file_index):
        f = dummy_file()
        return f.time[file_index]

    def get_hydrofile_time_step(self,time):
        # this is field group property??
        info= self.info
        nt = int(info['hydro_model_time_steps']*(time- info['hydro_model_time_range'][0])/(info['hydro_model_time_range'][1]-info['hydro_model_time_range'][0]))
        return nt

    def fill_buffers(self,grid, nt_hydro_required):
        # todo move to reading a single time step?
        info = self.info
        bi = self.buffer_info

        # clip required nt to range
        nt_hydro = nt_hydro_required.copy()
        nt_hydro = nt_hydro[ np.logical_and( 0 <= nt_hydro ,nt_hydro < info['hydro_model_time_steps'])]
        buffer_index = nt_hydro % bi['time_buffer_size']


        # convert global nt to file nt
        file_index = nt_hydro
        grid['time'][buffer_index] = self.read_time(file_index)

        return nt_hydro


class FieldGroupManger(ParameterBaseClass):
    def __init__(self):
        super().__init__()
        self.add_default_params(dict(
                    async_pause_interval=PVC(.005, [float, int],
                                            doc_str='time asyc reader pauses bewteen checking if action is needed',
                                            units='s'),
                    async_progress_warning_interval=PVC(30., [float, int],
                                            doc_str='time asyc reader warns of time, if reader or model solver waits too long for movement by the other',
                                            units='s' ),
                                 ))
    def initial_setup(self):

        self.info= dict(nt_hydro_current=np.full((2,), -1,dtype=np.int32),
                        current_step_fractions=np.full((2,), -1, dtype=np.float64),
                        )

        self.reader = Reader()
        reader = self.reader
        reader.params = merge_params_with_defaults(reader.params,reader.default_params,reader.shared_info.msg_logger)

        async_settings=  {k: v for k, v in self.params.items() if k.startswith('async')}

        self.grid = reader.initial_setup()
        #setup async reader
        self.A = AsyncReaderManager()
        self.A.start(async_settings,self.grid,self.reader)

    def update(self, time_model):

        info=  self.info
        # get buffer step at this and next hydro model step
        nb = self.reader.get_hydrofile_time_step(time_model)
 
        self.A.update(nb) # fill buffer if possible

        time_buffer = self.grid['time']
        nb= info['nt_hydro_current'] % time_buffer.size

        f= (time_model - time_buffer[nb[0]]) / (time_buffer[nb[1]] -time_buffer[nb[0]])
        info['current_step_fractions'][0] = 1. - f
        info['current_step_fractions'][1] = f
        self.step_fraction = f
        pass

    def interp_fields(self):
        # interp at current time
        grid= self.grid
        info = self.info

        time_buffer = self.grid['time']
        nb = info['nt_hydro_current'] % time_buffer.size

        self.time_check = time_buffer[nb[0]]* info['current_step_fractions'][0] + time_buffer[nb[1]]* info['current_step_fractions'][1]

    def close(self):
        self.A.close()

class dummy_msg_logger():
    def msg(self,text, warning=None, hint=None):
        print(text)


def connect_to_shared_memory(sm_builder, shared_refs):
    sm_name = sm_builder['shared_mem_name']
    shared_refs[sm_name] = shared_memory.SharedMemory(sm_name, create=False) # maintains a reference
    data= np.ndarray(sm_builder['shape'], dtype=sm_builder['dtype'], buffer=shared_refs[sm_name].buf,
                            order=sm_builder['order'])
    return data


class ControlAsyc():
    # get and set contol shared control variables in 4 elebel interg array
    def __init__(self,control_array):
        self._control_array = control_array
        self._control_flag = control_array[:1]
        self._nt_hydro_current= control_array[1:2]
        self._nt_buffer_start = control_array[2:3]
        self._nt_buffer_end = control_array[3:4]
        self._number_steps_in_buffer = control_array[4:5]



    def set_current_hydro_step(self,nt):self._nt_hydro_current[0] = nt
    def get_current_hydro_step(self): return self._nt_hydro_current[0]

    def is_hydro_step_in_buffer(self,nt, model_dir= 1):
        # check in current and next hydro time steps are in buffer
        r =  nt >= self._nt_buffer_start[0] and nt+1 < self._nt_buffer_end[0]
        return r

    def inc_buffer(self, n=1):
        self._nt_buffer_start[0] +=n
        self._nt_buffer_end[0] += n

    def set_buffer_start(self, nt): self._nt_buffer_start[0] = nt
    def get_buffer_start(self): return self._nt_buffer_start[0]

    def set_buffer_end(self, nt): self._nt_buffer_end[0] = nt
    def get_buffer_end(self): return self._nt_buffer_end[0]

    def set_steps_in_buffer(self, nt): self._number_steps_in_buffer[0] = nt
    def get_steps_in_buffer(self): return self._number_steps_in_buffer[0]

    # these contol the async reader actions
    def start_async_running(self): self._control_flag[0] = 10
    def is_async_running(self): return self._control_flag[0] == 10

    def end(self): self._control_flag[0] = -10
    def has_ended(self): return self._control_flag[0] == -10
    def has_started(self): return self._control_flag[0] != 0

    def buffer_state(self):
        s = f'buffer start {self._nt_buffer_start[0]}, current step {self._nt_hydro_current[0]}, buffer end {self._nt_buffer_end[0]} '
        return s

if __name__ == '__main__':
    dt = 3600
    ml = dummy_msg_logger()
    F = FieldGroupManger()
    F.shared_info.msg_logger= ml
    F.params = merge_params_with_defaults(F.params, F.default_params, ml)


    F.initial_setup()
    F.shared_info = dict(model_time_step=dt, back_trackin=False)

    times= np.arange(F.reader.info['hydro_model_time_range'][0], F.reader.info['hydro_model_time_range'][1],dt)
    time_check= np.full_like(times,np.nan)
    for nt, time in enumerate(times[:-2]):
        F.update(time) # fill buffer if possible
        F.interp_fields()

        # mimic computation effort

        sleep(1)
        time_check[nt] = F.time_check
        ml.msg(f'Solver> completed step {nt}')

        pass
    F.close()


    print('max_time check diff',np.nanmax(times-time_check))
    print(time_check)

