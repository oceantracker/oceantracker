
from copy import deepcopy
from oceantracker.definitions import known_readers

def find_file_format_and_file_list(reader_params, class_importer, msg_logger, crumbs='', caller = None):
    found=False
    # first see if it matches known formats
    crumbs += '> find_file_format_and_file_list'''
    if 'class_name' in reader_params:
        reader = class_importer.make_class_instance_from_params('reader', reader_params, default_classID='reader', check_for_unknown_keys=False)
        if reader is None:
            msg_logger.msg(f'Error loading given reader  hydro-model files of type  "{reader_params["class_name"]}"', exit_now= True)
        file_list = reader.get_file_list()
        return reader_params, file_list

    # search
    for r_name, r in known_readers.items():
        params= deepcopy(reader_params)
        params['class_name'] = r
        reader = class_importer.make_class_instance_from_params('reader', params, default_classID='reader',
                                                                check_for_unknown_keys=False, crumbs = crumbs + f'> loading reader {r_name}', caller=caller)
        file_list = reader.get_file_list()

        if len(file_list) ==0:
            pass

        if len(file_list) > 0 and reader.is_file_format(file_list[0]):
            # found format
            if 'class_name' not in reader_params: reader_params['class_name'] = r # dont overwrite user given class name
            found = True
            break
    if found:
        msg_logger.progress_marker(f'found hydro-model files of type  "{r_name.upper()}"')
    else:
        msg_logger.msg(f'Could not set up reader, no files in dir = "{reader_params["input_dir"]} found matching mask = "{reader_params["file_mask"]}"  (or "out2d*.nc" if schism v5), or files do no match known format',
                        hint='Check given input_dir and  file_mask params, check if any non-hydro netcdf files in the dir, otherwise may not be known format',
                        fatal_error=True,  exit_now=True, crumbs= crumbs, caller=caller )
    return reader_params, file_list

def detect_file_format(file_catalog,reader_params, class_importer, msg_logger, crumbs='', caller = None):
    found=False
    # first see if it matches known formats
    crumbs += '> find_file_format_and_file_list'''
    if 'class_name' in reader_params:
        reader = class_importer.make_class_instance_from_params('reader', reader_params, default_classID='reader', check_for_unknown_keys=False)
        if reader is None:
            msg_logger.msg(f'Error loading given reader  hydro-model files of type  "{reader_params["class_name"]}"', exit_now= True)
        file_list = reader.get_file_list()
        return reader_params, file_list

    # search
    for r_name, r in known_readers.items():
        params= deepcopy(reader_params)
        params['class_name'] = r
        reader = class_importer.make_class_instance_from_params('reader', params, default_classID='reader',
                                                                check_for_unknown_keys=False, crumbs = crumbs + f'> loading reader {r_name}', caller=caller)
        file_list = reader.get_file_list()

        if len(file_list) ==0:
            pass

        if len(file_list) > 0 and reader.is_file_format(file_list[0]):
            # found format
            if 'class_name' not in reader_params: reader_params['class_name'] = r # dont overwrite user given class name
            found = True
            break
    if found:
        msg_logger.progress_marker(f'found hydro-model files of type  "{r_name.upper()}"')
    else:
        msg_logger.msg(f'Could not set up reader, no files in dir = "{reader_params["input_dir"]} found matching mask = "{reader_params["file_mask"]}"  (or "out2d*.nc" if schism v5), or files do no match known format',
                        hint='Check given input_dir and  file_mask params, check if any non-hydro netcdf files in the dir, otherwise may not be known format',
                        fatal_error=True,  exit_now=True, crumbs= crumbs, caller=caller )
    return reader_params, file_list




