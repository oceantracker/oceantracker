import xarray as xr
from copy import copy, deepcopy
from os import path
from glob import  glob

from oceantracker.shared_info import shared_info as si
from oceantracker import definitions


def make_a_reader_from_params(reader_params, settings, msg_logger, crumbs=''):
    crumbs = crumbs + '>build_a_reader '


    file_list = _check_input_dir(reader_params, crumbs=crumbs)

    known_readers, all_variables, all_dims =  _get_known_readers_variables_and_dims(reader_params,file_list, crumbs)

    # detect reader format and add clas_name to params
    reader = _detect_hydro_file_format(reader_params, known_readers, all_variables, all_dims, crumbs=crumbs)

    if reader.development:
        msg_logger.msg(f'Class "{reader.__class__.__name__}" under development, it may not work in all cases',
                           hint=f' contact developer with any unexpected issues', warning=True)


    info = reader.info

    # additional info on vert grid etc, node dim etc
    reader.info.update(reader.get_hindcast_info())

    # sort files into time order and add info to reader bulider on if 3D hindcast and mapped field
    reader.catalog_dataset(msg_logger=msg_logger, crumbs=crumbs)

    # set working vertical grid type,if remapping to sigma grids
    vgt = si.vertical_grid_types

    info['vert_grid_type_in_files'] = copy(info['vert_grid_type'])

    if info['vert_grid_type'] in [vgt.Slayer, vgt.LSC] and settings['regrid_z_to_uniform_sigma_levels']:
        info['vert_grid_type'] = vgt.Sigma
        info['regrid_z_to_uniform_sigma_levels'] = True

    elif info['vert_grid_type'] in [vgt.Sigma, vgt.Zfixed]:
        info['regrid_z_to_uniform_sigma_levels'] = False

    elif info['is3D']:
        msg_logger.msg(f'Unknown grid vertical type "{info["vert_grid_type"]}"',
                       hint=f'must be one of {str(vgt.possible_values())}',
                       fatal_error=True)

    info['has_A_Z_profile'] = 'A_Z_profile' in info['field_info']
    info['has_bottom_stress'] = 'bottom_stress' in info['field_info']
    # work out in 3D run from water velocity
    info['geographic_coords'] = reader.detect_lonlat_grid(msg_logger)
    info['time_buffer_size'] = si.settings.time_buffer_size

    return reader

def _get_known_readers_variables_and_dims(reader_params,file_list, crumbs):
    # get dict of known  reader instances  and file variables and dims
    known_readers = {}
    drop_variables = []
    for name, r in definitions.known_readers.items():
        params = deepcopy(reader_params)
        params['class_name'] = r
        reader = si.class_importer.make_class_instance_from_params('reader',
                                                                   params, check_for_unknown_keys=False,  # dont flag unknown keys
                                                                   crumbs=crumbs + f'> loading reader "{name}"  class "{r}"')
        known_readers[name] = reader
        drop_variables += reader.params['drop_variables']  # find all problematic variables to drop

    # look through files to see which reader's signature matches
    # must check all files as variables may be split between files

    all_variables = []
    all_dims = {}
    for fn in file_list:
        ds = xr.open_dataset(fn, decode_times=False, drop_variables=drop_variables)
        all_variables += list(ds.variables.keys())
        all_dims.update(ds.sizes)
        ds.close()
    all_variables = sorted(list(set(all_variables)))  # unique list of variables

    return known_readers, all_variables, all_dims

def _detect_hydro_file_format(reader_params, known_readers, all_variables, all_dims, crumbs=''):
    # detect hindcast format and add reader class_name to params if missing
    # return reader class_name if given
    #todo show which tests passed for each reader
    ml = si.msg_logger
    crumbs += '> detecting reader file format '
    if 'class_name' in reader_params:
        reader = si.class_importer.make_class_instance_from_params('reader',
                                     reader_params, check_for_unknown_keys=True,
                                     crumbs=crumbs + f'> loading given reader with class_name "{reader_params["class_name"]}"')
        reader.info['variables'] = all_variables
        reader.info['dims'] = all_dims
        return reader

    # lok for reader amonst known readers
    reader = None

    tests ={} # set of tests to pass

    for name, r in known_readers.items():
        # first check if essential variables are in the file
        gmap = r.params['grid_variable_map']
        fmap= r.params['field_variable_map']
        t = dict(time = gmap['time'] in all_variables,
                x = gmap['x'] in all_variables,
                velocity = fmap['water_velocity'][0] in  all_variables \
                        or fmap['water_velocity_depth_averaged'][0] in  all_variables)
        # check if other variables in the signature are present
        for s in r.params['variable_signature']:
            t[s] = s in all_variables

        tests[name] = t
        # break if all testes passed as found reader
        if all(t.values()):
            reader = r
            break

    if reader is None:
        ml.msg (f'Could not set up reader, could not detect file format  as not all expected variables are present ',
               hint=f'May be an unknown format, or unexpected differences in variable names to the expected format, varaibles {all_variables}',
               fatal_error=True, crumbs=crumbs)

    reader.info['variables'] = all_variables
    reader.info['dims'] = all_dims
    ml.progress_marker(f'Detected reader class_name = "{reader.__class__.__module__}.{reader.__class__.__name__}"')
    return reader


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

    # get the file_list
    # check files are there
    mask = path.join(reader_params['input_dir'], '**', reader_params['file_mask'])  # add subdir search
    file_list = glob(mask, recursive=True)
    if len(file_list) == 0:
        si.msg_logger.msg(f'No files found in input_dir, or its sub-dirs matching mask "{mask}"',
                       hint=f'searching with "gob" mask "{mask}"', fatal_error=True)
    return file_list
