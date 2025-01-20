import xarray as xr
from copy import copy, deepcopy
from os import path
from glob import  glob

from oceantracker.shared_info import shared_info as si
from oceantracker import definitions


def make_a_reader_from_params(reader_params, settings, msg_logger, crumbs=''):
    crumbs = crumbs + '>build_a_reader '


    file_list = _check_input_dir(reader_params, crumbs=crumbs)

    # detect reader format and add clas_name to params
    reader = _detect_hydro_file_format(reader_params, file_list, crumbs=crumbs)
    info = reader.info

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
    info['time_buffer_size'] = reader.params['time_buffer_size']

    return reader

def _detect_hydro_file_format(reader_params, file_list, crumbs=''):
    # detect hindcast format and add reader class_name to params if missing
    # return reader class_name if given
    ml = si.msg_logger
    crumbs += '> detecting reader file format '
    if 'class_name' in reader_params:
        reader = si.class_importer.make_class_instance_from_params('reader',
                                                                   reader_params, check_for_unknown_keys=True,
                                                                   crumbs=crumbs + f'> loading given reader with class_name "{reader_params["class_name"]}"')
        return reader

    # search all known readers for variable signature match
    # first build full set of instances of known readers
    # and their variable signatures
    known_readers ={}
    drop_variables =[]
    for name, r in definitions.known_readers.items():
        params = deepcopy(reader_params)
        params['class_name'] = r
        reader = si.class_importer.make_class_instance_from_params('reader',
                                                                   params, check_for_unknown_keys=False, # dont flag unknown keys
                                                                   crumbs=crumbs + f'> loading reader "{name}"  class "{r}"')
        known_readers[name] = dict(instance=reader,
                                   variable_sig = reader.params['variable_signature'],
                                   )
        drop_variables += reader.params['drop_variables'] # find all problematic variables to drop

    # look through files to see which reader's signature matches
    # must check all files as variables may be split between files
    found_reader = None
    all_variables= []
    for fn in file_list:
        ds = xr.open_dataset(fn, decode_times=False, drop_variables=drop_variables)
        all_variables += list(ds.variables.keys())
        ds.close()

    all_variables = list(set(all_variables)) # unique list of variables
    for name, r in known_readers.items():
        # check if each variable in the signature
        found_var = [v in all_variables for v in r['variable_sig']]
        # break if all variables are found for this reader
        if all(found_var):
            found_reader = name
            break

    if found_reader is None:
        ml.msg \
            (f'Could not set up reader, no files in dir = "{reader_params["input_dir"]} found matching mask = "{reader_params["file_mask"]}"  (or "out2d*.nc" if schism v5), or files do no match known format',
               hint='Check given input_dir and  file_mask params, check if any non-hydro netcdf files in the dir, otherwise may not be known format',
               fatal_error=True, crumbs=crumbs)
    # match found
    ml.progress_marker(f'found hydro-model files of type  "{found_reader.upper()}"')
    # return merged params
    # params = known_readers[found_reader]['instance'].params
    reader = known_readers[found_reader]['instance']

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
