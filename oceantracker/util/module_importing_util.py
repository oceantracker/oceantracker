from oceantracker.util.message_and_error_logging import MessageClass
from importlib import import_module
import traceback

def import_module_from_string(s):
    # module reference, with or without param dict

# replace  short nclas namw with long name if possible
    #if s in package_info['short_class_name_map']: s= package_info['short_class_name_map'][s]

    try:
        ss = s.rsplit('.', 1)
        module_object = import_module(ss[0])
    except Exception as e:
        msg =MessageClass('Failed to find/load module given by string in or before __init__() "' + s + '"',
                          hint='Module names are case sensitive?, sytax error in module?, import error within module?',
                          exception=e, traceback_str=traceback.print_exc())
        return None, msg
    # make instance
    try:
        instance = getattr(module_object, ss[1])()  # an instance
        return instance, None
    except Exception as e:

        msg= MessageClass('Failed create instance from imported module given by string "' + s + '" ' ,
                          hint='Sytax error in module or its imports? cannot find an import?',
                          exception=e, traceback_str=traceback.print_exc())
        return None, msg





