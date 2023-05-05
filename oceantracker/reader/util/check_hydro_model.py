from oceantracker.util.ncdf_util import NetCDFhandler
from glob import  glob
from os import path
from oceantracker.common_info_default_param_dict_templates import default_reader
# check imput files exist and work out what type of file

def check_fileformat(reader_params, msg_logger):
    input_dir =path.normpath(reader_params['input_dir'])

    #first check if folder exists
    if not path.isdir(input_dir):
        msg_logger.msg('Cannot find hydro-model file directory= ' + str(input_dir), fatal_error=True,exit_now=True,
                       hint='check reader parameter "input_dir"')

    file_mask = reader_params['file_mask']
    file_names = glob(path.normpath(path.join(input_dir,file_mask)))
    if len(file_names)==0:
        msg_logger.msg('No hydro-model files found in input_dir, or its sub-dir whih matching file mask = ' + str(file_mask),
                       fatal_error=True, exit_now=True,  hint='check reader parameter "file_mask"')

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

        reader_params['class_name']  = default_reader[cl]
        msg_logger.progress_marker('found hydro-model files of type ' + cl.upper())

    return reader_params


