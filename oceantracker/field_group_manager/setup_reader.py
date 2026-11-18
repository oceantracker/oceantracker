import xarray as xr
import numpy as np
from copy import copy, deepcopy
from scipy import stats
from time import perf_counter

from numba.core.typing import signature

from oceantracker.shared_info import shared_info as si
from oceantracker import definitions
from oceantracker.util import  time_util, json_util,basic_util
from oceantracker.reader._oceantracker_dataset import OceanTrackerDataSet
from oceantracker.util.parameter_checking import ReaderMapAlternativesChecker, ReaderListMapAlternativesChecker
from oceantracker.util.parameter_checking import ParamValueChecker, ParameterListChecker
from oceantracker.field_group_manager import get_file_info
import tempfile

def make_a_reader_from_params(users_reader_params):
    t0 = perf_counter()
    ml = si.msg_logger

    file_info, var_info, dim_info = get_file_info.build_hindcast_info(users_reader_params)

    # detect reader format and add class_name to params
    reader = _detect_hydro_file_format(users_reader_params, var_info, dim_info)
    info = reader.info

    # discard problematic variables given by user
    for file_var in reader.params['drop_variables']:
        if file_var in reader.info['variables']:
            del var_info[file_var]
        else:
            ml.msg(f'Cannot drop file variable {file_var}, not in files', warning=True, caller=reader)

    # put required hindcast info into reader info
    _add_file_var_dim_info_to_reader_info(reader, file_info, var_info, dim_info)

    # assemble dataset share reader info with it
    reader.dataset = OceanTrackerDataSet(reader.info)

    reader.add_hindcast_info()  # any tweaks for specific reader

    _make_variable_time_step_to_fileID_map(reader, file_info)

    _catalog_fields(reader) # work out if mapped fields are  time varying , 2D, 3D etc


    if reader.development:
        ml.msg(f'Class "{reader.__class__.__name__}" under development, it may not work in all cases',
                           hint=f' contact developer with any unexpected issues', warning=True)


    # sort files into time order and add info to reader builder on if 3D hindcast and mapped field
    # uses times in files containing the velocity variable
    _time_sort_files(reader,file_info)

    _determine_vertical_grid_regridding(reader)

    # sort out use of A-z profile in vertical random walk, bottom stress in friction velocity calc.
    info['has_A_Z_profile'] = 'A_Z_profile' in info['field_info']
    info['has_bottom_stress'] = 'bottom_stress' in info['field_info']

    # work out if in geographic coords
    info['geographic_coords'] = reader.detect_lonlat_grid()
    info['time_buffer_size'] = si.settings.time_buffer_size

    # hindcast integrity checks
    _check_file_variables_have_same_time_and_dim_sizes(reader)
    _check_time_consistency(reader)

    ml.progress_marker('made reader from its params. and time sorted files', start_time=t0, tabs = 1)
    return reader

def _detect_hydro_file_format(reader_params, var_info, dim_info):
    # detect hindcast format and add reader class_name to params if missing
    # return reader class_name if given
    #todo show which tests passed for each reader
    ml = si.msg_logger

    if 'class_name' in reader_params:
        ml.progress_marker(f'Using given reader parameter class_name = "{reader_params["class_name"]}"')
        readers_to_check = dict(user_named_reader=reader_params[ 'class_name'] )
    else:
        # look for reader amongst known readers
        readers_to_check = definitions.known_readers

    readers=[]
    is_format = []
    for name, class_name in readers_to_check.items():
        # first check if essential variables are in the file
        p = deepcopy(reader_params)
        p['class_name'] = class_name
        r, isf =  _import_reader(p, var_info, dim_info)

        # break if all testes passed as found reader
        readers.append(r)
        is_format.append(isf)
        if isf:  break

    if not any(is_format):
        ml.msg(f' In detecting file format, not all tests against known file format variables were passed')
        for r in readers:
            params= r.params
            fvm, gvm,dm = params['field_variable_map'], params['grid_variable_map'], params['dimension_map']
            report = r.info['hindcast_integrity_report']
            ml.msg(f'Has required variables/dims for format "{report["class_name"]}" ', tabs= 3)
            req= report['required']
            ml.msg('Field variables: '+ ", ".join([f"{k} (mapped to  {fvm[k]})={v}" for k, v in req['fields'].items()]), tabs=4)
            ml.msg('Grid variables: ' + ", ".join([f"{k} (mapped to  {gvm[k]})={v}" for k, v in req['grid'].items()]), tabs=4)
            ml.msg('Dimensions    : ' + ", ".join([f"{k} (mapped to  {dm[k]})={v}" for k, v in req['dims'].items()]), tabs=4)

        ml.msg (f'Could not set up reader, as could not detect file format  as not all expected variables are present, may be an unknown format , or unexpected differences in variable names',
                 )
        ml.msg(f'Found variables {list(var_info.keys())}', tabs=3)
        ml.msg(f'Found dimensions {list(dim_info.keys())}',tabs=3)
        ml.msg(f'Check file variable/dims., ' , hint='Adjust reader field/grid/dims maps to match file variables/dims',
               error = True)

    # make and merge defaults for found reader
    reader = readers[is_format.index(True)]

    ml.progress_marker(f'Detected reader class_name = "{reader.__class__.__module__}.{reader.__class__.__name__}"')
    return reader

