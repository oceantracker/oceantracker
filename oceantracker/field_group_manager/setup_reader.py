import xarray as xr
import numpy as np
from copy import copy, deepcopy
from os import path
from glob import  glob

from oceantracker.shared_info import shared_info as si
from oceantracker import definitions
from oceantracker.util import  time_util, json_util
from oceantracker.reader._oceantracker_dataset import OceanTrackerDataSet

def make_a_reader_from_params(reader_params, settings, crumbs=''):

    crumbs = crumbs + '>build_a_reader '

    _check_input_dir(reader_params, crumbs=crumbs)
    dataset = OceanTrackerDataSet(reader_params)

    # detect reader format and add clas_name to params
    reader = _detect_hydro_file_format(reader_params, dataset,  crumbs=crumbs)


    # discard problematic variables
    for file_var in reader.params['drop_variables']:
        if file_var in reader.dataset.info['variables']:
            del reader.dataset.info['variables'][file_var]
        else:
            si.msg_logger.msg(f'Cannot drop file variable {file_var}, not in file', warning=True, caller = reader)

    if reader.development:
        si.msg_logger.msg(f'Class "{reader.__class__.__name__}" under development, it may not work in all cases',
                           hint=f' contact developer with any unexpected issues', warning=True)

    # sort out which velocity variable to use
    # ie.  water_velocity field if present, otherwise try depth average velocity if present
    fvm = reader.params['field_variable_map']
    file_vars = dataset.info['variables']

    if fvm['water_velocity'][0] not in file_vars and fvm['water_velocity_depth_averaged'] is not None:
        fvm['water_velocity'] = fvm['water_velocity_depth_averaged']  # map to  depth average

    if  fvm['water_velocity'][0] not in file_vars: # no velocity found
        si.msg_logger.msg(f'No velocity variable  in files, could not find  {str(fvm["water_velocity"][0])}. nor  depth average vel. {str(fvm["water_velocity_depth_averaged"])}',
                          hint=f'file variables ={str(list(file_vars))}', fatal_error=True)

    # sort files into time order and add info to reader builder on if 3D hindcast and mapped field
    # uses times in files containing the velocity variable
    _time_sort_files(reader, crumbs)


    _make_variable_time_step_to_fileID_map(reader)

    info = reader.info
    info.update(reader.dataset.info) # make data set and reader info the same

    # additional info on is D, vert grid type, node dim etc needed to size field buffers etc
    _standard_needed_info(reader) # common to all readers

    reader.add_hindcast_info() # any tweaks for specific reader


    # todo check all required fields are set
    if info['vert_grid_type'] is not None and info['vert_grid_type'] not in si.vertical_grid_types.possible_values():
        si.msg_logger.msg(f'Coding error, dont recognise vert_grid_type grid type, got {info["vert_grid_type"]}, must be one of [None , "Slayer_or_LSC","Zlayer","Sigma"]',
                hint=f'check reader codes  get_hindcast_info() ', error=True)

    _catalog_fields(reader, crumbs=None)

    # set working vertical grid type,if remapping to sigma grids
    vgt = si.vertical_grid_types

    info['vert_grid_type_in_files'] = copy(info['vert_grid_type'])

    if info['vert_grid_type'] in [vgt.Slayer, vgt.LSC] and reader_params['regrid_z_to_sigma_levels']:
        info['vert_grid_type'] = vgt.Sigma
        reader_params['regrid_z_to_sigma_levels'] = True

    elif info['vert_grid_type'] in [vgt.Slayer, vgt.LSC]  and not reader_params['regrid_z_to_sigma_levels']:
        reader_params['regrid_z_to_sigma_levels'] = False

    elif info['vert_grid_type'] in [vgt.Sigma, vgt.Zfixed]:
        reader_params['regrid_z_to_sigma_levels'] = False

    elif info['is3D']:
        si.msg_logger.msg(f'Unknown grid vertical type "{info["vert_grid_type"]}"',
                       hint=f'must be one of {str(vgt.possible_values())}',
                       fatal_error=True)

    info['has_A_Z_profile'] = 'A_Z_profile' in info['field_info']
    info['has_bottom_stress'] = 'bottom_stress' in info['field_info']

    # work out in 3D run from water velocity
    info['geographic_coords'] = reader.detect_lonlat_grid()
    info['time_buffer_size'] = si.settings.time_buffer_size

    return reader

