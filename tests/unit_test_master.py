import  argparse
from os import path,chdir
from oceantracker import definitions
from glob import glob
import importlib
import  sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--test',type=int)
    parser.add_argument('-reference_case', action='store_true')
    parser.add_argument('-save_plots', action='store_true')

    args = parser.parse_args()
    if args.test:
        test_list = [args.test]
    else:
        test_list=[1,90]

    test_dir =path.join(definitions.ot_root_dir,'tests')
    info=[]
    files_dir = path.join(test_dir,'unit_tests')
    for n in glob(path.join(files_dir,'unit_*.py')):
        name = path.split(n)[-1].split('.')[0]
        info.append([ int(name.split('_')[2]),name])

    sys.path.append(files_dir)

    for n, name in info:
        if n in test_list:

            p = importlib.import_module(name)
            p.main(args)

