import  argparse
from os import path,chdir, mkdir
from oceantracker import definitions
from glob import glob
import importlib
import  sys

from  unit_tests import common_definitions as cd
from oceantracker.util import json_util, yaml_util
import dev_runs.test_definitions
import oceantracker.main
import inspect

def get_test_num(name):
    return int(name.split('test')[1].split('_')[0])

if __name__ == "__main__":

    args = cd.get_args()

    files_dir = path.join(path.dirname(__file__),'unit_tests')

    sys.path.append(files_dir)

    for fname in glob( path.join(  files_dir ,'test*.py')):
        mod_name = path.basename(fname).split('.')[0]
        if get_test_num(mod_name) != args.mod: continue
        mod = importlib.import_module( mod_name)
        for name, F in inspect.getmembers(mod):
            if not inspect.isfunction(F): continue
            if get_test_num(name) != args.test: continue
            F()
