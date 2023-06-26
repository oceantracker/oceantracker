# this fiel must
import pkgutil
import inspect
import traceback
from os import path, walk, listdir
import glob
from importlib import import_module
from oceantracker.util.parameter_base_class import ParameterBaseClass

from oceantracker.common_info_default_param_dict_templates import package_fancy_name


import inspect
import importlib
import pkgutil

import os
import importlib
import inspect

def get_all_classes(module_name):
    module = importlib.import_module(module_name)
    classes = []

    for loader, name, is_pkg in pkgutil.walk_packages(module.__path__):
        if is_pkg:
            sub_module = f"{module_name}.{name}"
            classes.extend(get_all_classes(sub_module))
        else:
            sub_module = importlib.import_module(f"{module_name}.{name}")
            sub_module_classes = inspect.getmembers(sub_module, inspect.isclass)
            classes.extend(sub_module_classes)

    return classes




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

def build_short_class_name_map(package_dir,msg_list):

    files = glob.glob(path.join(package_dir,'**','*.py'),recursive=True)
    out={}

    for name in files:

        modname = 'oceantracker' + name.split(package_dir)[1].replace('\\','.').replace('.py','')

        try:
            module = import_module(modname)
        except Exception as e:
            print('Could not load oceantracker module ="' +  modname +'"'
                        +', May be sytax error or import error in oceantracker'+ traceback.format_exc())
            return out, msg_list

        for class_name, c in inspect.getmembers(module, inspect.isclass):
            if not issubclass(c, ParameterBaseClass): continue
            if len(inspect.signature(c.__init__).parameters) != 1: continue# only look at these with no __init__ argmuments and make an instance to get defaults created there
            if not inspect.isclass(c): continue
            if c.__module__ != module.__name__: continue  # only work on locally declared classes
            instance = c()
            full_name = modname + '.' + class_name
            if class_name in out:
                print('Class names within the OceanTracker package must be unique, class name = ' +
                               class_name +' is in both :\n' + '    ' + out[class_name] +'\n    ' + full_name+ traceback.format_exc())
                return out, msg_list
            else:
                out[class_name] = full_name

    return out, msg_list

def check_package(calling_file):
    # calling file must be in the root dir of package ie oceantracker_main
    package_dir = path.dirname(calling_file)
    d= {'package_dir': package_dir,
        'package_name': package_dir.split('\\')[-1],
        'short_class_name_map':{}}
    msg_list=[]
    msg_base= package_fancy_name +'-package checks: '
    print('____________________________________________________')
    print(msg_base +' Started for package in ' + d['package_dir'])

    d['short_class_name_map'] =  build_short_class_name_map(package_dir, msg_list)
    print( msg_base + ' OK')

    return d, msg_list

