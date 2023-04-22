import argparse
import sys
from os import  path
from oceantracker.util import yaml_util
from oceantracker.util import json_util
from oceantracker import main


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--param_file', type=str,help='json or yaml file of input parameters')
    parser.add_argument('--input_dir', type=str,  help='overrides dir for hindcast files given in param file')
    parser.add_argument('--root_output_dir', type=str, help='overrides root output dir given in param file')
    parser.add_argument('--processors', type=int,  help='overrides number of processors in param file')
    parser.add_argument('--replicates', type=int,  help='overrides number of case replicates given in param file')
    parser.add_argument('--duration', type=float, help='in seconds, overrides model duration in seconds of all of cases, useful in testing ')
    parser.add_argument('--cases', type=int, help='only runs  first "cases" of the case_list, useful in testing ')
    parser.add_argument('-debug', action='store_true', help=' gives better error information, but runs slower, eg checks Numba array bounds')

    args = parser.parse_args()

    if not path.isfile(path.normpath(args.param_file)):
        sys.exit('Cannot find parameter file ' + args.param_file)

    print(args)
    file_ext = path.splitext(args.param_file)[1].lower()

    if file_ext== '.json':
        params= json_util.read_JSON(args.param_file)

    elif file_ext  == '.yaml':
        params = yaml_util.read_YAML(args.param_file)
    else:
        sys.exit('Parameter file must be *.yaml or *.json, is ' + args.param_file)

    # override top level shared_params in json within any arguments
    if args.root_output_dir : params['shared_params']['root_output_dir'] = args.root_output_dir
    if args.input_dir       : params['reader']['input_dir']      = args.input_dir
    if args.processors      : params['shared_params']['processors']     = args.processors
    if args.duration        : params['shared_params']['max_duration']   = args.duration
    if args.debug           : params['shared_params']['debug']          = args.debug

    # do fewer cases in debugging
    if args.cases:  params['case_list'] =  params['case_list'][:min([args.cases,len(params['case_list'])])]

    print(str(args))
    runInfo_file_name, has_errors = main.run(params)