def _standard_needed_info(reader):
    # info need to size the field reader buffers etc
    params= reader.params
    info = reader.info
    ds_info = reader.dataset.info
    file_vars = ds_info['variables']
    dm = params['dimension_map']
    fvm = params['field_variable_map']
    gm = params['grid_variable_map']

    # hindcast is 3D if velocity has any z dim
    v_name = fvm['water_velocity'][0]
    info['is3D'] =  any([ d in file_vars[v_name]['dims'] for d in dm['all_z_dims']])

    # set default z dim info to that for 2D, add_hindcast_info changes them for  3D
    info['z_dim'] = None
    info['num_z_interfaces'] = 1
    info['all_z_dims'] = []
    info['vert_grid_type'] = None


def _detect_hydro_file_format(reader_params, dataset, crumbs=''):
    # detect hindcast format and add reader class_name to params if missing
    # return reader class_name if given
    #todo show which tests passed for each reader
    ml = si.msg_logger
    crumbs += '> detecting reader file format '
    if 'class_name' in reader_params:
        reader = si.class_importer.make_class_instance_from_params('reader',
                                     reader_params, check_for_unknown_keys=True,
                                     crumbs=crumbs + f'> loading given reader with class_name "{reader_params["class_name"]}"')
        reader.dataset = dataset
        ml.progress_marker(f'Using given reader parameter class_name = "{reader.__class__.__module__}.{reader.__class__.__name__}"')
        return reader

    # look for reader amongst known readers
    reader_class_name = None

    tests ={} # set of tests to pass
    ds_info = dataset.info
    file_vars = ds_info['variables']
    for name, class_name in definitions.known_readers.items():
        # first check if essential variables are in the file
        p = deepcopy(reader_params)
        p['class_name'] = class_name
        r = si.class_importer.make_class_instance_from_params('reader',p,
                        check_for_unknown_keys=False,
                        crumbs=crumbs + f'> loading reader = class name "{class_name}"')
        gmap = r.params['grid_variable_map']
        fmap= r.params['field_variable_map']

        # do basic tests for format for time, x and velocity
        p = True
        if fmap['water_velocity'][0] in file_vars:
            vel_var = fmap['water_velocity'][0]
        elif  fmap['water_velocity_depth_averaged'][0] in  file_vars:
            vel_var = fmap['water_velocity_depth_averaged'][0]
        else:
            # neither in file
            vel_var = 'velocity'
            p=False
        t = { vel_var: p}
        # check if other variables in the signature are present
        for s in r.params['variable_signature'] + [gmap['time'], gmap['x']]:
            t[s] = s in ds_info['variables']

        tests[name] = t
        # break if all testes passed as found reader
        if all(t.values()):
            reader_class_name = class_name
            break


    if reader_class_name is None:
        ml.msg(f' In detecting file format, not all tests against known file format variables were passed', error=True)
        for name, vals in tests.items():
            ml.msg(f' Format "{name}" , required variables detected {str(vals)} ', tabs= 2)
        ml.msg (f'Could not set up reader, as could not detect file format  as not all expected variables are present, may be an unknown format , or unexpected differences in variable names',
               hint=f'use reader to map to names in files? found variables {list(ds_info["variables"].keys())}',
               fatal_error=True, crumbs=crumbs)

    # make and merge defaults for found reader
    reader_params['class_name'] = reader_class_name
    reader = si.class_importer.make_class_instance_from_params('reader', reader_params,
                check_for_unknown_keys=True,
                crumbs=crumbs + f'> loading detected reader = class name "{reader_class_name}"')

    reader.dataset = dataset
    ml.progress_marker(f'Detected reader class_name = "{reader.__class__.__module__}.{reader.__class__.__name__}"')
    return reader


