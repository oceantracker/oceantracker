import numpy as np
from os import path ,walk
from glob import glob
from oceantracker.shared_info import shared_info as si
import xarray as xr
from time import perf_counter
from copy import  copy, deepcopy
from oceantracker.util import  time_util
class OceanTrackerDataSet(object):
    '''
    Class to wrap whole set of files into single time series like xarray
    copes with variables being help in different files
    assumes - all files with variables with t time dimension hane
            - assume time variable has units atrbute which enables x array to convert to datetime64
    '''
    def __init__(self, reader_params):

        # get the file_list
        # check files are there
        mask = path.join(reader_params['input_dir'], '**', reader_params['file_mask'])  # add subdir search
        file_list = glob(mask, recursive=True)
        if len(file_list) == 0:
            si.msg_logger.msg(f'No files found in input_dir, or its sub-dirs matching mask "{mask}"',
                              hint=f'searching with "gob" mask "{mask}"', fatal_error=True)

        self.info = dict(input_dir= reader_params['input_dir'], file_mask=reader_params['file_mask'],
                        variables={}, files=[], dims={}, attributes={})
        info = self.info
        vars = info['variables']

        for fileID, fn in enumerate(file_list):
            ds = xr.open_dataset(fn, decode_times=False)
            info['dims'].update(dict(ds.sizes)) # all dims found

            info['files'].append(dict(name=fn,start_time=None,
                            variables= list(ds.variables.keys()),
                            dims = dict(ds.sizes))) # to see if dims the same
            for name, var in ds.variables.items():
                if name not in vars:
                    vars[name] = dict( dims={key:ds.sizes[key]  for key in var.dims},
                                       fileIDs=[], attrs = var.attrs,
                                       #encoding = var.encoding,
                                       shape= copy(var.shape),
                                       dtype = var.dtype)

                info['variables'][name]['fileIDs'].append(fileID)
            info['attributes'].update(ds.attrs)

        self.info['variables'] = vars

    def time_steps_available(self, nt):
        # which of  time steps are in the data set
        # used to calculate buffer index
        sel =  np.logical_and( nt >= 0, nt < self.info['time_coord'].size)
        nt_available = nt[sel]
        return nt_available

    def read_data(self, file_var_name: str, nt=None):
        return self.read_variable(file_var_name, nt=nt).data
    def read_variable(self, file_var_name: str, nt=None):

        # read simple variable
        info = self.info
        vi = info['variables'][file_var_name]
        if vi['time_varying']:
            out = self._read_time_varying_variable(file_var_name, nt)
        else:
            out = self._read_non_time_varying_variable(file_var_name)
        return out

    def _read_non_time_varying_variable(self, file_var_name: str):
        info = self.info
        vi = info['variables'][file_var_name]
        fi = info['files'][vi['fileIDs']]

        ds = self._open_file(fi['name'])
        out = ds[file_var_name].compute()
        return out

    def _read_time_varying_variable(self,file_var_name:str, nt):
        # get data at "nt" model integer time steps

        info = self.info
        vi = info['variables'][file_var_name]

        time_dim =info['time_dim']

        if nt is None: nt = np.arange(vi['dims'][time_dim],dtype=np.int32)

        nt = np.asarray(nt)
        nt_required = nt.copy()

        # clip to full range
        nt_required = nt_required[ np.logical_and( nt_required >= 0, nt_required < info['time_coord'].size)]

        files_read = 0
        while nt_required.size > 0 :
            file_no = vi['time_step_to_fileID_map'][nt_required[0]]
            fi = info['files'][file_no]

            # required time steps in this file
            nt0 = fi['first_time_step_in_file']
            sel = np.logical_and( nt_required >= nt0, nt_required < nt0 + fi['time_steps'])
            nt_available = nt_required[sel]

            # get mapped file offsets
            file_offsets = vi['time_step_to_file_offset_map'][nt_available]

            # open file and read
            ds = self._open_file(fi['name'])
            if files_read == 0:
                # first files time step
                out = ds[file_var_name][{time_dim: file_offsets}].compute()
            else:
                # next files time steps
                try:
                    out = xr.concat((out,ds[file_var_name][{time_dim: file_offsets}].compute()), dim=time_dim)
                except Exception as e:
                    print('xx',fi['name'],file_var_name,nt,  nt_required,nt_available)
                    raise (e)
            ds.close()
            nt_required = nt_required[nt_available.size:]
            files_read += 1

        return out # return numpy array at  found time steps

    def _open_file(self, file_name):
        try:
            ds = xr.open_dataset(file_name, decode_times=False)
        except Exception as e:
            raise (e)
        return ds


    def get_time_step(self,time, backtracking):
        #round down/up to time step for forward/backwards
        info = self.info
        nt = (info['total_time_steps']-1)*abs(time-info['start_time'])/abs(info['end_time']-info['start_time'])
        nt = np.ceil(nt) if backtracking else np.floor(nt)
        return int(nt)














