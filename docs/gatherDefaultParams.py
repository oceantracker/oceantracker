# serach all classes  in oceantracker package to extract defaults

from oceantracker.util import basic_util
import inspect
from importlib import import_module
from oceantracker.util.parameter_base_class import ParameterBaseClass
import pkgutil

def build_default_param_dict():

    d={}
    n=0
    for importer, modname, ispkg in  pkgutil.walk_packages(['..\\oceantracker']):
        if  ispkg: continue
        module = import_module(modname)
        print(module.__name__)

        # look for classes in the imporeted module
        for c in inspect.getmembers(module, inspect.isclass):
            if c[1].__module__ !=  module.__name__ : continue  # only work on locally declared claseses

            if len(inspect.signature(c[1].__init__).parameters) == 1:
                # only look at these with no __init__ argmument and make an instance to get defaults created there
                i = c[1]()
                if issubclass(i.__class__, ParameterBaseClass):
                    # find where to place defaults in d
                    key_loc= d

                    for kk in i.__module__.split('.'):
                        if kk not in key_loc:
                            key_loc[kk]={}
                        key_loc = key_loc[kk]

                    # get defaults by dummy merge
                    i. merge_with_class_defaults({},{})
                    key_loc.update(i.params)

    return d

if __name__ == '__main__':

    d= build_default_param_dict()

    a= list(d.keys())
    a.sort()
    d2={}
    for key in a:
        d2[key]= d[key]
    json_util.write_JSON('all_default_parameters.json', d2)