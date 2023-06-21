# reads rectangular or flat output into buffer, reads whole file
from  oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from numba import njit

from oceantracker.util import json_util

def read_particle_tracks_file(file_name, var_list=None, release_group= None, fraction_to_read=None):
    # release group is 1 based
    nc = NetCDFhandler(file_name, mode='r')

    if var_list is  None:
        working_var_list = nc.all_var_names()
    else:
        # get list plus min data set
        var_list = list(set(['x', 'time', 'status', 'IDrelease_group', 'IDpulse', 'x0', 'dry_cell_index', 'num_part_released_so_far'] + var_list))
        # trim list to variables in the file
        working_var_list= []
        for var in var_list:
            if var not in nc.all_var_names():
                print('Warning: read_particle_tracks_file, particle property variable not in track file ' + var)
            elif var not in working_var_list:
                working_var_list.append(var)

    if nc.is_dim( 'time_particle_dim'):
        d=  _read_compact_tracks(nc,working_var_list,release_group)
    else:
        d= _read_rectangular_tracks(nc, working_var_list,release_group)

    d.update(_get_release_group_map_and_points(nc))

    nc.close()

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

def _read_rectangular_tracks(nc,var_list, release_group):
    # read rectangular output file, dim time and particle
    num_released= nc.global_attr('total_num_particles_released')
    rg = nc.read_a_variable('IDrelease_group')[:num_released]
    d = {'dimensions': {}, 'total_num_particles_released' :num_released }
    for var in set(var_list):
        dims= nc.all_var_dims(var)
        if 'particle' in dims and 'time' in dims:
            d[var] = nc.read_a_variable(var)[:, :num_released, ...]
            if release_group is not None: d[var] = d[var][:, rg == release_group-1, ...]

        elif 'particle' in dims:
            d[var] = nc.read_a_variable(var)[:num_released,...]
            if release_group is not None:   d[var] = d[var][rg == release_group-1, ...]
        else:
            d[var] = nc.read_a_variable(var)

        d['dimensions'][var] = nc.all_var_dims(var)

    return d

def _read_compact_tracks(nc, var_list, release_groupID):
    # read compact file with stream of values  with given in timestep and particle ID in time_particle dimension


    d = nc.global_attrs()# read all  global attibutes
    d['dimensions'] =  nc.dims()

    num_released = d['total_num_particles_released']


    particle_IDs = nc.read_a_variable('particle_ID') # this is time_particle particleID to allow unpacking

    time_steps_written= nc.global_attr('time_steps_written')

    n_time_step =  nc.read_a_variable('write_step_index')

    # todo status is special as last value for each particle when it is alive is needed to continue after death???
    # '_FillValue'
    missing_status= -99
    d['status'] =  np.full((time_steps_written, num_released), nc.global_attr('status_notReleased'), dtype=nc.var_dtype('status'))
    _insertMatrixValues(d['status'], n_time_step, particle_IDs, nc.read_a_variable('status'))
    last_recordedID = _get_last_alive(d['status'], nc.global_attr('status_notReleased'), nc.global_attr('status_dead'))
    rg = nc.read_a_variable('IDrelease_group')

    # don't reprocess status, and don't process others, not needed in rectangular format
    for v in ['status','particle_IDs' ,'write_step_index']:
        if v in var_list: var_list.remove(v)

    for name in set(var_list): # only do unique vars
        if nc.is_var_dim(name,'time_particle_dim'):
            # compact time varying variablesF
            s = nc.var_shape(name)
            d[name] = np.full((time_steps_written, num_released) + tuple(s[1:]),
                               nc.var_fill_value(name), dtype=nc.var_dtype(name))

            data = np.array(nc.read_a_variable(name))

            _insertMatrixValues(d[name], n_time_step, particle_IDs, data)
            _filIinDeadParticles(d[name], last_recordedID, nc.var_fill_value(name))

            if release_groupID is not None:
                 d[name] = d[name][:, rg == release_groupID, ...]

        elif   nc.is_var_dim(name,'particle_dim'):
            d[name] =nc.read_a_variable(name)[:num_released]
            if release_groupID is not None:
                d[name] = d[name][rg == release_groupID, ...]
        else:
        # non time_particle varying parameters, eg time
            d[name] = nc.read_a_variable(name)

        d['dimensions'][name] = nc.all_var_dims(name)
        if d['dimensions'][name][0] == 'time_particle':
            # output wil be retangual so correct dim
            d['dimensions'][name] = ['time', 'particle'] + d['dimensions'][name][1:]

    if release_groupID is not None:
        # finally get only  release group for status variable
        d['status'] = d['status'][:, rg == release_groupID]

    return d

@njit
def _insertMatrixValues(x,row,col,values):
    for n in range(values.shape[0]):
        x[row[n],col[n],...] = values[n]
