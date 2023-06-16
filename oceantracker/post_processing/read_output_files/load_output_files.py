# these are wrappers for  read_ncdf_output_files equivalents but load from runcase_info file name
import numpy as np

from oceantracker.util import json_util
from oceantracker.post_processing.read_output_files import read_ncdf_output_files
from os import path
from glob import glob



def get_case_info_file_from_run_file(runInfo_fileName_or_runInfoDict, ncase = 0, run_output_dir= None):
    # get case_info.json file name from runInfo dict or json file name, can also set root_output_dir, if output moved to new location
    # ncase is one based
    if type(runInfo_fileName_or_runInfoDict) is str:
       run_case_info = json_util.read_JSON(runInfo_fileName_or_runInfoDict)
    else:
        run_case_info = runInfo_fileName_or_runInfoDict

    if run_case_info is None:
        # file not found
       raise IOError('Could not read file' +runInfo_fileName_or_runInfoDict)

    if run_output_dir is None:
        run_output_dir = run_case_info['output_files']['run_output_dir']

    case_info_file_name = run_case_info['output_files']['case_info'][ncase]

    try:
        case_info_file_name = path.join(run_output_dir, case_info_file_name)

    except Exception as e:
        raise Exception('load_ouput_files.get_case_info: Can not find case file json "' + str(case_info_file_name) + "', file missing or case may have had an error see *.err file")

    return path.normpath(case_info_file_name)

def get_case_info_files_from_dir(dir_name, case = None):
    # get all case_info files in given folder, optionally only return given case file (first case is case = 1)
    # folder is cleaned out before start of run so any unfinished caseInfo.json files will  be missing
    # this method allows for missing cases from incomplete runs done in parallel, so  items in list = None for missing cases

    mask= path.join(dir_name, '*_caseInfo.json')
    case_file_names= glob(mask)

    if len(case_file_names)==0:  raise IOError('No case info files in dir '  + dir_name + ', matching mask *_caseInfo.json')

    # get cases as process IDs matching mask
    case_file_list, processorID = [], []
    for case_name in case_file_names:
        case_file_list.append(case_name)
        d = read_case_info_file(case_name)
        processorID.append(d['processorID'])

    # make a full list of cases from their processorID's,  which allows for any missing cases due to dead rund
    case_files_out = max(processorID+1)*[None]
    for ID, c in zip(processorID, case_file_list):
        case_files_out[ID] = c

    missing_cases = [i for i, x in enumerate(case_files_out) if x is None]
    if len(missing_cases) > 0: print('Warning  some cases file missing from dir ', dir_name, ', missing case files for case number(s) =', str( (np.asarray(missing_cases)).tolist()))

    # look for requested case
    if case is not None:
        if not ( 0 < case <= len(case_files_out) ):
            raise ValueError('Requested case number='+ str(case) + ' is outside range of available cases in dir' + dir_name + ', where there are ' + str(len(case_files_out)) + '  cases, (note first case is case = 1')
        if case_files_out[case-1] is None:
            raise ValueError('Requested case number='+ str(case) + ' is missing from dir = ' + dir_name + ', where there are ' + str(len(case_files_out)) + '  cases, (note first case is case =1)')
        case_files_out = case_files_out[case - 1]

    return case_files_out

def read_case_info_file(case_info_file_name):
    # load runInfo and given case case_infofiles into dict
    # runcase_info is used as input for all particle_plot methods

    case_info = json_util.read_JSON(case_info_file_name)

    # make case info output dir consistent with given file name
    case_info['output_files']['run_output_dir'] = path.dirname(case_info_file_name)
    case_info['output_files']['root_output_dir'] = path.dirname(case_info['output_files']['run_output_dir'])

    # force run out dir and root output dir to match that of case_info_file name if user has data in another folder name
    case_info['output_files']['run_output_dir']  = path.dirname(case_info_file_name)
    case_info['output_files']['root_output_dir'] = path.dirname(case_info['output_files']['run_output_dir'])
    return case_info

def load_particle_track_vars(case_info_file_name, var_list=None, release_group= None, fraction_to_read=None, track_file_number=1):
    # load one track file from squeuence of what may be split files
    # todo load split track files into  dictionary
    if var_list is None: var_list=[]
    var_list = list(set(var_list+['time', 'x','status'])) # default vars

    case_info = read_case_info_file(case_info_file_name)

    track_file = path.join( case_info['output_files']['run_output_dir'], case_info['output_files']['tracks_writer'][track_file_number-1])
    tracks = read_ncdf_output_files.read_particle_tracks_file(track_file, var_list, release_group=release_group, fraction_to_read=fraction_to_read)
    tracks['grid'] = load_grid(case_info_file_name)

    tracks= _extract_useful_info(case_info, tracks)
    x= tracks['x'][:,:,0]
    y = tracks['x'][:, :, 1]
    tracks['axis_lim'] = np.asarray([np.nanmin(x), np.nanmax(x),np.nanmin(y), np.nanmax(y)])
    return tracks