def _import_reader(reader_params, var_info, dim_info):
    reader = si.class_importer.make_class_instance_from_params('reader', reader_params)
    report = _do_hindcast_variables_match_format_report(reader, var_info, dim_info)

    # ensure vel params are correct
    if report['is_format'] and 'water_velocity' in reader.params['field_variable_map']:
        vel_vars, reader.info['is3D'] =  _detect_vel_var_and_if_3D(reader, var_info, dim_info)
        if vel_vars is not None:
            reader_params['field_variable_map']['water_velocity'] = vel_vars
    reader.info['hindcast_integrity_report'] = report
    return reader,report['is_format']


def _time_sort_files(reader, file_info):
    # sort variable fileIDs by time, now all files are read
    info = reader.info
    time_var =  info['time_var']
    # add times to each files info

    # first get start times of all files from pre-read time variables and convert to 1970 time
    for ID, f in enumerate(file_info):

        if f['time'] is not None:
            time = f['time']
            time = np.round(reader.decode_time(time),3) # round unversal time to milli seconds
            f['start_time'] = float(time[0])
            f['end_time'] = float(time[-1])
            f['time_steps'] = time.size
            f['ID'] = ID
            f['time'] = time # save  universal time
            f['time_attrs'] = f['variables'][time_var]['attrs']
            f['start_date'] = time_util.seconds_to_isostr( f['start_time'])
            f['end_date'] = time_util.seconds_to_isostr(f['end_time'])

    # sort variable fileIDs into time order
    for name, var in info['variables'].items():
        var['time_varying'] = info['time_dim'] in var['dims']
        if  var['time_varying']:
            start_times = np.asarray([file_info[ID]['start_time'] for ID in var['fileIDs']])
            file_order = np.argsort(start_times)
            var['fileIDs'] = var['fileIDs'][file_order]
        else:
            var['fileIDs'] = var['fileIDs'][0]  # todo keep as list??

    #  build a time for every variables
    #  note time may appear in many files if variables are split between file, eg schsim v5 than once in each file
    # so must do this for all variables to ensure all files are covered, with some unnecessary repeats when more than one variable in same file
    #   time is not done as done a below as a "coordinate"
    vel_var0 = reader.params['field_variable_map']['water_velocity'][0]
    for var_name, var in info['variables'].items():
        if not var['time_varying']: continue
        if var_name == time_var : continue
        # only look at time varying variables, which are not time
        var['time'] = np.concatenate([file_info[fID]['time'] for fID in var['fileIDs']])

    # set each file's first/last hindcast time step only from variables spanning the whole hindcast,
    # variables only in some of the files, eg. extra outputs added part way through a run,
    # would otherwise give file time steps counted from the first file they are in
    n_steps = info['variables'][vel_var0]['time'].size
    partial_vars = []
    for var_name, var in info['variables'].items():
        if not var['time_varying'] or var_name == time_var: continue
        if var['time'].size != n_steps:
            partial_vars.append(var_name)
            continue
        n0 = 0
        for fID in var['fileIDs']:
            file_info[fID]['first_time_step_in_file'] = n0
            file_info[fID]['last_time_step_in_file'] = n0 + file_info[fID]['time_steps'] - 1
            n0 += file_info[fID]['time_steps']

    if len(partial_vars) > 0:
        si.msg_logger.msg(f'Hindcast variables only in some files, these can not be used as fields: {partial_vars}',
                          hint='variables are missing from some hindcast files, eg. outputs switched on part way through the hydro-model run', note=True)


    # if variables in different files, eg schism v5, time may be in many files,
    #  only use file IDs for the ones for the first water velocity variable, which must always be in hindcasts
    vel_var0= reader.params['field_variable_map']['water_velocity'][0]
    time =  info['variables'][vel_var0]['time']
    info['time_coord'] = time

    if time.size < 2:
        si.msg_logger.msg('Velocity variable in hydro files has less than 2 time steps', hint = 'need at least 2 steps for particle tracking', fatal_error=True)

   # hindcast start and ends times from time_coord
    info['start_time'] = time[0]
    info['end_time'] = time[-1]
    info['duration'] = time[-1] - time[0]
    info['total_time_steps'] =  time.size

    info['time_step'] = np.median(np.diff(time)) # todo should this be mode?

    info['start_date'] = time_util.seconds_to_isostr(info['start_time'])
    info['end_date'] = time_util.seconds_to_isostr(info['end_time'])
    info['dates'] = time_util.seconds_to_isostr( time)

    pass

