import numpy as np
from oceantracker.reader.SCHISM_reader import SCHISMreaderNCDF
from os import path ,walk
from glob import glob
from oceantracker.util import class_importer_util, basic_util
from oceantracker.shared_info import shared_info as si
from oceantracker.util.message_logger import MessageLogger
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
    def build_catalog(self, input_dir, time_variable, file_mask='*.nc', msg_logger=None, crumbs=''):
        t0 = perf_counter()
        self.msg_logger= msg_logger
        self.crumbs= crumbs +'OceanTrackerDataSet> '


        mask = path.join(input_dir,'**', file_mask) # add subdir search

        file_names= glob(mask, recursive=True)
        if len(file_names)==0:
            msg_logger.msg(f'No files found in input_dir, or its sub-dirs matching mask "{file_mask}"',
                           hint=f'searching with "gob" mask "{mask}"', fatal_error = True,exit_now=True)
        msg_logger.msg(f'Cataloging hindcast with {len(file_names)} files in dir {input_dir}')

        self.catalog = dict(info=dict(input_dir=path.normpath(input_dir),file_mask=file_mask),
                            file_info=[], variables={})
        cat = self.catalog
        info = cat['info']
        self._unpack_variables(file_names, time_variable)
        self._time_sort_variable_fileIDs()
        self._make_time_step_to_fileID_map()

        # special case, set up time to be read,
        # as same time may be in multiple files, if variables split among files
        v_name = next(name for name, i in cat['variables'].items() if i['has_time'])  # first variable with time
        time = cat['variables'][v_name]['global_time_step_check']
        cat['ref_time'] = time

        vi = deepcopy(cat['variables'][v_name])
        vi.update(dims=info['time_dim'], shape=( time .size,), dtype=time.dtype )
        cat['variables'][info['time_variable']] = vi

        # set up statr ends times
        i = cat['info']
        i['start_date'], i['end_date'] = time[0], time[-1]
        i['start_time'], i['end_time'] = float(time[0])/1e9, float(time[-1])/1e9
        i['duration'] = i['end_time'] - i['start_time']
        i['total_time_steps'] = time.size
        i['time_step'] = i['duration']/(time.size-1)

        self._check_time_consistency()
        return self.get_catalog()

    def build_dataset_from_catalog(self,catalog):
        self.catalog = catalog
        self.variables = self.catalog['variables']

    def time_steps_available(self, nt):
        # which of  time steps are in the data set
        # used to calculate buffer index
        cat = self.catalog
        sel =  np.logical_and( nt >= 0, nt < cat['ref_time'].size)
        nt_available = nt[sel]
        return nt_available

    def read_variable(self, file_var_name: str, nt=None):
        # read simple variable
        cat = self.catalog
        vi = cat['variables'][file_var_name]
        if vi['has_time']:
            out = self._read_time_varying_variable(file_var_name, nt)
        else:
            out = self._read_non_time_varying_variable(file_var_name)
        return out

    def _read_non_time_varying_variable(self, file_var_name: str):
        cat = self.catalog
        vi = cat['variables'][file_var_name]
        fi = cat['file_info'][vi['fileID']]

        ds = self._open_file(fi['name'])
        out = ds[file_var_name].compute()
        return out

    def _read_time_varying_variable(self,file_var_name:str, nt):
        # get data at "nt" model integer time steps

        cat = self.catalog
        info = cat['info']
        vi = cat['variables'][file_var_name]
        time_dim =info['time_dim']

        if nt is None: nt = np.zeros((1,),dtype=np.int32)
        nt = np.asarray(nt)
        nt_required = nt.copy()

        # clip to full range
        nt_required = nt_required[ np.logical_and( nt_required >= 0, nt_required < cat['ref_time'].size)]
        files_read = 0
        while nt_required.size > 0 :
            file_no = vi['time_step_to_fileID_map'][nt_required[0]]
            fi = cat['file_info'][file_no]

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
        ds =xr.open_dataset(file_name )
        return ds

    def _unpack_variables(self, file_names, time_variable):
        # find variables
        t0= perf_counter()
        tlast=perf_counter()
        cat = self.catalog
        info = cat['info']
        info['time_variable'] = time_variable
        info['time_dim'] = None
        ml = self.msg_logger
        info['dims']= {}
        info['attrs'] = {}
        for fileID, fn in enumerate(file_names):
            fi = dict(name=fn, ID=fileID, has_time=False)
            ds = self._open_file(fi['name'])
            # add time info if present
            if time_variable in ds.variables:
                info['time_dim'] = ds[time_variable].dims[0]
                info['time_dtype'] = ds[time_variable].dtype
                fi['has_time'] = True
                time = ds.variables[info['time_variable']].data
                fi['time'] = time
                fi['start_time'] = time[0]
                fi['end_time'] = time[-1]
                fi['time_steps'] = time.size

            for key, d in ds.sizes.items(): info['dims'][key] = d
            for key, d in ds.attrs.items(): info['attrs'][key] = d
            cat['file_info'].append(fi)

            # get variable data
            for v_name in ds.variables:
                if v_name == info['time_variable']: continue
                data = ds[v_name]
                # add to variables
                if v_name not in cat['variables']:  # make new variable
                    cat['variables'][v_name] = dict(fileID=[])
                cat['variables'][v_name]['fileID'].append(fileID)
                cat['variables'][v_name]['dims'] = data.dims
                cat['variables'][v_name]['attrs'] = data.attrs
                cat['variables'][v_name]['encoding'] = data.encoding
                cat['variables'][v_name]['dtype'] = data.dtype
                cat['variables'][v_name]['shape'] = data.shape
                cat['variables'][v_name]['has_time'] = info['time_dim'] in data.dims

            ds.close()
            if  perf_counter()-tlast > 30:
                s = path.dirname(fn) + '\\' + path.basename(fn)
                ml.progress_marker(f'Cataloging hindcast file # {fileID} of {len(file_names)}, '
                                        f'name="{s}"',start_time=t0)
                tlast = perf_counter()

        if info['time_dim'] is None or 'units'  not in ds.variables[info['time_variable']].encoding:
            ml.msg(f'X=xarray could not identify time variable index in file ={fn}',
                   fatal_error=True,exit_now=True, crumbs= self.crumbs,
                   hint='Hindcast file does not have time variable with "units" attribute meeting CF convention, eg. "seconds since 2017-01-01 00:00:00 +0000"  ')
    def _time_sort_variable_fileIDs(self):
        # sort variable fileIDs by time, now all files are read
        cat = self.catalog
        for v_name, item in cat['variables'].items():
            if item['has_time']:
                item['fileID'] = np.asarray(item['fileID'])
                start_times = np.asarray([cat['file_info'][x]['start_time'] for x in item['fileID']])
                file_order = np.argsort(start_times)
                item['fileID'] = item['fileID'][file_order]
                # get first time step in the file
                time_steps = np.asarray([cat['file_info'][x]['time_steps'] for x in item['fileID']])
                first_time_step_in_file = np.cumsum(time_steps) - time_steps[0]
                # insert first time step into the file info in time order
                # this will be unnecessarily  repeated, if more than one variable in a file
                for n, fID in enumerate(item['fileID']):
                    cat['file_info'][fID]['first_time_step_in_file'] = first_time_step_in_file[n]
            else:
                item['fileID'] = item['fileID'][0]

        pass
    def _make_time_step_to_fileID_map(self):

        # make time step to fileID map, accounting for file order
        cat = self.catalog
        info = cat['info']
        for v_name, item in cat['variables'].items():
            if item['has_time']:
                time_step_file_map = np.zeros((0,),dtype=np.int32)
                global_time_check = np.zeros((0,),dtype=info['time_dtype'])
                for fileID in  item['fileID']: #IDs have aleady been time sorted
                    fi = cat['file_info'][fileID]
                    time_step_file_map =  np.append(time_step_file_map,fi['ID']*np.ones(( fi['time_steps'] ,), dtype=np.int32))
                    times = fi['time']
                    global_time_check  = np.append(global_time_check, times)
                item['time_step_to_fileID_map'] = np.asarray(time_step_file_map, dtype=np.int32)
                item['global_time_step_check'] = global_time_check
        pass
    def _check_time_consistency(self):
        # check all variables have same time_step_to_fileID_map, and save one version of it
        cat = self.catalog
        ml = self.msg_logger


        starts = []
        n_files=[]
        ref_time = None
        vars=[]

        for v_name, item in cat['variables'].items():

            if item['has_time']:
                starts.append(item['global_time_step_check'][0])
                n_files.append(len(item['fileID']))
                vars.append(v_name)
                item.pop('global_time_step_check') # discard times
                vars.append(v_name)
        # checks on hindcasts with variables in different files
        # check if difernt number of files for any variable
        sel = np.flatnonzero( np.abs(np.diff(np.asarray(n_files)) ) > 0)
        if sel.size>0:
            ml.msg('File numbers differ for some variables for hindcast where variables are in separate n files',fatal_error=True,
                             hint=f'look for missing file variables- {str([vars[x] for x in sel])}, {[vars[x+1] for x in sel]}')
        # check if all variables start at the same times
        starts = np.asarray(starts).astype(np.float64)
        sel = np.flatnonzero( np.abs(np.diff(starts)))
        if sel.size > 0:
            ml.msg('Start times differ for some variables for hindcast where files are split between files',fatal_error=True,
                            hint=f'look for missing file variables- {str([vars[x] for x in sel])}, {[vars[x+1] for x in sel]}')

        # for all check missing time steps
        t =cat['ref_time'].astype('datetime64[s]').astype(np.float64)
        sel = np.flatnonzero(np.abs(np.diff(t)) > 4*cat['info']['time_step'])
        if sel.size > 0:
            ml.msg('There are gaps in hindcast times larger than 4 time steps',warning=True,
                            hint= f'there may be missing hindcast files, look at dates around {[ str(x) for x in cat["ref_time"][sel]]}')

    def get_time_step(self,time, backtracking):

        #round down/up to time step for forward backwards
        info = self.catalog['info']
        nt = (info['total_time_steps']-1)*abs(time-info['start_time'])/abs(info['end_time']-info['start_time'])
        nt = np.ceil(nt) if backtracking else np.floor(nt)
        return int(nt)

    def get_catalog(self): return self.catalog

