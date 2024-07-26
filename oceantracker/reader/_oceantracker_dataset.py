import numpy as np
from oceantracker.reader.schism_reader import SCHISMreaderNCDF
from os import path ,walk
from glob import glob
from oceantracker.util import class_importer_util, basic_util
from oceantracker.shared_info import SharedInfo as si
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
    def __init__(self, input_dir, file_mask='*.nc',msg_logger=None):
        t0 = perf_counter()
        self.info =dict()
        self.msg_logger= msg_logger

        mask = path.join(input_dir,'**', file_mask) # add subdir search

        file_names= glob(mask, recursive=True)
        msg_logger.msg(f'Cataloging hindcast with {len(file_names)} files in dir {input_dir}')

        self.catalog = dict(input_dir=path.normpath(input_dir), file_info=[], variables={})
        cat = self.catalog

        self._unpack_variables(file_names)
        self._time_sort_variable_fileIDs()
        self._make_time_step_to_fileID_map()


        # special case, set up time to be read,
        # as same time may be in multiple files, if variables split among files
        v_name = next(name for name, i in cat['variables'].items() if i['has_time'])  # first variable with time
        time = cat['variables'][v_name]['global_time_step_check']
        cat['ref_time'] = time

        vi = deepcopy(cat['variables'][v_name])
        vi.update(dims=cat['time_dim'], shape=( time .size,), dtype=time.dtype )
        cat['variables'][cat['time_var']] = vi

        # set up statr ens times
        i = self.info
        i['start_date'], i['end_date'] = time[0], time[-1]
        i['start_time'], i['end_time'] = float(time[0])/1e9, float(time[-1])/1e9
        i['duration'] = i['end_time'] - i['start_time']
        i['total_time_steps'] = time.size
        i['time_step'] = i['duration']/(time.size-1)

        self._check_time_consistency()


    def read_variable(self,file_var_name:str, nt=None):
        # get data at "nt" model time steps
        cat = self.catalog
        vi = cat['variables'][file_var_name]
        t0 = perf_counter()
        time_dim =cat['time_dim']

        if vi['has_time']:
            nt_required = nt.copy()
            nt_required = nt_required[ np.logical_and( nt_required >= 0, nt_required < cat['ref_time'].size)]
            n_file= 0
            while nt_required.size > 0 :
                file_no = vi['time_step_to_fileID_map'][nt_required[0]]
                fi = cat['file_info'][file_no]
                # required time steps in this file
                nt0 = vi['first_time_step_in_file'][n_file]
                sel = np.logical_and( nt_required >= nt0, nt_required < nt0 + fi['time_steps'])
                nt_available = nt_required[sel]
                # open file and read
                ds = self._open_file(fi['name'])

                nt_file = nt_available-nt0 # file offset

                if n_file ==0:
                    out  = ds[file_var_name][{time_dim: nt_file}].compute()
                else:
                    t0= perf_counter()
                    out = xr.concat((out,ds[file_var_name][{time_dim: nt_file}].compute()), dim=time_dim)

                ds.close()
                nt_required = nt_required[nt_available.size:]
                n_file += 1

        else:
            fi = cat['file_info'][vi['fileID']]
            ds =self._open_file(fi['name'])
            out = ds.variables[file_var_name].values
            ds.close()

        return out.data

    def _open_file(self, file_name):
        return xr.open_dataset(file_name)

    def _unpack_variables(self, file_names):
        # find variables
        t0= perf_counter()
        tlast=perf_counter()
        cat = self.catalog
        for fileID, fn in enumerate(file_names):
            fi = dict(name=fn, ID=fileID, has_time=False)
            ds = self._open_file(fi['name'])

            # get time variable from dataset indexes
            for name, v in ds.indexes.variables.items():
                if np.issubdtype(v.dtype, np.datetime64):
                    cat['time_var'] = name
                    cat['time_dim'] = v.dims[0]
                    cat['time_dtype'] = v.dtype
                    fi['has_time'] = True

            # add file times if in file
            if fi['has_time']:
                time = ds.variables[cat['time_var']].data
                fi['time'] = time
                fi['start_time'] = time[0]
                fi['end_time'] = time[-1]
                fi['time_steps'] = time.size
            cat['file_info'].append(fi)

            # get variable data
            for v_name in ds.variables:
                if v_name == cat['time_var']: continue
                data = ds[v_name]
                # add to variables
                if v_name not in cat['variables']:  # make new variable
                    cat['variables'][v_name] = dict(fileID=[])
                cat['variables'][v_name]['fileID'].append(fileID)
                cat['variables'][v_name]['dims'] = data.dims
                cat['variables'][v_name]['dtype'] = data.dtype
                cat['variables'][v_name]['shape'] = data.shape
                cat['variables'][v_name]['has_time'] = cat['time_dim'] in data.dims

            ds.close()
            if  perf_counter()-tlast > 30:
                self.msg_logger.progress_marker(f'Cataloging hindcast file # {fileID} of {len(file_names)}, '
                                                f'name="{fi["name"].split(cat["input_dir"])[-1]}"',start_time=t0)
                tlast = perf_counter()

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
                item['first_time_step_in_file']  = np.cumsum(time_steps)-time_steps[0]
            else:
                item['fileID'] = item['fileID'][0]
        pass
    def _open_file(self, file_name):
        return xr.open_dataset(file_name)
    def _make_time_step_to_fileID_map(self):

        # make time step to fileID map, accounting for file order
        cat = self.catalog
        for v_name, item in cat['variables'].items():
            if item['has_time']:
                time_step_file_map = np.zeros((0,),dtype=np.int32)
                global_time_check = np.zeros((0,),dtype=cat['time_dtype'])
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
            ml.msg('File numbers differ for some variables for hindcast where files split are between files',fatal_error=True,
                             hint=f'look for missing file variables- {str([vars[x] for x in sel])}, {[vars[x+1] for x in sel]}')
        # check if all variables start at the same times
        starts = np.asarray(starts).astype(np.float64)
        sel = np.flatnonzero( np.abs(np.diff(starts)))
        if sel.size > 0:
            ml.msg('Start times differ for some variables for hindcast where files are split between files',fatal_error=True,
                            hint=f'look for missing file variables- {str([vars[x] for x in sel])}, {[vars[x+1] for x in sel]}')

        # for all check missing time steps
        t =cat['ref_time'].astype('datetime64[s]').astype(np.float64)
        sel = np.flatnonzero(np.abs(np.diff(t)) > 4*self.info['time_step'])
        if sel.size > 0:
            ml.msg('There are gaps in hindcast times larger than 4 time steps',warning=True,
                            hint= f'there may be missing hindcast files, look at dates around {[ str(x) for x in cat["ref_time"][sel]]}')

    def get_time_step(self,time, backtracking=False):

        #round down/up to time step for forward backwards
        info = self.info
        nt = info['total_time_steps']*abs(time-info['start_time'])/abs(info['end_time']-info['start_time'])
        nt = np.ceil(nt) if backtracking else np.floor(nt)
        return int(nt)

    def get_catalog(self): return self.catalog()

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



    ds= OceanTrackerDataSet(input_dir, file_mask=file_mask,msg_logger=si.msg_logger)



    t0 = perf_counter()
    time= ds.info['start_time'] + 7190
    print('time step',ds.get_time_step(time,False))
    data= {}
    for name in ds.catalog['variables'].keys():
        t1=perf_counter()
        data[name] = ds.read_variable(name, nt=sel)

    print('read vars', perf_counter()-t0)
    print('info', ds.info)
    pass











