# reads rectangular or flat output into buffer, reads whole file
from  oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from os import path

from oceantracker.util import json_util
from oceantracker.util.numba_util import njitOT
from oceantracker.util.triangle_utilities import make_domain_mask

def read_compact_particle_tracks_file(file_name_or_list,file_dir=None, var_list=None, file_number=None, fraction_to_read=None):
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
        var_list = nc.all_var_names()
    else:
        # get list plus min data set
        var_list = list(set(['write_step_index','ID','particle_ID', 'x', 'time', 'status', 'IDrelease_group',
                             'IDpulse', 'x0', 'dry_cell_index', 'num_part_released_so_far']
                                + var_list))

    data = nc.read_variables(var_list)
    data['variable_info']  = nc.variable_info
    data['global_attributes']=nc.global_attrs()
    data['dimensions'] = nc.dims()

    nc.close()

    return data

def _unpack_compact_tracks(data):
    # read compact file with stream of values  with given in timestep and particle ID in time_particle dimension

    attributes = data['global_attributes']
    variable_info= data['variable_info']

    d = dict(dimensions=dict())

    num_released = data['ID'].max() + 1
    particle_IDs = data['particle_ID'] # this is time_particle particleID to allow unpacking

    time_steps_written= data['time'].size

    n_time_step =  data['write_step_index']

    # todo status is special as last value for each particle when it is alive is needed to continue after death???
    # '_FillValue'
    d['status'] =  np.full((time_steps_written, num_released), attributes['status_notReleased'], dtype=variable_info['status']['dtype'])
    _insertMatrixValues(d['status'], n_time_step, particle_IDs, data['status'])
    last_recordedID = _get_last_alive(d['status'], attributes['status_notReleased'], attributes['status_dead'])
    rg =  data['IDrelease_group']

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

            _insertMatrixValues(d[name], n_time_step, particle_IDs, data[name])
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



def read_stats_file(file_name,nt=None):
    # read stats files

    nc = NetCDFhandler(file_name, mode='r')
    d = dict( global_attributes = nc.global_attrs())  # read all  global attibutes
    d['dimensions'] = nc.dims()
    d['limits']=  {}

    data = nc.read_variables(sel=nt)
    d.update(data)

    if 'time' in data:
        d['time_var'] = 'time'
        d['date'] = d['time'].astype('datetime64[s]')
    else:
        d['time_var'] = 'age_bins'

    d.update(data)

    if nc.is_dim('polygon_dim'):
        d['stats_type'] = 'polygon'
        d = unpack_polygon_list('Polygon_', d)

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
                d['limits'][name] = {'min' : np.nanmin(new_data[name]), 'max': np.nanmax(new_data[name])}

    with np.errstate(divide='ignore', invalid='ignore'):
        # conectivity calc. is different depending on direction, use all particles if forwards, selected if backwards
        if 'backtracking' not in d['global_attributes']:
            b = d['count_all_particles'] # version prior to june 2025
        else:
            b = d['count_all_selected_particles'] if d['global_attributes']['backtracking'] == 1 else d['count_all_alive_particles']

        if d['stats_type'] == 'grid':
            d['connectivity_matrix'] = d['count'] / b[..., np.newaxis, np.newaxis]
        else:
            d['connectivity_matrix'] = d['count'] / b[..., np.newaxis]

    d.update(new_data)
    nc.close()
    return d

def unpack_polygon_list(tag,d):
    # make polygon list from variables starting with d
    out = []
    for key in d.keys():
        if key.startswith(tag):
            a = d['variable_attributes'][key]
            out.append(dict(points=d[key],name=a['polygon_name'],
                            user_polygonID=a['user_polygonID'],
                            instanceID = a['instanceID'] ))
    d['polygon_list'] = out
    d={key: item for key, item in d.items() if not key.startswith(tag) }
    return d
def read_LCS(file_name):
    # read stats files

    nc = NetCDFhandler(file_name, mode='r')
    d = nc.read_variables(nc.all_var_names())
    d.update(nc.global_attrs())
    d['dimensions'] = nc.dims()
    nc.close()
    return d

def read_concentration_file(file_name):
    # read concentration et cdf
    d={}
    nc = NetCDFhandler(file_name, 'r')

    for var in  nc.all_var_names():
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
    d.update(nc.global_attrs())


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
    d.update(nc.global_attrs())

    for a,val in nc.global_attrs().items():
        d[a] = val
    for var in nc.file_handle.variables.keys():
        d[var]= nc.read_a_variable(var)

    if nc.is_var('domain_outline_nodes'):
        domain=dict(nodes=d['domain_outline_nodes'],
                    points= d['domain_outline_x'] if  'domain_outline_x' in d else d['x'][d['domain_outline_nodes'],:],
                    )
        domain_masking_polygon =  d['domain_masking_polygon'] if 'domain_masking_polygon' in d\
                                                    else make_domain_mask(domain['points'])

        if nc.is_var('island_outline_nodes'):
            island_nodes = nc.un_packed_1Darrays('island_outline_nodes')
            islands = [ dict(nodes = n,points= d['x'][n,:]) for n in island_nodes]
        else:
            islands =[]

        d['grid_outline'] = dict(domain= domain, islands=islands,
                                 domain_masking_polygon=domain_masking_polygon)
    nc.close()

    return d

def read_grid_outline_file(file_name):
    return json_util.read_JSON((file_name))

def dev_read_event_file(file_name):
    #todo finish event reader
    nc = NetCDFhandler(file_name, 'r')
    nc.close()


def read_release_groups_info(file_name):
    nc = NetCDFhandler(file_name,mode='r')
    d= dict()


    for name in nc.all_var_names():
        data = nc.read_a_variable(name)
        attr = nc.all_var_attr(name)
        rg_name= attr['release_group_name']

        # extract info
        d[rg_name] = attr
        if 'geographic_coords' in nc.global_attrs():
            d[rg_name]['geographic_coords'] = bool(nc.global_attr('geographic_coords'))
        if 'points' in name:
            d[rg_name]['points'] = data

        pass
    nc.close()
    return d