def _make_variable_time_step_to_fileID_map(reader, file_info):
    info= reader.info
    # make time step to fileID map and file offset map for every time step, accounting for each variable's file order

    for name, var in info['variables'].items():
        if not var['time_varying']: continue

        time_step_fileID_map = np.zeros((0,),dtype=np.int32)
        time_step_file_offset_map = np.zeros((0,), dtype=np.int32)

        for fileID in  var['fileIDs']: #IDs have aleady been time sorted
            fi = file_info[fileID]
            n_time_steps = fi['time'].size # time steps in this file
            time_step_fileID_map =  np.append(time_step_fileID_map,fi['ID']*np.ones(( n_time_steps ,), dtype=np.int32))
            time_step_file_offset_map = np.append(time_step_file_offset_map,  np.arange(n_time_steps, dtype=np.int32))

        var['time_step_to_fileID_map'] = time_step_fileID_map
        var['time_step_to_file_offset_map'] = time_step_file_offset_map
    pass

def _determine_vertical_grid_regridding(reader):
    #sort out if regridding vertical grid
    info = reader.info
    params= reader.params

    # set default z dim info to that for 2D, add_hindcast_info changes them for  3D

    if not info['is3D']:
        info['num_z_interfaces'] = 1
        info['vert_grid_type'] = None
        info['vert_grid_type_in_files'] = None
        params['regrid_z_to_sigma_levels'] = False
        return

    # set working vertical grid type,if remapping to sigma grids
    vgt = si.vertical_grid_types

    info['vert_grid_type_in_files'] = copy(info['vert_grid_type'])

    if info['vert_grid_type'] in [vgt.Slayer, vgt.LSC] and params['regrid_z_to_sigma_levels']:
        info['vert_grid_type'] = vgt.Sigma
        params['regrid_z_to_sigma_levels'] = True

    elif info['vert_grid_type'] in [vgt.Slayer, vgt.LSC] and not params['regrid_z_to_sigma_levels']:
        params['regrid_z_to_sigma_levels'] = False

    elif info['vert_grid_type'] in [vgt.Sigma, vgt.Zfixed]:
        params['regrid_z_to_sigma_levels'] = False
    else:
        si.msg_logger.msg(f'Unknown grid vertical type "{info["vert_grid_type"]}"',
                          hint=f'must be one of {str(vgt.possible_values())}',
                          fatal_error=True)


def _catalog_fields(reader):
    # categorise field variables
    params = reader.params
    info = reader.info

    file_vars = info['variables']
    reader_field_vars_map = {}

    # loop over mapped variables and loaded variables
    mapped_fields = params['field_variable_map']
    for name in  params['field_variable_map']:

        # decompose variable list
        var_list = mapped_fields[name]
        if var_list is None: continue # no default
        if type(var_list) != list: var_list = [var_list]  # ensure it is a list
        if len(var_list) == 0: continue

        # use first variable to get basic info
        v1 = var_list[0]

        if v1 not in file_vars:
            continue

        field_params = dict(time_varying=file_vars[v1]['time_varying'],
                            is3D=any(x in params['all_z_dims'] for x in file_vars[v1]['dims']),  )
        field_params['zlevels'] = info['num_z_interfaces'] if field_params['is3D'] else 1

        # work out if variable is a vector field
        file_vars_info = {}

        dm = params['dimension_map']
        for n_var, v in enumerate(var_list):
            if v not in file_vars: continue  # listed var not in file, eg vector variable has no vertical velocity

            if dm['vector2D'] is not None and dm['vector2D'] in file_vars[v]['dims']:
                n_comp = 2
            elif dm['vector3D'] is not None and dm['vector2D'] in file_vars[v]['dims']:
                n_comp = 3
            else:
                n_comp = 1

            s4D = [si.settings.time_buffer_size if field_params['time_varying'] else 1,
                   info['num_nodes'],
                   info['num_z_interfaces'] if field_params['is3D'] else 1,
                   n_comp]

            file_vars_info[v] = dict(vector_components_per_file_var=n_comp,
                                     shape4D=np.asarray(s4D, dtype=np.int32),
                                     time_varying= field_params['time_varying'],
                                     is3D= field_params['is3D'] ,
                                     dims = list(file_vars[v]['dims'].keys()))

        field_params['is_vector'] = sum(x['vector_components_per_file_var'] for x in file_vars_info.values()) > 1
        reader_field_vars_map[name] = dict(file_vars_info=file_vars_info,
                                           params=field_params)
        if len(file_vars_info) < len(var_list):
            si.msg_logger.msg(f'not all vector components found for field {name}',
                   hint=f'missing file variables {[x for x in var_list if x not in file_vars_info]}', warning=True)

    # record field map
    info['field_info'] = reader_field_vars_map


