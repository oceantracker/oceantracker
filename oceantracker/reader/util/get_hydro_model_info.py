from oceantracker.util.ncdf_util import NetCDFhandler
from glob import  glob
from os import path
from oceantracker.common_info_default_param_dict_templates import default_reader
from pathlib import Path as pathlib_Path

def get_hydro_file_list(input_dir,file_mask, msg_logger):
    # get a list of hydrofile list

    if not path.isdir(input_dir):
        msg_logger.msg(f'Reader cannot find "input_dir"  = {input_dir}', fatal_error=True, exit_now=True)

    msg_logger.progress_marker(f'Searching for  hydro-files in "{input_dir}" matching mask "{file_mask}"')
    file_list = []
    for fn in pathlib_Path(input_dir).rglob( file_mask):
        file_list.append(path.abspath(fn))

    msg_logger.progress_marker(f'Found {len(file_list)} files', tabs =2)

    if len(file_list) == 0:
        msg_logger.msg(f'Reader cannot find any files in "{input_dir}" matching mask "{file_mask}"', fatal_error=True, exit_now=True)

    return file_list

# check imput files exist and work out what type of file

def check_fileformat(reader_params,file_names, msg_logger):
    input_dir =path.normpath(reader_params['input_dir'])

    # open first file to deterime format
    if 'class_name' not in reader_params or (reader_params['class_name'] is None and reader_params['class_instance'] is None):
        # check first file
        nc = NetCDFhandler(file_names[0])

        if nc.is_var('SCHISM_hgrid_node_x'):
            cl = 'schisim'

        elif set(['Times','nv', 'u', 'v', 'h']).issubset(list(nc.variable_info.keys())) :
            cl ='fvcom'

        elif set(['ocean_time','mask_psi','lat_psi','lon_psi','h','zeta','u','v']).issubset(list(nc.variable_info.keys())) :
            cl = 'roms'
        else:
            msg_logger.msg('reader class_name given and hydro files file variables do not match know types ' + str(file_mask),
                           fatal_error=True, exit_now=True,
                           hint='check files are netcf and expected format, or try to set up a generic reader  "file_mask"')

        reader_params['class_name'] = default_reader[cl]
        msg_logger.progress_marker('found hydro-model files of type ' + cl.upper())

    return reader_params


