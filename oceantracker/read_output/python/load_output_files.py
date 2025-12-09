# these are wrappers for  read_ncdf_output_files equivalents but load from runcase_info file name
import numpy as np

from oceantracker.util import json_util
from oceantracker.read_output.python import read_ncdf_output_files
from os import path


def read_case_info_file(case_info_file_name):
    # load runInfo and given case case_infofiles into dict
    # runcase_info is used as input for all particle_plot methods
    # if dir of case info does not match that in the case_info.json, then it is changed to match given name

    if type(case_info_file_name) == list:
        print('Warning: case_info_file is a list from a parallel run, loading first case, ie case_info_file[0], if another case required use read_case_info_file(case_info_file[n]) ')
        case_info = json_util.read_JSON(case_info_file_name[0])
    else:
        case_info = json_util.read_JSON(case_info_file_name)

    # make case info output dir consistent with given file name
    case_info['output_files']['run_output_dir'] = path.dirname(case_info_file_name)
    case_info['output_files']['root_output_dir'] = path.dirname(case_info['output_files']['run_output_dir'])

    # force run out dir and root output dir to match that of case_info_file name if user has data in another folder name
    case_info['output_files']['run_output_dir']  = path.dirname(case_info_file_name)
    case_info['output_files']['root_output_dir'] = path.dirname(case_info['output_files']['run_output_dir'])
    return case_info


def load_track_data(case_info_file_name, var_list=None, fraction_to_read= None, file_number=None, gridID=0):
    # load one track file from squeuence of what may be split files
    # todo load split track files into  dictionary

    case_info = read_case_info_file(case_info_file_name)

    tracks = read_ncdf_output_files.merge_track_files(case_info['output_files']['tracks_writer'],
                                                              dir=case_info['output_files']['run_output_dir'],
                                                              var_list=var_list,
                                                              fraction_to_read=fraction_to_read)

    tracks['grid'] = load_grid(case_info_file_name,gridID=gridID)

    tracks= _extract_useful_info(case_info, tracks)
    x= tracks['x'][:,:,0]
    y = tracks['x'][:, :, 1]
    tracks['axis_lim'] = np.asarray([np.nanmin(x), np.nanmax(x),np.nanmin(y), np.nanmax(y)])
    return tracks

def _extract_useful_info(case_info, d):
    # get release group info
    if 'run_output_dir' in case_info['output_files']:
        prg_info = read_ncdf_output_files.read_release_groups_info(path.join(case_info['output_files']['run_output_dir'], case_info['output_files']['release_groups']))

    else:
        #todo deprecated from version 0.5
        prg_info = case_info['release_groups']

    d.update( particle_status_flags =case_info['particle_status_flags'],
              particle_release_groups= prg_info)

    return d

def load_grid(case_info_file_name, gridID=0):
    # load OT output file grid from  output of load_runInfo() or load_runcase_info()
    case_info = read_case_info_file(case_info_file_name)
    if type(case_info['output_files']['grid']) == list:
        grid_file = case_info['output_files']['grid'][gridID]
    else:
        # old version with only one grid file
        grid_file = case_info['output_files']['grid']

    grid_file = path.join(case_info['output_files']['run_output_dir'],grid_file)

    d = read_ncdf_output_files.read_grid_file(grid_file)

    if 'grid_outline' not in d:
        # todo deprecated from version 0.5, data now in netcdf grid file
        # load  json grid outline and convert outline to numpy arrays
        grid_outline_file = path.join(case_info['output_files']['run_output_dir'], case_info['output_files']['grid_outline'])
        d['grid_outline'] = read_ncdf_output_files.read_grid_outline_file(grid_outline_file)

        # make outline list np arrays for plotting
        for key in d['grid_outline']['domain']:
            d['grid_outline']['domain'][key] = np.asarray(d['grid_outline']['domain'][key])
        for n in range(len(d['grid_outline']['islands'])):
            for key in  d['grid_outline']['islands'][n]:
                d['grid_outline']['islands'][n][key]= np.asarray( d['grid_outline']['islands'][n][key])

    return d

def load_stats_data(case_info_file_name, name = None,nt=None):
    # load gridded or polygon stas file using runcase_info, the output of  load_runcase_info()

    case_info = read_case_info_file(case_info_file_name)
    name = _get_role_dict_name(case_info, 'particle_statistics', name)
    stat_nc_file_name = _get_role_dict_file_name(case_info, 'particle_statistics', name)
    d = read_ncdf_output_files.read_stats_file(stat_nc_file_name, nt=nt)

    d = _extract_useful_info(case_info, d)
    d['grid'] = load_grid(case_info_file_name)
    return d

def load_residence_file(case_info_file_name=None,name=None, var_list=[]):
    # load residence time in relese polygon

    case_info = read_case_info_file(case_info_file_name)
    name = _get_role_dict_name(case_info, 'particle_statistics', name)
    nc_file_name =  _get_role_dict_file_name(case_info, 'particle_statistics', name)
    d = read_ncdf_output_files.read_residence_file(nc_file_name, var_list)
    #d['info']= case_info['class_roles_info']['particle_statistics'][name]
    d['params'] = case_info['working_params']['class_roles']['particle_statistics'][name]

    d = _extract_useful_info(case_info, d)
    d['grid'] = load_grid(case_info_file_name)
    return d

def load_LSC(case_info_file_name):
    # load LCS
    case_info = read_case_info_file(case_info_file_name)
    fn = path.join(case_info['output_files']['run_output_dir'],case_info['output_files']['integrated_model'])
    d = read_ncdf_output_files.read_LCS(fn)
    d = _extract_useful_info(case_info, d)
    d['grid'] = load_grid(case_info_file_name)
    return d

def _get_role_dict_name(caseinfo, class_dict, name= None):
    o = caseinfo['output_files']
    c = o[class_dict]
    if name is None:
        name = list(caseinfo['class_roles_info'][class_dict].keys())[0]  # use first one
        print('Post processing ,no name given loading "' + class_dict + '" named  "' + name + '"')
    if name not in c:
        raise Exception('Post processing error, "' + class_dict + '" does not have class name  "' + name + '"')
    return name

def _get_role_dict_file_name(caseinfo, class_dict, name=None):
    # val is astring name of relese group ot integer
    o = caseinfo['output_files']
    name =  _get_role_dict_name(caseinfo, class_dict, name= name)
    return path.join(o['run_output_dir'],o[class_dict][name])

# ubder dev
def dev_load_events_file(case_info_file_name, name=None):
    # load  flat events
    #todo finish
    case_info = read_case_info_file(case_info_file_name)
    nc_file_name = _get_role_dict_file_name(case_info, 'event_loggers', name)