def _time_sort_files(reader, crumbs):
    # sort variable fileIDs by time, now all files are read
    ds_info= reader.dataset.info

    ds_info['time_var'] = reader.params['grid_variable_map']['time']

    time_var = ds_info['time_var']
    time_var_info = ds_info['variables'][ time_var]
    ds_info['time_dim'] = list(time_var_info['dims'].keys())[0]

    # add times to each files info
    # first read start times of all files
    fi = ds_info['files']  # file names etc
    for ID, f in enumerate(ds_info['files']):
        ds = reader.dataset._open_file(f['name'])
        f['has_time'] =  ds_info['time_var'] in ds.variables
        if f['has_time']:
            time = ds[time_var].compute()
            time = np.round(reader.decode_time(time),3) # round to milli seconds
            f['start_time'] = float(time[0])
            f['end_time'] = float(time[-1])
            f['time_steps'] = time.size
            f['ID'] = ID
            f['time'] = time
            f['time_attrs'] = ds[time_var].attrs
            f['start_date'] = time_util.seconds_to_isostr( f['start_time'])
            f['end_date'] = time_util.seconds_to_isostr(f['end_time'])

    # sort variable fileIDs into time order
    for v_name, item in ds_info['variables'].items():
        item['time_varying'] = ds_info['time_dim'] in item['dims']
        if  item['time_varying']:
            item['fileIDs'] = np.asarray(item['fileIDs'])
            start_times = np.asarray([fi[x]['start_time'] for x in item['fileIDs']])
            file_order = np.argsort(start_times)
            item['fileIDs'] = item['fileIDs'][file_order]
        else:
            item['fileIDs'] = item['fileIDs'][0]  # todo keep as list??



    #  build a time for every variables
    #  note time may appear in many files if variables are split between file, eg schsim v5 than once in each file
    # so must do this for all variables to ensure all files are covered, with some unnecessary repeats when more than one variable in same file
    #   time is not done as done a below as a "coordinate"
    vel_var0 = reader.params['field_variable_map']['water_velocity'][0]
    for var_name, item in ds_info['variables'].items():
        if not item['time_varying']: continue
        if var_name == time_var : continue
        # only look at time varying variables, which are not time
        time = np.empty((0,), dtype=np.float64)
        for fID in item['fileIDs']:
            time = np.append(time, fi[fID]['time'])
            fi[fID]['first_time_step_in_file'] = time.size - fi[fID]['time_steps']
            fi[fID]['last_time_step_in_file'] = time.size - 1
        #print('xx',var_name,  fi[fID]['first_time_step_in_file'],  fi[fID]['last_time_step_in_file'] )
        item['time'] =  time


    # if variables in different files, eg schism v5, time may be in many files,
    #  only use file IDs for the ones for the first water velocity variable, which must always be in hindcasts
    vel_var0= reader.params['field_variable_map']['water_velocity'][0]
    time =  ds_info['variables'][vel_var0]['time']
    ds_info['time_coord'] = time

    if time.size < 2:
        si.msg_logger.msg('Velocity variable in hydro files has less than 2 time steps', hint = 'need at least 2 steps for particle tracking', fatal_error=True)

   # hindcast start and ends times from time_coord
    ds_info['start_time'] = time[0]
    ds_info['end_time'] = time[-1]
    ds_info['duration'] = time[-1] - time[0]
    ds_info['total_time_steps'] =  time.size
    ds_info['time_step'] = np.median(np.diff(time)) # tim syep but try to aviod glitched is hindcast times due to missing files

    ds_info['start_date'] = time_util.seconds_to_isostr(ds_info['start_time'])
    ds_info['end_date'] = time_util.seconds_to_isostr(ds_info['end_time'])
    ds_info['dates'] = time_util.seconds_to_isostr( time)

    pass

def _catalog_fields(reader, crumbs=None):
    # categorise field variables
    params = reader.params
    info = reader.info

    file_vars = info['variables']
    reader_field_vars_map = {}

    # loop over mapped variables and loaded variables
    mapped_fields = params['field_variable_map']
    for name in list(set(params['load_fields'] + list(mapped_fields.keys()))):
        # if named var not in map, try to use is name as a map,
        # ie load named field is a file varaiable name
        if name not in mapped_fields:
            mapped_fields[name] = name
            if name not in info['variables']:
                si.msg_logger.msg(
                    f' No  field_variable_map to load variable named "{name}" and no variable in file matching this name, so can not load this field',
                    hint=f'Add a map for this variable readers "field_variable_map"  param or check spelling loaded variable name matches a file variable, current map is {str(mapped_fields)}',
                    fatal_error=True)

        # decompose variable list

        var_list = mapped_fields[name]
        if var_list is None: continue # no default
        if type(var_list) != list: var_list = [var_list]  # ensure it is a list
        if len(var_list) == 0: continue

        # use first variable to get basic info
        v1 = var_list[0]

        if v1 not in file_vars: continue

        field_params = dict(time_varying=file_vars[v1]['time_varying'],
                            is3D=any(x in info['all_z_dims'] for x in file_vars[v1]['dims']),  )
        field_params['zlevels'] = info['num_z_interfaces'] if field_params['is3D'] else 1

        # work out if variable is a vector field
        file_vars_info = {}

        dm = params['dimension_map']
        for n_var, v in enumerate(var_list):
            if v not in file_vars: continue  # listed var not in file, eg vecotion variable has npo vertical velocity

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
    # add grid variable info
    si.msg_logger.exit_if_prior_errors('Errors matching field variables with those in the file, see above')