def _extract_useful_info(case_info, d):
    d.update({'particle_status_flags': case_info['particle_status_flags'],
                 'particle_release_group_info': case_info['particle_release_group_info']})
    d['full_case_params'] = case_info['full_case_params']

    return d

def load_concentration_vars(case_info_file_name, var_list=[], name= None):
    case_info = read_case_info_file(case_info_file_name)
    nc_file_name= _get_class_dict_file_name(case_info,'particle_concentrations', name)
    d = read_ncdf_output_files.read_concentration_file(nc_file_name, var_list=var_list)
    d['grid'] = load_grid(case_info_file_name)
    d =  _extract_useful_info(case_info, d)
    return d

def load_grid(case_info_file_name):
    # load OT output file grid from  output of load_runInfo() or load_runcase_info()
    case_info = read_case_info_file(case_info_file_name)
    grid_file = path.join(case_info['output_files']['run_output_dir'], case_info['output_files']['grid'])
    d = read_ncdf_output_files.read_grid_file(grid_file)

    # load  grid outline and convert outline to numpy arrays
    grid_outline_file = path.join(case_info['output_files']['run_output_dir'], case_info['output_files']['grid_outline'])
    d['grid_outline'] = read_ncdf_output_files.read_grid_outline_file(grid_outline_file)

    # make outline list np arrays for plotting
    for key in d['grid_outline']['domain']:
        d['grid_outline']['domain'][key] = np.asarray(d['grid_outline']['domain'][key])
    for n in range(len(d['grid_outline']['islands'])):
        for key in  d['grid_outline']['islands'][n]:
            d['grid_outline']['islands'][n][key]= np.asarray( d['grid_outline']['islands'][n][key])

    return d

def load_stats_file(case_info_file_name, name = None, var_list=[]):
    # load gridded or polygon stas file using runcase_info, the output of  load_runcase_info()

    case_info = read_case_info_file(case_info_file_name)
    stat_nc_file_name = _get_class_dict_file_name(case_info, 'particle_statistics', name)

    d= read_ncdf_output_files.read_stats_file(stat_nc_file_name, var_list)
    d['info']= case_info['class_info']['particle_statistics'][name]
    d['params'] = case_info['full_case_params']['class_dicts']['particle_statistics'][name]

    if 'release_group_centered_grids' in d['params'] and d['params']['release_group_centered_grids']:
        d['release_group_centered_grids'] = True
    else:
        d['release_group_centered_grids'] = False

    # add stats polygons to output, if stats grid its loaded by
    if 'polygon_list' in d['params']:
        d['polygon_list'] = d['params']['polygon_list']

    d = _extract_useful_info(case_info, d)
    d['grid'] = load_grid(case_info_file_name)
    return d

def load_residence_file(case_info_file_name=None,name=None, var_list=[]):
    # load residence time in relese polygon

    case_info = read_case_info_file(case_info_file_name)
    name = _get_class_dict_name(case_info, 'particle_statistics', name)
    nc_file_name =  _get_class_dict_file_name(case_info, 'particle_statistics', name)
    d = read_ncdf_output_files.read_residence_file(nc_file_name, var_list)
    d['info']= case_info['class_info']['particle_statistics'][name]
    d['params'] = case_info['full_case_params']['class_dicts']['particle_statistics'][name]

    d = _extract_useful_info(case_info, d)
    d['grid'] = load_grid(case_info_file_name)
    return d

def _get_class_dict_name(caseinfo, class_dict, name= None):
    o = caseinfo['output_files']
    c = o[class_dict]
    if name is None:
        name = list(caseinfo['class_info'][class_dict].keys())[0]  # use first one
        print('Post processing ,no name given loading "' + class_dict + '" named  "' + name + '"')
    if name not in c:
        raise ('Post processing error, "' + class_dict + '" does not have clas name  "' + name + '"')
    return name

def _get_class_dict_file_name(caseinfo, class_dict, name=None):
    # val is astring name of relese group ot integer
    o = caseinfo['output_files']
    name =  _get_class_dict_name(caseinfo, class_dict, name= name)
    return path.join(o['run_output_dir'],o[class_dict][name])

# ubder dev
def dev_load_events_file(case_info_file_name, name=None):
    # load  flat events
    #todo finish
    case_info = read_case_info_file(case_info_file_name)
    nc_file_name = _get_class_dict_file_name(case_info, 'event_loggers', name)
