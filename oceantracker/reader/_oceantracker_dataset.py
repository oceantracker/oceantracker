import numpy as np
from os import path ,walk
from glob import glob
from oceantracker.shared_info import shared_info as si
import xarray as xr
from time import perf_counter
from copy import  copy, deepcopy

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
        vars = self.info['variables']

        for fileID, fn in enumerate(file_list):
            ds = xr.open_dataset(fn, decode_times=False)
            info['dims'].update(ds.sizes)
            info['files'].append(dict(name=fn,start_time=None))
            for name, var in ds.variables.items():
                if name not in vars:
                    vars[name] = dict( dims={key:ds.sizes[key]  for key in var.dims},
                                       fileIDs=[], attrs = var.attrs,
                                       #encoding = var.encoding,
                                       dtype = var.dtype)

                info['variables'][name]['fileIDs'].append(fileID)

        self.info['variables'] = vars



    def time_steps_available(self, nt):
        # which of  time steps are in the data set
        # used to calculate buffer index
        sel =  np.logical_and( nt >= 0, nt < self.info['ref_time'].size)
        nt_available = nt[sel]
        return nt_available

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

        if nt is None: nt = np.zeros((1,),dtype=np.int32)
        nt = np.asarray(nt)
        nt_required = nt.copy()

        # clip to full range
        nt_required = nt_required[ np.logical_and( nt_required >= 0, nt_required < info['ref_time'].size)]
        files_read = 0
        while nt_required.size > 0 :
            file_no = vi['time_step_to_fileID_map'][nt_required[0]]
            fi = info['files'][file_no]

            # required time steps in this file
            nt0 = fi['first_time_step_in_file']
            sel = np.logical_and( nt_required >= nt0, nt_required < nt0 + fi['time_steps'])
            nt_available = nt_required[sel]
            # open file and read
            ds = self._open_file(fi['name'])
            nt_file = nt_available-nt0 # file offset
            if files_read ==0:
                try:
                    out = ds[file_var_name][{time_dim: nt_file}].compute()
                except Exception:
                    pass
            else:
                # time invariant
                t0= perf_counter()
                out = xr.concat((out,ds[file_var_name][{time_dim: nt_file}].compute()), dim=time_dim)
            ds.close()
            nt_required = nt_required[nt_available.size:]
            files_read += 1

        # return numpy array and found time steps
        return out

    def _open_file(self, file_name):
        ds = xr.open_dataset(file_name, decode_times=False)
        return ds


    def _make_time_step_to_fileID_map(self):

        # make time step to fileID map, accounting for file order
        info = self.info
        for v_name, item in info['variables'].items():
            if item['time_varying']:
                time_step_file_map = np.zeros((0,),dtype=np.int32)
                for fileID in  item['fileIDs']: #IDs have aleady been time sorted
                    fi = info['files'][fileID]
                    time_step_file_map =  np.append(time_step_file_map,fi['ID']*np.ones(( fi['time_steps'] ,), dtype=np.int32))
                    times = fi['time']
                item['time_step_to_fileID_map'] = np.asarray(time_step_file_map, dtype=np.int32)
        pass
    def _check_time_consistency(self):
        # check all variables have same time_step_to_fileID_map, and save one version of it
        info= self.info
        ml = self.msg_logger


        starts = []
        n_files=[]
        ref_time = None
        vars=[]

        for v_name, item in info['variables'].items():

            if item['has_time']:
                starts.append(item['global_time_step_check'][0])
                n_files.append(len(item['fileIDs']))
                vars.append(v_name)
                item.pop('global_time_step_check') # discard times
                vars.append(v_name)
        # checks on hindcasts with variables in different files
        # check if difernt number of files for any variable
        sel = np.flatnonzero( np.abs(np.diff(np.asarray(n_files)) ) > 0)
        if sel.size>0:
            ml.msg('File numbers differ for some variables for hindcast where variables are in separate n files',error=True,
                             hint=f'look for missing file variables- {str([vars[x] for x in sel])}, {[vars[x+1] for x in sel]}')
        # check if all variables start at the same times
        starts = np.asarray(starts).astype(np.float64)
        sel = np.flatnonzero( np.abs(np.diff(starts)))
        if sel.size > 0:
            ml.msg('Start times differ for some variables for hindcast where files are split between files',error=True,
                            hint=f'look for missing file variables- {str([vars[x] for x in sel])}, {[vars[x+1] for x in sel]}')

        # for all check missing time steps
        t = info['ref_time'].astype('datetime64[s]').astype(np.float64)
        sel = np.flatnonzero(np.abs(np.diff(t)) > 4*info['time_step'])
        if sel.size > 0:
            ml.msg('There are gaps in hindcast times larger than 4 time steps',warning=True,
                            hint= f'there may be missing hindcast files, look at dates around {[ str(x) for x in cat["ref_time"][sel]]}')

    def get_time_step(self,time, backtracking):
        #round down/up to time step for forward/backwards
        info = self.info
        nt = (info['total_time_steps']-1)*abs(time-info['start_time'])/abs(info['end_time']-info['start_time'])
        nt = np.ceil(nt) if backtracking else np.floor(nt)
        return int(nt)














