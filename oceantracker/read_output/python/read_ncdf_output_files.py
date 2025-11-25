# reads rectangular or flat output into buffer, reads whole file
from  oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from os import path
from oceantracker.util import json_util
from oceantracker.util.triangle_utilities import make_domain_mask
from oceantracker.read_output.python.util import read_rectangular_tracks_file, read_compact_tracks_file


def read_tracks_file(file_name, var_list=None, fraction_to_read=None):
    # read a single tracks file

    nc = NetCDFhandler(file_name,mode='r')
    is_compact  = nc.is_dim('time_particle_dim')
    nc.close()
    if is_compact:
        print(f'Reading compact track file {path.basename(file_name)}')
        data= read_compact_tracks_file.read_comp_tracks_file(
                            file_name, var_list=var_list,
                            fraction_to_read=fraction_to_read)
    else:
        data = read_rectangular_tracks_file.read_rect_tracks_file(
                            file_name, var_list=var_list,
                            fraction_to_read=fraction_to_read)

    data['date'] = data['time'].astype('datetime64[s]') # make sure time is seconds
    return data


def merge_track_files(file_list, dir=None, var_list=None,fraction_to_read=None):
    # append  tracks from file list of full paths or names within given dir

    if dir is not None: file_list = [path.join(dir, fn) for fn in file_list]

    # read old compact format
    nc = NetCDFhandler(file_list[0], mode='r')
    is_compact = nc.is_dim('time_particle_dim')
    nc.close()
    if is_compact:
        print('Merging compact track files')
        result= read_compact_tracks_file.read_comp_tracks_file(
                        file_list, var_list=var_list,
                        fraction_to_read=fraction_to_read)
    else:
        print('Merging rectangular track files')
        result = read_rectangular_tracks_file.merge_rect_track_files(
                        file_list,  var_list=var_list,
                        fraction_to_read=fraction_to_read)
    return result


def read_stats_file(file_name, nt=None):
    # read stats files
    nc = NetCDFhandler(file_name, mode='r')
    d = dict(global_attributes = nc.attrs())  # read all  global attibutes
    d['dimensions'] = nc.dims()
    d['limits'] = {}

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

    # get mean values oldf version, where average props are not in file
    new_data ={}
    for var, vals in d.items():
        # only calc props if not already in file
        if var.startswith('sum_') and var.removeprefix('sum_') not in d:
            name = var.removeprefix('sum_')
            with np.errstate(divide='ignore', invalid='ignore'):
                new_data[name] = d[var]/d['count'] # calc mean
                d['limits'][name] = {'min' : np.nanmin(new_data[name]), 'max': np.nanmax(new_data[name])}

    nc.close()
    return d

def read_LCS(file_name):
    # read stats files

    nc = NetCDFhandler(file_name, mode='r')
    d = nc.read_variables(nc.var_names())
    d.update(nc.attrs())
    d['dimensions'] = nc.dims()
    nc.close()
    return d

def read_concentration_file(file_name):
    # read concentration et cdf
    d={}
    nc = NetCDFhandler(file_name, 'r')

    for var in  nc.var_names():
        if nc.is_var(var):
            d[var]= nc.read_variable(var)
        else:
            print('Warning: cannot find requested variable "' + var + '" in concentrations.nc output file, variables are ' + str(nc.var_names()))

    nc.close()

    return d

def read_residence_file(file_name, var_list=[]):
    # read stats files
    var_list =  var_list  # make sure count is first, do to means
    nc = NetCDFhandler(file_name, mode='r')
    num_released = nc.attr('total_num_particles_released')
    d = {'total_num_particles_released': num_released,'limits' : {}}

    d['release_times']= nc.read_variable('release_times')
    d.update(nc.attrs())


    # read count first for mean value calc
    for v in ['count','count_all_particles','time']:
        d[v]  = nc.read_variable(v)
        d['limits'][v] = {'min': np.nanmin(d[v]), 'max': np.nanmax(d[v])}
        if v in var_list: var_list.remove(v)

    for var in set(var_list):
        if nc.is_var(var):
            d[var]=  nc.read_variable(var)
        elif nc.is_var('sum_'+ var) :
            # check if summed version is in file and calc mean
            d['sum_'+ var] = nc.read_variable('sum_' + var)
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
    d.update(nc.attrs())

    for a,val in nc.attrs().items():
        d[a] = val
    for var in nc.file_handle.variables.keys():
        d[var]= nc.read_variable(var)

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


    for name in nc.var_names():
        data = nc.read_variable(name)
        attr = nc.var_attrs(name)
        rg_name= attr['release_group_name']

        # extract info
        d[rg_name] = attr
        if 'geographic_coords' in nc.attrs():
            d[rg_name]['geographic_coords'] = bool(nc.attr('geographic_coords'))
        if 'points' in name:
            d[rg_name]['points'] = data

        pass
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

def read_particle_tracks_file(file_name_or_list,file_dir=None, var_list=None, file_number=None, fraction_to_read=None):
    print('Error >>>> reading tracks file, obsolete code ')
    print('\t "read_particle_tracks_file()" function has been removed')
    print('\t\t to read single file use >> read_tracks_file(file_name, var_list=None, fraction_to_read=None)')
    print('\t\t to read multiple files use >> merge_track_files(file_list, dir=None, var_list=None,fraction_to_read=None)')
    print('\t import these from module "oceantracker.read_output.python.read_ncdf_output_files"')
    raise(Exception('obsolete oceantracker code, see above'))