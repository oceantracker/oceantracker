from oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from copy import  deepcopy
from os import path
def read_rect_tracks_file(file_name, var_list=None, fraction_to_read=None):
    # read rectangluar  format
    print(f'\t Reading rectangular track file "{path.basename(file_name)}"')
    nc = NetCDFhandler(file_name, mode='r')
    if var_list is None:
        var_list = list(nc.variable_info.keys())
    else:
        # get list plus min data set
        var_list = list(set(['x', 'time', 'status', 'x0', 'dry_cell_index'] + var_list))

    data = nc.read_variables(var_list)
    data['global_attributes'] = nc.attrs()
    data['dimensions'] = nc.dims()
    data['variables'] = dict()
    for v in var_list:
        data['variables'][v] = dict(nc.variable_info[v])
        data['variables'][v]['data'] = data[v]

    return data

def merge_rect_track_files(file_list,  var_list=None,fraction_to_read=None):
    n_times = []
    for fn in file_list:
        nc = NetCDFhandler(fn, mode='r')
        lastID = nc.read_variable('ID', -1)
        n_times.append(nc.variable_info['time']['shape'][0])
        nc.close()

    total_time_steps = sum(n_times)
    first_time_step = np.cumsum(np.asarray([0] + n_times))
    result = dict()

    for n_file, fn in enumerate(file_list):
        d1 = read_rect_tracks_file(fn, var_list=var_list)
        ID = d1['ID']
        sel = np.flatnonzero(ID >= 0)
        for name in d1['variables'].keys():

            v = d1['variables'][name]
            if name not in result:
                # make space for all files in results, add empty variables
                dims = deepcopy(v['sizes'])
                if 'time_dim' in dims: dims['time_dim'] = total_time_steps
                if 'particle_dim' in dims:  dims['particle_dim'] = lastID + 1
                s = [m for m in dims.values()]
                result[name] = np.full(s, v['attrs']['_FillValue'], dtype=v['dtype'])

            r = [int(first_time_step[n_file]), int(first_time_step[n_file + 1])]
            # insert file data into matrix
            if 'particle_dim' in v['dims'] and 'time_dim' in v['dims']:
                result[name][r[0]:r[1], ID[sel], ...] = v['data'][:, sel, ...]

            elif 'particle_dim' in v['dims']:
                result[name][ID[sel], ...] = v['data'][sel, ...]

            elif 'time_dim' in v['dims']:
                result[name][r[0]:r[1], ...] = v['data']

    return result