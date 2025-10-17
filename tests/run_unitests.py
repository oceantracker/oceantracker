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



if __name__ == "__main__":

    args = cd.get_args()

    files_dir = path.join(path.dirname(__file__),'unit_tests')

    sys.path.append(files_dir)

    # build dict of tests
    tests={}
    for fname in glob( path.join(  files_dir ,'test*.py')):
        mod_name = path.basename(fname).split('.')[0]

        mod = importlib.import_module( mod_name)
        for name, F in inspect.getmembers(mod):
            if not inspect.isfunction(F): continue
            tests[cd.get_test_num(name)] = F

    # run all or one test
    for number, F in tests.items():
        if not args.test and number != args.test: continue
        F()
