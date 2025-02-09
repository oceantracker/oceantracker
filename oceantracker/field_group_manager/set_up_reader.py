import xarray as xr
import numpy as np
from copy import copy, deepcopy
from os import path
from glob import  glob

from oceantracker.shared_info import shared_info as si
from oceantracker import definitions
from oceantracker.util import  time_util
from oceantracker.reader._oceantracker_dataset import OceanTrackerDataSet

def make_a_reader_from_params(reader_params, settings, crumbs=''):
    crumbs = crumbs + '>build_a_reader '


    _check_input_dir(reader_params, crumbs=crumbs)
    dataset = OceanTrackerDataSet(reader_params)



    # detect reader format and add clas_name to params
    reader = _detect_hydro_file_format(reader_params, dataset,  crumbs=crumbs)

    if reader.development:
        si.msg_logger.msg(f'Class "{reader.__class__.__name__}" under development, it may not work in all cases',
                           hint=f' contact developer with any unexpected issues', warning=True)

    # sort files into time order and add info to reader bulider on if 3D hindcast and mapped field
    _time_sort_files(reader, crumbs)
    reader.dataset._make_time_step_to_fileID_map()

    info = reader.info
    info.update(reader.dataset.info) # make data set and reader info the same

    # additional info on vert grid etc, node dim etc
    reader.info.update(reader.get_hindcast_info())

    # checks on hindcast info
    # todo check all required fields are set
    if info['vert_grid_type'] is not None and info['vert_grid_type'] not in si.vertical_grid_types.possible_values():
        si.msg_logger.msg(f'Coding error, dont recognise vert_grid_type grid type, got {info["vert_grid_type"]}, must be one of [None , "Slayer_or_LSC","Zlayer","Sigma"]',
                hint=f'check reader codes  get_hindcast_info() ', error=True)

    catalog_fields(reader, crumbs=None)

    # set working vertical grid type,if remapping to sigma grids
    vgt = si.vertical_grid_types

    info['vert_grid_type_in_files'] = copy(info['vert_grid_type'])

    if info['vert_grid_type'] in [vgt.Slayer, vgt.LSC] and settings['regrid_z_to_uniform_sigma_levels']:
        info['vert_grid_type'] = vgt.Sigma
        info['regrid_z_to_uniform_sigma_levels'] = True

    elif info['vert_grid_type'] in [vgt.Sigma, vgt.Zfixed]:
        info['regrid_z_to_uniform_sigma_levels'] = False

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
        return reader

    # lok for reader amongst known readers
    reader = None

    tests ={} # set of tests to pass
    ds_info = dataset.info

    for name, class_name in definitions.known_readers.items():
        # first check if essential variables are in the file
        p = deepcopy(reader_params)
        p['class_name'] = class_name
        r = si.class_importer.make_class_instance_from_params('reader',p,
                              check_for_unknown_keys=False,  # dont flag unknown keys
                              crumbs=crumbs + f'> loading reader "{name}"  class name "{class_name}"')
        gmap = r.params['grid_variable_map']
        fmap= r.params['field_variable_map']
        t = dict(time = gmap['time'] in ds_info['variables'],
                x = gmap['x'] in ds_info['variables'],
                velocity = fmap['water_velocity'][0] in  ds_info['variables'] \
                        or fmap['water_velocity_depth_averaged'][0] in  ds_info['variables'])
        # check if other variables in the signature are present
        for s in r.params['variable_signature']:
            t[s] = s in ds_info['variables']

        tests[name] = t
        # break if all testes passed as found reader
        if all(t.values()):
            reader = r
            break

    if reader is None:
        ml.msg (f'Could not set up reader, could not detect file format  as not all expected variables are present ',
               hint=f'May be an unknown format, or unexpected differences in variable names to the expected format, varaibles {all_variables}',
               fatal_error=True, crumbs=crumbs)

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


    # first read start times of all files
    fi = ds_info['files']  # file names etc
    for ID, f in enumerate(ds_info['files']):
        ds = reader.dataset._open_file(f['name'])
        f['has_time'] =  ds_info['time_var'] in ds.variables
        if f['has_time']:
            time = ds[time_var].compute()
            time = reader.decode_time(time)
            f['start_time'] = float(time[0])
            f['end_time'] = float(time[-1])
            f['time_steps'] = time.size
            f['ID'] = ID
            f['time'] = time

    # sort variable fileIDs into time order, but maintain given file order

    for v_name, item in ds_info['variables'].items():
        item['time_varying'] = ds_info['time_dim'] in item['dims']
        if  item['time_varying']:
            item['fileIDs'] = np.asarray(item['fileIDs'])
            start_times = np.asarray([fi[x]['start_time'] for x in item['fileIDs']])
            file_order = np.argsort(start_times)
            item['fileIDs'] = item['fileIDs'][file_order]
            # get first time step in the file
            time_steps = np.asarray([fi[x]['time_steps'] for x in item['fileIDs']])
            first_time_step_in_file = np.cumsum(time_steps) - time_steps[0]
            # insert first time step into the file info in time order

            # this will be unnecessarily  repeated, if more than one variable in a file
            for n, fID in enumerate(item['fileIDs']):
                fi[fID]['first_time_step_in_file'] = first_time_step_in_file[n]

        else:
            item['fileIDs'] = item['fileIDs'][0]  # todo keep as list??

    # append times in order of time variable's file IDs
    time = np.empty((0,), dtype=np.float64)
    for ID in ds_info['variables'][ds_info['time_var']]['fileIDs']:
        time = np.append(time, ds_info['files'][ID]['time'])

    ds_info['ref_time'] = time

   # hindcast start and ends times
    ds_info['start_time'] = time[0]
    ds_info['end_time'] = time[-1]
    ds_info['duration'] = time[-1]- time[0]
    ds_info['total_time_steps'] =  time.size
    ds_info['time_step'] = ds_info['duration']/(time.size-1)

    ds_info['start_date'] = time_util.seconds_to_isostr(ds_info['start_time'])
    ds_info['end_date'] = time_util.seconds_to_isostr(ds_info['end_time'])

    pass



def catalog_fields(reader, crumbs=None):
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

        # decompose variabele lis
        var_list = mapped_fields[name]
        if type(var_list) != list: var_list = [var_list]  # ensure it is a list

        # use first variable to get basic info
        v1 = var_list[0]
        if v1 not in file_vars: continue

        field_params = dict(time_varying=file_vars[v1]['time_varying'],
                            is3D=any(x in info['all_z_dims'] for x in file_vars[v1]['dims']),
                            )
        field_params['zlevels'] = info['num_z_levels'] if field_params['is3D'] else 1

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
                   info['num_z_levels'] if field_params['is3D'] else 1,
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