@njit
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

@njit
def _filIinDeadParticles(data, last_recordedID, missing_status):
    # fill in values after death with last good one
    for n in range(data.shape[1]):
        n_last_write= last_recordedID[n]
        # fill in dead values below last recorded with last recorded value
        for nrow in range(n_last_write+1,data.shape[0]):
            data[nrow, n, ...] =  data[n_last_write, n, ...]

def read_stats_file(file_name):
    # read stats files

    nc = NetCDFhandler(file_name, mode='r')
    d = nc.global_attrs()  # read all  global attibutes
    d['dimensions'] = nc.dims()
    d['limits']=  {}
    d.update(_get_release_group_map_and_points(nc))

    data = nc.read_variables()
    d.update(data)

    if 'time' in data:
        d['time_var'] = 'time'
    else:
        d['time_var'] = 'age_bins'

    d.update(data)

    if nc.is_dim('polygon'):
        d['stats_type'] = 'polygon'
    else:
        d['stats_type'] = 'grid'

    # read count first fot mean value calc
    d['limits']['count'] = {'min': np.nanmin(d['count']), 'max': np.nanmax(d['count'])}

    # get mean values
    new_data ={}
    for var, vals in d.items():
        if var.startswith('sum_'):
            name = var.removeprefix('sum_')
            with np.errstate(divide='ignore', invalid='ignore'):
                new_data[name] = d[var]/d['count'] # calc mean
                d['limits'][name] = {'min' : np.nanmin(d[var]), 'max': np.nanmax(d[var])}

    d.update(new_data)
    nc.close()
    return d

def read_concentration_file(file_name, var_list=[]):
    # read concentration et cdf
    d={}
    nc = NetCDFhandler(file_name, 'r')
    var_list= list(set(['time','particle_count', 'particle_concentration']+ var_list))
    d.update(_get_release_group_map_and_points(nc))
    for var in var_list:
        if nc.is_var(var):
            d[var]= nc.read_a_variable(var)
        else:
            print('Warning: cannot find requested variable "' + var + '" in concentrations.nc output file, variables are ' + str(nc.all_var_names()) )

    nc.close()

    return d

def read_residence_file(file_name, var_list=[]):
    # read stats files
    var_list =  var_list  # make sure count is first, do to means
    nc = NetCDFhandler(file_name, mode='r')
    num_released = nc.global_attr('total_num_particles_released')
    d = {'total_num_particles_released': num_released,'limits' : {}}

    d['release_times']= nc.read_a_variable('release_times')

    d.update(_get_release_group_map_and_points(nc))

    # read count first for mean value calc
    for v in ['count','count_all_particles','time']:
        d[v]  = nc.read_a_variable(v)
        d['limits'][v] = {'min': np.nanmin(d[v]), 'max': np.nanmax(d[v])}
        if v in var_list: var_list.remove(v)

    for var in set(var_list):
        if nc.is_var(var):
            d[var]=  nc.read_a_variable(var)
        elif nc.is_var('sum_'+ var) :
            # check if summed version is in file and calc mean
            d['sum_'+ var] = nc.read_a_variable('sum_'+ var)
            with np.errstate(divide='ignore', invalid='ignore'):
                d[var] = d['sum_' + var]/d['count'] # calc mean

        else:
            print('Warning reading residence file ' + file_name + ', cannot load variable ' + var + ', is not in file ')
        d['limits'][var] = {'min': np.nanmin(d[var]), 'max': np.nanmax(d[var])}

    nc.close()
    return d

def read_grid_file(file_name):
    # load OT output file grid
    d={}
    nc = NetCDFhandler(file_name,'r')
    for var in nc.file_handle.variables.keys():
        d[var]= nc.read_a_variable(var)
    nc.close()

    return d

def read_grid_outline_file(file_name):
    return json_util.read_JSON((file_name))

def dev_read_event_file(file_name):
    #todo finish event reader
    nc = NetCDFhandler(file_name, 'r')
    nc.close()

def _get_release_group_map_and_points(nc):
    # get a dict mapping release group index to names and the reverse
    m = {'release_groupID': {},'release_locations':{} }
    name_list=[]
    for n, a  in enumerate(nc.global_attr_names()):
        val = nc.global_attr(a)
        if a.startswith('release_groupID_'):
            name= a.split('release_groupID_')[-1]
            m['release_groupID'][name] = val
            name_list.append(name)

    # unpack release points
    is_polygon_release = nc.read_a_variable('is_polygon_release')
    number_of_release_points = nc.read_a_variable('number_of_release_points')
    release_points = nc.read_a_variable('release_points')

    for n in range( is_polygon_release.size):
        m['release_locations'][name_list[n]]=dict(points =release_points[n,:number_of_release_points[n],:],is_polygon= is_polygon_release[n]==1)
    return m



