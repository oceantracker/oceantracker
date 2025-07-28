# reads rectangular or flat output into buffer, reads whole file
from  oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from os import path
from oceantracker.util.numba_util import njitOT


def read_comp_tracks_file(file_name_or_list, file_dir=None, var_list=None, file_number=None, fraction_to_read=None):
    # release group is 1 based

    file_list = [file_name_or_list] if type(file_name_or_list) == str else file_name_or_list

    if file_dir is not None: file_list = [path.join(file_dir,fn) for fn in file_list]
    if file_number is not None: file_list = [file_list[file_number]] # take one file only

    #  mege files in list
    time_steps = 0
    for n, fn in enumerate(file_list):
        if n ==0:
            data= _read_one_track_file(fn, var_list)
        else:
            # append
            data1 = _read_one_track_file(fn, var_list)
            for name, val in data.items():
                if name in data['variable_info']:
                    vi = data['variable_info'][name]
                    if any( [ s in vi['dims'] for s in ['time_particle_dim', 'particle_dim' , 'time_dim']]):
                        data[name] = np.concatenate((data[name],data1[name]), axis=0)

    d = _unpack_compact_tracks(data)

    if d['x'].shape[2] == 3: d['z'] = d['x'][:,:,2] # make a z variable if 3D

    if fraction_to_read is not None:
        # get random fraction as subset of all particles
        sel_particles = np.sort(np.random.randint(0,high=d['x'].shape[1] - 1, size=int(np.ceil(d['x'].shape[1] * fraction_to_read))))
        n0 = d['x'].shape[1] # original number of particles
        for key, item in d.items():
            if isinstance(item, np.ndarray):
                if item.shape[0]==n0:
                    d[key]= item[sel_particles,...]
                if len(item.shape) > 1 and item.shape[1] == n0:
                    d[key] = item[:, sel_particles, ...]

    return d

def _read_one_track_file(file_name, var_list):

    nc = NetCDFhandler(file_name, mode='r')

    if var_list is  None:
        var_list = nc.var_names()
    else:
        # get list plus min data set
        var_list = list(set(['write_step_index','ID','particle_ID', 'x', 'time', 'status', 'IDrelease_group',
                             'IDpulse', 'x0', 'dry_cell_index', 'num_part_released_so_far']
                                + var_list))

    data = nc.read_variables(var_list)
    data['variable_info']  = nc.variable_info
    data['global_attributes']=nc.attrs()
    data['dimensions'] = nc.dims()

    nc.close()

    return data

def _unpack_compact_tracks(data):
    # read compact file with stream of values  with given in timestep and particle ID in time_particle dimension

    attributes = data['global_attributes']
    variable_info= data['variable_info']

    d = dict(dimensions=dict())


    particle_IDs = data['particle_ID'] # this is time_particle particleID to allow unpacking

    time_steps_written= data['time'].size

    n_time_step =  data['write_step_index'] - data['write_step_index'][0]
    part_offset =  particle_IDs -  particle_IDs[0]
    num_released = part_offset[-1] + 1
    # todo status is special as last value for each particle when it is alive is needed to continue after death???
    # '_FillValue'
    d['status'] =  np.full((time_steps_written, num_released), attributes['status_notReleased'], dtype=variable_info['status']['dtype'])
    _insertMatrixValues(d['status'], n_time_step, part_offset, data['status'])
    last_recordedID = _get_last_alive(d['status'], attributes['status_notReleased'], attributes['status_dead'])

    # don't reprocess status, and don't process others, not needed in rectangular format
    var_list = list(data.keys())

    for v in ['status','write_step_index','variable_attributes','variable_info','dimensions', 'global_attributes']:
        if v in var_list: var_list.remove(v)

    for name in set(var_list): # only do unique vars
        vi = variable_info[name]
        if 'time_particle_dim' in vi['dims']:
            # compact time varying variablesF
            s = vi['shape']
            d[name] = np.full((time_steps_written, num_released) + tuple(s[1:]),
                               vi['attrs']['_FillValue'], dtype=vi['dtype'])

            _insertMatrixValues(d[name], n_time_step, part_offset, data[name])
            _filIinDeadParticles(d[name], last_recordedID, vi['attrs']['_FillValue'])

        elif  'particle_dim' in vi['dims']:
            d[name] =data[name][:num_released,...]

        else:
            # non time_particle varying parameters, eg time
            d[name] = data[name]

        d['dimensions'][name] = vi['dims']
        if d['dimensions'][name][0] == 'time_particle':
            # output wil be retangular so correct dim
            d['dimensions'][name] = ['time', 'particle'] + d['dimensions'][name][1:]

    return d

@njitOT
def _insertMatrixValues(x,row,col,values):
    for n in range(values.shape[0]):
        x[row[n],col[n],...] = values[n]
@njitOT
def _get_last_alive(status,status_notReleased, status_dead):
    # return last row/time when each  particle is alive
    ID = np.zeros((status.shape[1],),dtype=np.int32)
    for n in range(status.shape[1]):
        # from last time/row look up for first status >=
        nrow = status.shape[0]-1 # start in last row
        while nrow >= 0:
            # look for matrix fill value of status_notReleased
            # this will keep all statuses but status_notReleased, including bad cord etc
            if status[nrow, n] != status_notReleased:
                break

            status[nrow, n] = status_dead  # mark dead
            nrow -= 1

        ID[n]= nrow # need to use as start of  range
    return ID

@njitOT
def _filIinDeadParticles(data, last_recordedID, missing_status):
    # fill in values after death with last good one
    for n in range(data.shape[1]):
        n_last_write= last_recordedID[n]
        # fill in dead values below last recorded with last recorded value
        for nrow in range(n_last_write+1,data.shape[0]):
            data[nrow, n, ...] =  data[n_last_write, n, ...]