def _check_input_dir(reader_params,crumbs=''):
    ml = si.msg_logger
    crumbs = crumbs + '> check_input_dir'
    # check params and folders exists
    if 'input_dir' not in reader_params or 'file_mask' not in reader_params:
        ml.msg('Reader class requires settings, "input_dir" and "file_mask" to read the hindcast',
               fatal_error=True, crumbs=crumbs)
    # check input dir exists
    if path.isdir(reader_params['input_dir']):
        ml.progress_marker(f'Found input dir "{reader_params["input_dir"]}"')
    else:
        ml.msg(f'Could not find input dir "{reader_params["input_dir"]}"',
               hint='Check reader parameter "input_dir"', fatal_error=True)

    # file mask is optional
    if 'file_mask' not in reader_params: reader_params['file_mask'] = None


def _make_variable_time_step_to_fileID_map(reader):

    # make time step to fileID map and file offset map for every time step, accounting for each variable's file order
    info = reader.dataset.info
    for v_name, item in info['variables'].items():
        if not item['time_varying']: continue

        time_step_fileID_map = np.zeros((0,),dtype=np.int32)
        time_step_file_offset_map = np.zeros((0,), dtype=np.int32)

        for fileID in  item['fileIDs']: #IDs have aleady been time sorted
            fi = info['files'][fileID]
            time_step_fileID_map =  np.append(time_step_fileID_map,fi['ID']*np.ones(( fi['time_steps'] ,), dtype=np.int32))
            time_step_file_offset_map = np.append(time_step_file_offset_map,  np.arange(fi['time_steps'], dtype=np.int32))
            pass

        item['time_step_to_fileID_map'] = time_step_fileID_map
        item['time_step_to_file_offset_map'] = time_step_file_offset_map
        pass
    pass


def _hindcast_integrity_checks(reader):
    # todo , not ey used, put call in fgm final setup after all classes set up?
    params = reader.params
    info = reader.info
    file_vars = info['variables']
    ml = si.msg_logger
    vars =[]

    # check needed fields  are present
    for name, i in reader.fields.items():
        if 'file_vars_info' not in i.info: continue  # only do reader fiields
        for var_name in i.info['file_vars_info'].keys():
            vars.append(var_name)
            if var_name not in file_vars:
                ml.msg(f'Reader field {name}, file variable{var_name} is not in hindcast files', caller=reader, fatal_error=True)



        pass
    ml.progress_marker('passed hindcast integrity checks', caller = reader)
    return


def _check_time_consistency(reader):
    # check all variables have same time_step_to_fileID_map, and save one version of it
    #todo do not currently used, reactivate?
    info= reader.info
    ml = si.msg_logger

    dt = np.abs( np.diff(reader.info['time_coord']))

    # look for repeated time steps, eg, from  data servive which repeats last step in next file as first in next file
    sel = dt < 0.1 * reader.info['time_step']
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
        si.msg_logger.msg(f'Hindcasts has repeated time steps, space as les tha .8*time_step, ignoring repeats,  eg. at {time_util.seconds_to_isostr(t1[0])}',
                          hint=' see hindcast_info.json for list of repeats. Used a hindcast download service?,\n it may repeat last time step in file as first tim step in next file  ',
                          warning = True)

        reader.info['time_step_repeats'] = [[time_util.seconds_to_isostr(a), time_util.seconds_to_isostr(b)] for a, b in zip(t1, t2)]

    sel = np.flatnonzero( dt > 3 * reader.info['time_step'])
    if np.any(sel):
        t1 = reader.info['time_coord'][sel]
        t2 = reader.info['time_coord'][sel+1]

        si.msg_logger.msg('Some hindcast time steps are longer than 3 average time steps',error=True,
                        hint = f'Hindcast may be missing files or othe time error, eg at {time_util. seconds_to_isostr(t1[0])} to {time_util. seconds_to_isostr(t2[0])}, see hindcast_info.json for full list of dates', warning=True)

        for d1,d2  in [ [time_util. seconds_to_isostr(a),time_util. seconds_to_isostr(b) ] for a,b in zip(t1,t2) ]:
            si.msg_logger.msg(f'Gap from {d1}  to {d2}' , error=True, tabs=2)

        si.msg_logger.msg('Hindcast must have all time steps', fatal_error=True,
                            hint=f'Find missing files, check al time steps are in all files, covering above time gaps')



    return