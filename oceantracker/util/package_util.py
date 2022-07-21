# this fiel must
import pkgutil
import inspect
import traceback
from os import path, walk
from importlib import import_module
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.message_and_error_logging import append_message, GracefulExitError
from oceantracker.common_info_default_param_dict_templates import package_fancy_name

# def get package name
def get_package_name():
    return __package__.split('.')[0]

def get_package_dir():
    return path.join(get_root_package_dir(), get_package_name())

def get_root_package_dir():
    n= __file__.rfind(get_package_name())
    root_package_dir = __file__[:n-1]
    return root_package_dir

def package_relative_file_name(file_name):
    return file_name.split(get_root_package_dir() + '\\')[-1].replace('\\','/')
# not working yet
def build_short_class_name_map(d, calling_file):
    msg_list= []
    msg_base= package_fancy_name +'-package checks: '
    append_message(msg_list, '____________________________________________________')
    append_message(msg_list,msg_base +' Started for package in ' + d['package_dir'])

    for root, dirs, files in walk(d['package_dir']):
        for name in files:
            if name[0] == '': continue
            file_name = path.join(root, name)
            if  ispkg: continue
            try:
                file_name = pkgutil.resolve_name(modname).__file__
            except Exception as e:
                append_message(msg_list, 'Could resolve module name ="' + modname + '"'
                               + ', May be sytax error or import error in oceantracker',
                               exception=e, traceback_str=traceback.format_exc())
                return d, msg_list

            # dont work on those or the calling file to aviod circular imports
            if file_name == calling_file : continue
            if file_name== __file__ : continue

            try:
                module = import_module(modname)
            except Exception as e:
                append_message(msg_list,'Could not load oceantracker module ="' +  modname +'"'
                            +', May be sytax error or import error in oceantracker',
                               exception=e, traceback_str=traceback.format_exc())
                return d, msg_list

            for class_name, i in inspect.getmembers(module, inspect.isclass):
                if not issubclass(i, ParameterBaseClass): continue
                if len(inspect.signature(i.__init__).parameters) != 1: continue# only look at these with no __init__ argmuments and make an instance to get defaults created there
                if not inspect.isclass(i): continue
                if i.__module__ != module.__name__: continue  # only work on locally declared classes
                instance = i()
                full_name = modname + '.' + class_name
                if class_name in d:
                    append_message(msg_list,'Class names within the OceanTracker package must be unique, class name = ' +
                                   class_name +' is in both :\n' + '    ' + d[class_name] +'\n    ' + full_name,
                                   modname, exception=GracefulExitError)
                    return d, msg_list
                else:
                    d['short_class_name_map'][class_name] = full_name
    append_message(msg_list, msg_base + ' OK')
    return d, msg_list

def check_package(calling_file):
    # calling file must be in the root dir of package ie oceantracker_main
    package_dir = path.dirname(calling_file)
    d= {'package_dir': package_dir,
        'package_name': package_dir.split('\\')[-1],
        'short_class_name_map':{}}
    msg_list=[]
    #d, msg_list =  build_short_class_name_map(d,calling_file)
    return d, msg_list

