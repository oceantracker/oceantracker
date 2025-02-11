import argparse
import sys
from os import  path
from oceantracker.util import yaml_util
from oceantracker.util import json_util
from oceantracker import main

def tweak_params(params, args):

    # override top level shared_params in json within any given arguments
    if args.root_output_dir: params['root_output_dir'] = args.root_output_dir
    if args.input_dir: params['reader']['input_dir'] = args.input_dir
    if args.processors: params['processors'] = args.processors
    if args.duration: params['max_run_duration'] = args.duration
    if args.debug: params['debug'] = args.debug

    return params


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('param_file', type=str,help='json or yaml file of input parameters')
    parser.add_argument('--input_dir', type=str,  help='overrides dir for hindcast files given in param file')
    parser.add_argument('--root_output_dir', type=str, help='overrides root output dir given in param file')
    parser.add_argument('--processors', type=int,  help='overrides number of processors in param file')
    parser.add_argument('--duration', type=float, help='in seconds, overrides model duration in seconds of all of cases, useful in testing ')
    parser.add_argument('--cases', type=int, help='only runs  first "cases" of the case_list, useful in testing ')
    parser.add_argument('-debug', action='store_true', help=' gives better error information, but runs slower, eg checks Numba array bounds')

    args = parser.parse_args()


    if args.param_file is None:
        sys.exit('Must give param file name eg  find parameter file, got ' + args.param_file)

    fn =path.abspath(args.param_file)
    if not path.isfile(fn):
        sys.exit('Cannot find parameter file ' + fn)

    file_ext = path.splitext(fn)[-1].lower()
    #print(file_ext)
    if file_ext== '.json':
        params= json_util.read_JSON(fn)

    elif file_ext  == '.yaml':
        params = yaml_util.read_YAML(fn)
    else:
        sys.exit('Parameter file must be *.yaml or *.json, is ' + args.param_file)

    params = tweak_params(params, args)

    caseInfo_file_name = main.run(params)
