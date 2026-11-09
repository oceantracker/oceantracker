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
    Class to wrap whole set of files into single time series like xarray,
    that are in given dir or its sub dirs.
    Copes with variables being held in different files
    assumes - all files with variables with t time dimension have time in same file
    '''
    def __init__(self, file_list):

        self.catalog=dict(variables={},  dims={}, attributes={},
            file_info = [dict(name=  name) for name in  file_list])

    def build_catalog(self):
        cat=self.catalog
        vars = cat['variables']

        for fileID, fn in enumerate(cat['file_info']):
            ds = xr.open_dataset(fn['name'], decode_times=False)
            cat['dims'].update(dict(ds.sizes)) # all dims found

            for name, var in ds.variables.items():
                if name not in vars:
                    vars[name] = dict( dims={key:ds.sizes[key]  for key in var.dims},
                                       fileIDs=[], attrs = var.attrs,
                                       #encoding = var.encoding,
                                       shape= copy(var.shape),
                                       dtype = var.dtype)

                cat['variables'][name]['fileIDs'].append(fileID)
            cat['attributes'].update(ds.attrs)

    def time_steps_available(self, nt):
        # which of  time steps are in the data set
        # used to calculate buffer index
        sel =  np.logical_and( nt >= 0, nt < self.catalog['time_coord'].size)
        nt_available = nt[sel]
        return nt_available

    def read_data(self, file_var_name: str, nt=None):
        return self.read_variable(file_var_name, nt=nt).data
    def read_variable(self, file_var_name: str, nt=None):

        # read simple variable
        cat = self.catalog
        vi = cat['variables'][file_var_name]
        if vi['time_varying']:
            out = self._read_time_varying_variable(file_var_name, nt)
        else:
            out = self._read_non_time_varying_variable(file_var_name)
        return out

    def _read_non_time_varying_variable(self, file_var_name: str):
        cat = self.catalog
        vi = cat['variables'][file_var_name]
        fi = cat['file_info'][vi['fileIDs']]

        ds = self._open_file(fi['name'])
        out = ds[file_var_name].compute()
        return out

    def _read_time_varying_variable(self,file_var_name:str, nt):
        # get data at "nt" model integer time steps

        cat = self.catalog
        vi = cat['variables'][file_var_name]

        time_dim =cat['time_dim']

        if nt is None: nt = np.arange(vi['dims'][time_dim],dtype=np.int32)

        nt = np.asarray(nt)
        nt_required = nt.copy()

        # clip to full range
        nt_required = nt_required[ np.logical_and( nt_required >= 0, nt_required < cat['time_coord'].size)]

        if vi['time_step_to_fileID_map'].size != cat['time_coord'].size:
            raise ValueError(f'Variable "{file_var_name}" is only in some of the hindcast files, '
                             f'has {vi["time_step_to_fileID_map"].size} of {cat["time_coord"].size} time steps, cannot read it at hindcast time steps')

        files_read = 0
        while nt_required.size > 0 :
            file_no = vi['time_step_to_fileID_map'][nt_required[0]]
            fi = cat['file_info'][file_no]

            # required time steps in this file, from this variable's own time step to file map
            # (not the file's first_time_step_in_file, which is shared by all variables in the file)
            sel = vi['time_step_to_fileID_map'][nt_required] == file_no
            nt_available = nt_required[sel]
            if nt_available.size == 0:
                raise RuntimeError(f'No time steps of "{file_var_name}" found in file "{fi["name"]}", for hindcast time steps {nt_required}')

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
        cat = self.catalog
        nt = (cat['total_time_steps']-1)*abs(time-cat['start_time'])/abs(cat['end_time']-cat['start_time'])
        nt = np.ceil(nt) if backtracking else np.floor(nt)
        return int(nt)














