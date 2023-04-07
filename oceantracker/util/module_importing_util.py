
from importlib import import_module
import traceback

def import_module_from_string(s,msg_logger):
    # module reference, with or without param dict

# replace  short nclas namw with long name if possible
    #if s in package_info['short_class_name_map']: s= package_info['short_class_name_map'][s]

    try:
        ss = s.rsplit('.', 1)
        module_object = import_module(ss[0])
        #module_object = __import__(ss[0]) # not working but faster option but less checks???
    except Exception as e:
        msg_logger.msg('Failed to find/load module given by string in or before __init__() "' + s + '"',
                          hint='Module names are case sensitive?, sytax error in module?, import error within module?',
                          fatal_error=True, exit_now=True, traceback_str = traceback.print_exc())

    # make instance
    try:
        instance = getattr(module_object, ss[1])()  # an instance

    except Exception as e:

        msg_logger.msg('Failed create instance from imported module given by string "' + s + '" ' ,
                          hint='Sytax error in module or its imports? cannot find an import?',
                          fatal_error=True, exit_now=True, traceback_str=traceback.print_exc())

    return instance




