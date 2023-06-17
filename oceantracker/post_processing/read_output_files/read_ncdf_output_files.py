# reads rectangular or flat output into buffer, reads whole file
from  oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from numba import njit

from oceantracker.util import json_util

def read_particle_tracks_file(file_name, var_list=[], release_group= None, fraction_to_read=None):
    # release group is 1 based
    nc = NetCDFhandler(file_name, mode='r')
    var_list = ['x', 'time','status', 'IDrelease_group', 'IDpulse', 'x0','dry_cell_index','num_part_released_so_far'] + var_list
    # trim list to variables in the file
    working_var_list= []
    for var in var_list:
        if var not in nc.get_var_names():
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
    num_released= nc.get_global_attr('total_num_particles_released')
    rg = nc.read_a_variable('IDrelease_group')[:num_released]
    d = {'dimensions': {}, 'total_num_particles_released' :num_released }
    for var in set(var_list):
        dims= nc.get_var_dims(var)
        if 'particle' in dims and 'time' in dims:
            d[var] = nc.read_a_variable(var)[:, :num_released, ...]
            if release_group is not None: d[var] = d[var][:, rg == release_group-1, ...]

        elif 'particle' in dims:
            d[var] = nc.read_a_variable(var)[:num_released,...]
            if release_group is not None:   d[var] = d[var][rg == release_group-1, ...]
        else:
            d[var] = nc.read_a_variable(var)

        d['dimensions'][var] = nc.get_var_dims(var)

    return d

def _read_compact_tracks(nc,var_list,release_group):
    # read compact file with stream of values  with given in timestep and particle ID in time_particle dimension
    num_released = nc.get_global_attr('total_num_particles_released')

    d = {'dimensions': {},'total_num_particles_released': num_released}
    particle_IDs = nc.read_a_variable('particle_ID') # this is time_particle particleID to allow unpacking

    time_steps_written= nc.get_global_attr('time_steps_written')

    n_time_step =  nc.read_a_variable('write_step_index')

    # todo status is special as last value for each particle when it is alive is needed to continue after death???
    d['status'] =  np.full((time_steps_written, num_released) , -127, dtype=nc.get_var_dtype('status'))
    _insertMatrixValues(d['status'], n_time_step, particle_IDs, nc.read_a_variable('status'))

    rg = nc.read_a_variable('IDrelease_group')

    # dont reprocess status, and dont process others, not needed in rectangular format

    for v in ['status','particle_IDs' ,'write_step_index']:
        if v in var_list: var_list.remove(v)

    for var in set(var_list): # only do unique vars
        if nc.is_var_dim(var,'time_particle_dim'):
            # compact time varying variablesF
            s = nc.get_var_shape(var)
            d[var] = np.full((time_steps_written, num_released) + tuple(s[1:]), nc.get_var_fillValue(var), dtype=nc.get_var_dtype(var))

            data = np.array(nc.read_a_variable(var))

            _insertMatrixValues(d[var], n_time_step, particle_IDs, data)

            if release_group is not None:
                 d[var] = d[var][:, rg == release_group-1, ...]

        elif   nc.is_var_dim(var,'particle_dim'):
            d[var] =nc.read_a_variable(var)[:num_released]
            if release_group is not None:
                d[var] = d[var][rg == release_group-1, ...]
        else:
        # non time_particle varying parameters, eg time
            d[var] = nc.read_a_variable(var)

        d['dimensions'][var] = nc.get_var_dims(var)
        if d['dimensions'][var][0] == 'time_particle':
            # output wil be retangual so correct dim
            d['dimensions'][var] = ['time', 'particle'] + d['dimensions'][var][1:]

    if release_group is not None:
        # finally get only  release group for status variable
        d['status'] = d['status'][:, rg == release_group-1]

    #  fill in data for dead particles , as same as lastrecorded, but mark with status dead
    for var in var_list:
        if type(d[var]) == np.ndarray and  d[var].ndim > 1 and d[var].shape[1] == d['x'].shape[1]:
            _filIinDeadParticles(d[var], var, d['status'], -127)

    _filIinDeadParticles(d['status'], 'status', d['status'], -127) # do status last as needed to work on others


    return d

@njit
def _insertMatrixValues(x,row,col,values):
    for n in range(values.shape[0]):
        x[row[n],col[n],...] = values[n]

@njit
def _filIinDeadParticles(data, var, status, missing_status):
    # fill in values after death with last good one
    for m in range(data.shape[1]):
        n_last_write= 0
        for n in range(data.shape[0]):
            if status[n,m]  != missing_status:
                n_last_write  = n  #  find last good value, before particle is marked dead
            else:
                if var == 'status':
                    # no status once no longer been written is unknown, so make dead
                    data[n, m] = -2  # set as dead as read status unknown
                else:
                    data[n,m,...] =  data[n_last_write,m,...]

def read_stats_file(file_name, var_list=[]):
    # read stats files
    var_list = ['count'] + var_list  # make sure count is first, do to means
    nc = NetCDFhandler(file_name, mode='r')
    num_released = nc.get_global_attr('total_num_particles_released')
    d = {'total_num_particles_released': num_released,'limits' : {}}

    d.update(_get_release_group_map_and_points(nc))

    if nc.is_var('time') :
        var_list =  var_list +['time']
        d['time_var'] = 'time'
    else:
        var_list = var_list + ['age_bins']
        d['time_var'] = 'age_bins'

    if nc.is_dim('polygon'):
        d['stats_type'] = 'polygon'
    else:
        var_list = var_list + ['x', 'y']
        d['stats_type'] = 'grid'

    # read count first fot mean value calc
    #todo why id count al particls not done here
    d['count'] = nc.read_a_variable('count')
    d['limits']['count'] = {'min': np.nanmin(d['count']), 'max': np.nanmax(d['count'])}

    var_list.remove('count')

    for var in set(var_list):
        if nc.is_var(var):
            d[var]=  nc.read_a_variable(var)
        elif nc.is_var('sum_'+ var) :
            # check if summed version is in file and calc mean
            d['sum_'+ var] = nc.read_a_variable('sum_'+ var)
            with np.errstate(divide='ignore', invalid='ignore'):
                d[var] = d['sum_' + var]/d['count'] # calc mean
                d['limits'][var] = {'min' : np.nanmin(d[var]), 'max': np.nanmax(d[var])}

        else:
            print('Warning reading stats file ' + file_name + ', cannot load variable' + var + ', is not in file ')
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
            print('Warning: cannot find requested variable "' + var + '" in concentrations.nc output file, variables are ' + str(nc.get_var_names()) )

    nc.close()

    return d

def read_residence_file(file_name, var_list=[]):
    # read stats files
    var_list =  var_list  # make sure count is first, do to means
    nc = NetCDFhandler(file_name, mode='r')
    num_released = nc.get_global_attr('total_num_particles_released')
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
    for n, a  in enumerate(nc.all_global_attr()):
        val = nc.get_global_attr(a)
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



