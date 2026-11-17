# fror mal files in sub folder of readers input dir, and file mask, build a list of file info
# and gets a time variable for each based

from os import path
from copy import deepcopy, copy
from glob import glob

import numpy as np
import xarray as xr


from oceantracker.shared_info import shared_info as si
from oceantracker import definitions

def build_hindcast_info(users_reader_params):
    # make list of files with a dict of variables and time values


    file_list = _get_file_list(users_reader_params)
    time_vars = _get_possible_time_variable_names(users_reader_params)

    file_info =  _get_file_info(file_list, time_vars)
    var_info, dims_info = _get_var_dim_info(file_info)

    return file_info, var_info, dims_info


def _get_file_list(reader_params):
    ml = si.msg_logger

    # check params and folders exists
    if 'input_dir' not in reader_params or 'file_mask' not in reader_params:
        ml.msg('Reader class requires settings, "input_dir" and "file_mask" to read the hindcast',
               fatal_error=True)
    # check input dir exists
    if not path.isdir(reader_params['input_dir']):
        ml.msg(f'Could not find input dir "{reader_params["input_dir"]}"',
               hint='Check reader parameter "input_dir"', fatal_error=True)

    mask = path.join(reader_params['input_dir'], '**', reader_params['file_mask'])  # add subdir search
    file_list = glob(mask, recursive=True)
    if len(file_list) == 0:
        si.msg_logger.msg(f'No files found in input_dir, or its sub-dirs matching mask "{mask}"',
                          hint=f'searching with "gob" mask "{mask}"', fatal_error=True)

    ml.progress_marker(f'Found {len(file_list)} files in dir and sub-dirs of "{reader_params["input_dir"]}"')

    return file_list

def _get_possible_time_variable_names(user_reader_params):
    # get list of all possible time variables  to enable it to be read in single
    # pass of all files in the hindcast, before exact hindcast format type may be known

    ml = si.msg_logger

    # get user supplied time var if they havr give it
    if ('grid_variable_map' in user_reader_params and
        'time' in user_reader_params['grid_variable_map'] and
        user_reader_params['grid_variable_map']['time'] is not None
        ) :
        time_vars = user_reader_params['grid_variable_map']['time']
        return time_vars if type(time_vars)==list else [time_vars] # ensure a list is retuned

    if 'class_name' in user_reader_params:
        ml.progress_marker(f'Using given reader parameter class_name = "{user_reader_params["class_name"]}"')
        readers_to_check = dict(user_named_reader=user_reader_params[ 'class_name'] )
    else:
        # look for reader amongst known readers
        readers_to_check = definitions.known_readers
    pass

    # from readers get list of default time variable names
    time_vars=[]
    for name, class_name in readers_to_check.items():
        reader_params = dict(deepcopy(user_reader_params),class_name=class_name)   # work on a copy to be safe
        reader_params['class_name'] = class_name
        # loo class and merge params to get time variable
        i = si.class_importer.make_class_instance_from_params('reader', reader_params, initialize=False, merge_params=False)
        tv = i.default_params['grid_variable_map']['time'].get_default()
        if type(tv) ==list:
            time_vars.extend(tv)
        else:
            time_vars.append(tv)

    return list(set(time_vars)) # make list unique

def _get_file_info(file_list, time_vars):
    # build a list of dict containing file variable info and time values

    file_info =[]

    for fileID, fn in enumerate(file_list):
        ds = xr.open_dataset(fn, decode_times=False)
        fi = dict(ID = fileID, name = fn , attrs = {key:ds.attrs[key]  for key in ds.attrs},
                  dims={key:ds.sizes[key]  for key in ds.sizes}, variables=dict())

        for name, var in ds.variables.items():
            fi['variables'][name] = dict(
                                    dims={key:var.sizes[key]  for key in var.dims},
                                    attrs = {key:var.attrs[key] for key in var.attrs},
                                    shape= copy(var.shape),
                                    dtype = var.dtype, #encoding = var.encoding,
                                    )
        tv = list(set(time_vars) & set(list(ds.variables))) # find variables in possible time variables
        if len(tv)== 1:
            fi['time'] = ds.variables[tv[0]] # copy time data
        elif len(tv) > 1:
            si.msg_logger.msg(f'Found more than one of possible time variables in a file, found variables f{str(tv)}', error=True,
                              hint= 'Rebuild hindcast with only one time variable per file?')
        else:
            fi['time'] = None

        ds.close()

        file_info.append(fi)

    return file_info

def _get_var_dim_info(file_list):
    var_info = {}
    dim_info={}
    for fileID, fi in enumerate(file_list):
        for name, vi in fi['variables'].items():
            if name not in var_info:
                var_info[name] = dict(fi['variables'][name], fileIDs=[])  # get dims etc based og first occurrence

            var_info[name]['fileIDs'].append(fileID)  # build list of file IDs for each variable, not in time order
            dim_info.update(fi['dims'])


    # convert fileIDs to array to allow time sorting
    for name, vi in var_info.items():
        vi['fileIDs'] = np.asarray(vi['fileIDs']).astype(np.int32)

    return var_info, dim_info