def _do_hindcast_variables_match_format_report(reader, var_info, dim_info):
    # use readers map checker to find which ones are in the file

    file_vars = list(var_info.keys())
    dims= list(dim_info.keys())
    params= reader.params
    ml = si.msg_logger

    #todo simplify, below is essentially a merge with alternatives if present, do as a reader merge??
    report=dict(is_format=False, class_name = reader.params['class_name'],)
    for map_type in ['grid_variable_map','field_variable_map','dimension_map']:
        if map_type not in report: report[map_type] = dict( in_file = dict(),alternatives = dict())
        p = params[map_type]
        dp = reader.default_params[map_type]

        for key, val in dp.items():
            if key.startswith('control_key'): continue
            file_var_names = dims if map_type == 'dimension_map' else file_vars

            if not isinstance(val, (ReaderMapAlternativesChecker, ReaderListMapAlternativesChecker)) :
                # legacy variable maps with PCC and PLC, check if variable/param value  (or first if list of variables) in the file
                if map_type =='dimension_map' and type(p[key]) != list:
                    report[map_type]['in_file'][key] = p[key] in file_var_names
                elif type(val) == ParamValueChecker:
                    report[map_type]['in_file'][key]= p[key] in file_var_names
                elif type(val) == ParameterListChecker:
                    report[map_type]['in_file'][key] = (p[key][0] in file_var_names) if len(p[key]) >0 else False
                continue
            # new alternatives mappings
            if p[key] is None: # no user value given
                # choose from alternatives
                available = dims if map_type == 'dimension_map' else file_vars
                p[key] = dp[key].choose_alternative(available) # already have a default or user given value  for var

            if type(val) == ReaderMapAlternativesChecker:
                report[map_type]['in_file'][key] = p[key] in file_var_names
            elif type(val) == ReaderListMapAlternativesChecker:
                report[map_type]['in_file'][key] = (p[key][0] in file_var_names) if len(p[key]) > 0 else False

    # check if required variables present
    req = dict()
    req['fields'] =   {key: report['field_variable_map']['in_file'][key] for key in params['required_feilds']}
    req['fields']['water_velocity'] =  (report['field_variable_map']['in_file']['water_velocity']
                                                    or report['field_variable_map']['in_file']['water_velocity_depth_averaged'])
    req['grid'] = {key: report['grid_variable_map']['in_file'][key] for key in params['required_grid_variables']}
    req['dims'] = {key: report['dimension_map']['in_file'][key] for key in params['required_dimensions']}
    report['is_format'] = all([all(req['fields'].values()), all(req['grid'].values()), all(req['dims'].values())])
    report['required'] = req
    return report

def _add_file_var_dim_info_to_reader_info(reader, file_info, var_info, dim_info):
        # construct catalog
        info = reader.info
        info['file_info'] = file_info
        info['variables'] = var_info
        info['dims'] = dim_info
        info['time_var'] = reader.params['grid_variable_map']['time']

        # check if time dim is in each variable
        info['time_dim'] = list(var_info[info['time_var']]['dims'])[0]
        for name, var in var_info.items():
            var['time_varying'] =  info['time_dim']  in var['dims']

        # add full list of attributes
        info['file_attrs'] =dict()
        for f in file_info:
            info['file_attrs'].update(f['attrs'])