if __name__ == "__main__":
    # dev testing code
    input_dir = r'G:\Hindcasts_large\2020_MalbroughSounds_10year_benPhD\\2008\schism_marl2008010*.nc'
    input_dir = r'G:\Hindcasts_large\2020_MalbroughSounds_10year_benPhD\\2008\schism_marl2008010*.nc'
    input_dir = r'F:\Hindcasts\2017_PortPeg2017HincastFull\PortPegHindcastCurrents\*.nc'
    input_dir = r'F:\Hindcast_reader_tests\Schimsv5\WHOI_calvin\SCHISM_v2\*.nc'
    input_dir = r'G:\Hindcasts_large\2024_hauraki_gulf_auck_uni\2020'
    # mask= r'F:\Hindcasts\2022_PortPhillipBay2020\HUY2020\schism\*.nc'

    n=1

    file_mask='*.nc'
    time_var = 'time'
    match n:
        case 0:
            input_dir = r'G:\Hindcasts_large\2024_hauraki_gulf_auck_uni\2020'
            #sel = np.arange(12, 12+24, dtype=np.int32)
            sel = np.arange(0, 24, dtype=np.int32)
        case 1:
            input_dir = r'F:\Hindcast_reader_tests\Schimsv5\WHOI_calvin\SCHISM_v5'
            sel = np.arange(0, 24, dtype=np.int32)
        case 2:
            input_dir = r'G:\Hindcasts_large\2024_OceanNumNZ-2022-06-20\final_version'
            sel = np.arange(23, 46, dtype=np.int32)
        case 3:
            input_dir =   r'F:\Hindcast_reader_tests\ROMS_samples'
            sel = np.arange(0, 46, dtype=np.int32)
            file_mask='DopAnV2R3*.nc'

    ds = OceanTrackerDataSet()
    ds.build_catalog(input_dir,time_var, file_mask=file_mask, msg_logger=si.msg_logger)



    t0 = perf_counter()
    time= ds.catalog['info']['start_time'] + 7190
    print('time step',ds.get_time_step(time,False))
    data= {}
    for name in ds.catalog['variables'].keys():
        t1=perf_counter()
        data[name] = ds.read_variable(name, nt=sel)

    print('read vars', perf_counter()-t0)
    print('info', ds.catalog['info'])
    pass