def _check_file_variables_have_same_time_and_dim_sizes(reader):
    # check if all variables have same number of time steps
    info =reader.info
    ml = si.msg_logger

    # check all variables have same number of time steps
    var_time_steps = {name: var['time'].size for name, var in  info['variables'].items() if 'time' in var}
    result = stats.mode([n for name,n in var_time_steps.items()])
    if result.count > 1:
        bad_vars= { name: n for name,n in var_time_steps.items() if n != result.mode}
        if len(bad_vars)>0:
            ml.msg("Hindcast errors, some variables have different number of time steps from the most common number ",
                   hint=f"Hindcast may be missing some files containing variables and time steps are:\n{str(bad_vars)} \n use reader param. drop_variables to ignore these?",
                   error=True)

    # check dims sizes the same in all files
    for name, dim in  info['dims'].items():
        sizes= np.asarray([ fi['dims'][name] if name in fi['dims'] else  0 for fi in info['file_info']])
        result = stats.mode(sizes[sizes>0])
        if result.count > 1:
            bad_files = np.logical_and(sizes != result.mode, sizes > 0)
            if np.any(bad_files):
                fn = [ f['name'] for n, f in enumerate(info['file_info']) if bad_files[n]]
                ml.msg(f'Some files have different dimension sizes for dim. "{name}", expected size {int(result.mode)} \n bad files? {str(fn)}',
                    hint=f"Downloaded data with different settings? repeat download with consistent settings?",
                    error=True)

def _check_time_consistency(reader):
    # check all variables have same time_step_to_fileID_map, and save one version of it
    #todo do not currently used, reactivate?
    info= reader.info
    ml = si.msg_logger

    dt = np.diff(info['time_coord'])

    # look for repeated time steps, eg, from  data servive which repeats last step in next file as first in next file
    sel = dt < 0.1 * info['time_step']
    if False and  np.any(sel):
        for name, v in  info['variables'].items():

            if v['time_varying']:
                keep = np.flatnonzero(~sel)
                v['time_step_to_fileID_map'] = v['time_step_to_fileID_map'][keep]
                v['time_step_to_file_offset_map'] = v['time_step_to_file_offset_map'][keep]
                pass

        sel = np.flatnonzero(sel)
        t1 = reader.info['time_coord'][sel]
        t2 = reader.info['time_coord'][sel + 1]
        si.msg_logger.msg(f'Hindcasts has repeated time steps, space as les tha .1*time_step, ignoring repeats,  eg. at {time_util.seconds_to_isostr(t1[0])}',
                          hint=' see hindcast_info.json for list of repeats. Used a hindcast download service?,\n it may repeat last time step in file as first tim step in next file  ',
                          warning = True)

        reader.info['time_step_repeats'] = [[time_util.seconds_to_isostr(a), time_util.seconds_to_isostr(b)] for a, b in zip(t1, t2)]

    sel = np.flatnonzero( dt > 3 * info['time_step'])
    if np.any(sel):
        t1 = reader.info['time_coord'][sel]
        t2 = reader.info['time_coord'][sel+1]

        si.msg_logger.msg('Some hindcast time steps are longer than 3 average time steps',fatal_error=True,
           hint = f'Hindcast may be missing files or othe time error, eg at {time_util. seconds_to_isostr(t1[0])} to {time_util. seconds_to_isostr(t2[0])}, see hindcast_info.json for full list of dates', warning=True)

        for d1,d2  in [ [time_util. seconds_to_isostr(a),time_util. seconds_to_isostr(b) ] for a,b in zip(t1,t2) ]:
            si.msg_logger.msg(f'Gap from {d1}  to {d2}' , error=True, tabs=2)

        si.msg_logger.msg('Hindcast must have all time steps', fatal_error=True,
                            hint=f'Find missing files, check al time steps are in all files, covering above time gaps')

    return

def _detect_vel_var_and_if_3D(reader, var_info, dim_info):
    # work out if hincast id 3D by checking if vel is 3D and assign water_velovity vars

    params= reader.params
    fvm = params['field_variable_map']
    gvm = params['grid_variable_map']
    dm = params['dimension_map']

    if fvm['water_velocity'][0] in var_info:
        vel_vars = fvm['water_velocity']
    elif fvm['water_velocity_depth_averaged'][0] in var_info:
        vel_vars =fvm['water_velocity_depth_averaged']
    else:
        vel_vars=None
    # see if vel has any z dimensions
    if vel_vars is not None:
        is3D = any([d in var_info[vel_vars[0]]['dims'] for d in params['all_z_dims']])
    else:
        is3D= False
    return vel_vars, is3D