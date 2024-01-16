import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util, json_util
from os import path, walk
from datetime import datetime
from copy import copy
from oceantracker.util.ncdf_util import NetCDFhandler
from time import perf_counter
from oceantracker.util.basic_util import nopass
from oceantracker.reader.util.reader_util import append_split_cell_data
import oceantracker.reader.util.hydromodel_grid_transforms as  hydromodel_grid_transforms

from oceantracker.util import  cord_transforms
from oceantracker.reader.util import shared_reader_memory_util
from oceantracker.util.profiling_util import function_profiler
from oceantracker.util import triangle_utilities_code
from oceantracker.util.triangle_utilities_code import split_quad_cells
from oceantracker.fields._base_field import  CustomFieldBase , ReaderField
from oceantracker.reader.util import reader_util
from oceantracker.reader._base_reader import _BaseReader
from copy import  deepcopy

class GenericNCDFreader(_BaseReader):

    def __init__(self, shared_memory_info=None):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({
            'input_dir': PVC(None, str, is_required=True),
            'file_mask': PVC(None, str, is_required=True, doc_str='Mask for file names, eg "scout*.nc", finds all files matching in  "input_dir" and its sub dirs that match the file_mask pattern'),
            'time_zone': PVC(None, int, min=-12, max=12, units='hours', doc_str='time zone in hours relative to UTC/GMT , eg NZ standard time is time zone 12'),
            'cords_in_lat_long': PVC(False, bool, doc_str='Convert given nodal lat longs to a UTM metres grid'),
            'vertical_regrid': PVC(True, bool, doc_str='Convert vertical grid to same sigma levels'),
            'time_buffer_size': PVC(24, int, min=2),
            'grid_variable_map': {'time': PVC('time',str, doc_str='time variable nae in file' ),
                               'x': PLC(['x', 'y'], [str], fixed_len=2),
                               'zlevel': PVC(None, str),
                               'triangles': PVC(None, str),
                               'bottom_cell_index': PVC(None, str),
                               'is_dry_cell': PVC(None, np.int8, doc_str='Time variable flag of when cell is dry, 1= is dry cell')},
            'load_fields': PLC([], [str], doc_str=' A list of names of any additional variables to read and interplolate to give particle values, eg. a concentration field (water_veloctiy, tide and water_depth fields are always loaded). If a given name is in field_variable_map, then the mapped file variables will be used internally and in output. If not the given file variable name will be used internally and in particle property output. For any additional vector fields user must supply a file variable map in the "field_variable_map" parameter',
                                   make_list_unique=True),
            'field_variable_map': {'water_velocity': PLC(['u', 'v', 'w'], [str, None], fixed_len=3, is_required=True, doc_str='maps standard internal field name to file variable names for velocity components'),
                                'tide': PVC('elev', str, doc_str='maps standard internal field name to file variable name'),
                                'water_depth': PVC('depth', str, is_required=True,doc_str='maps standard internal field name to file variable name'),
                                'water_temperature': PVC('temp', str,doc_str='maps standard internal field name to file variable name'),
                                'salinity': PVC(None, str,doc_str='maps standard internal field name to file variable name'),
                                'wind_stress': PVC(None, str,doc_str='maps standard internal field name to file variable name'),
                                'bottom_stress': PVC(None, str,doc_str='maps standard internal field name to file variable name'),
                                'water_velocity_depth_averaged': PLC(['u', 'v'], [str], fixed_len=2,
                                                                        doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')

                                   },
            'dimension_map': {'time': PVC('time', str, is_required=True),
                              'node': PVC('node', str),
                              'z': PVC(None, str,doc_str='name of dim for vertical layer boundaries'),
                              'z_water_velocity': PVC('z', str, doc_str='z dimension of water velocity'),
                              'vector2D': PVC(None, str),
                              'vector3D': PVC(None, str)},
            'CRS_transform_code':  PVC(None, int, doc_str='CRY code for coordinate conversion of hydro-model lon-lat to a meters grid , eg. CRS for NZTM is 2193'),

            'one_based_indices' :  PVC(False, bool,doc_str='indices in hindcast start at 1, not zero, eg. triangulation nodes start at 1 not zero as in python'),
            'isodate_of_hindcast_time_zero': PVC('1970-01-01', 'iso8601date'),
            'max_numb_files_to_load': PVC(10 ** 7, int, min=1, doc_str='Only read no more than this number of hindcast files, useful when setting up to speed run')
             })  # list of normal required dimensions

        self.info['field_variable_info'] = {}
        self.info['buffer_info'] ={}

    def is_file_format(self,file_name):
        # check if file matches this file format
        nc = NetCDFhandler(file_name,'r')
        gm = self.params['grid_variable_map']
        fm  = self.params['field_variable_map']
        dm = self.params['dimension_map']

        is_file_type=  nc.is_dim(dm['time']) and nc.is_dim(dm['node']) and nc.is_var(gm['x'][0]) and nc.is_var(gm['x'][1]) and nc.is_var(fm['tide']) and nc.is_var(fm['water_depth'])
        nc.close()
        return is_file_type

    def get_field_params(self, nc, name, crumbs=''):
        # work out if feild is 3D ,etc
        fmap = deepcopy(self.params['field_variable_map'][name])
        dim_map = self.params['dimension_map']

        if type(fmap) != list: fmap = [fmap]
        f_params = dict(time_varying=nc.is_var_dim(fmap[0], dim_map['time']),
                        is3D=nc.is_var_dim(fmap[0], dim_map['z']),
                        is_vector=nc.is_var_dim(fmap[0],  dim_map['vector2D']) or nc.is_var_dim(fmap[0],  dim_map['vector3D']) or len(fmap) > 1
                        )
        return f_params



    def sort_files_by_time(self,file_list, msg_logger):
        # get time sorted list of files matching mask

        fi = {'names': file_list, 'n_time_steps': [], 'time_start': [], 'time_end': []}
        for n, fn in enumerate(file_list):
            # get first/second/last time from each file,
            nc = NetCDFhandler(fn, 'r')
            time = self.read_time_sec_since_1970(nc)
            nc.close()
            fi['time_start'].append(time[0])
            fi['time_end'].append(time[-1]) # -1 guards against there being only one time step in the file
            fi['n_time_steps'].append(time.shape[0])
            if n + 1 >= self.params['max_numb_files_to_load']: break

        # check some files found
        if len(fi['names']) == 0:
            msg_logger.msg('reader: cannot find any files matching mask "' + self.params['file_mask']
                           + '"  in input_dir : "' + self.params['input_dir'] + '"', fatal_error=True)

        # convert file info to numpy arrays for sorting
        keys = ['names', 'n_time_steps', 'time_start', 'time_end']
        for key in keys:
            fi[key] = np.asarray(fi[key])

        # sort files into order based on start time
        s = np.argsort(fi['time_start'])
        for key in fi.keys():
            if isinstance(fi[key],np.ndarray):
                fi[key] = fi[key][s]

        # tidy up file info
        fi['names'] =    fi['names'].tolist()

        # get time step index at start and end on files
        cs = np.cumsum(fi['n_time_steps'])
        fi['nt_starts'] = cs - fi['n_time_steps']
        fi['n_time_steps_in_hindcast'] = np.sum(fi['n_time_steps'], axis=0)
        fi['nt_ends'] = fi['nt_starts'] + fi['n_time_steps'] - 1

        self.info['file_info'] = fi

        return fi


    def get_hindcast_files_info(self, file_list, msg_logger):
        # read through files to get start and finish times of each file
        # create a time sorted list of files given by file mask in file_info dictionary
        # note this is only called once by OceantrackRunner to form file info list,
        # which is then passed to  OceanTrackerCaseRunner

        # build a dummy non-initialise reader to get some methods and full params
        # add defaults from template, ie get reader class_name default, no warnings, but get these below
        # check cals name
        fi = self.sort_files_by_time(file_list, msg_logger)


        t =  np.concatenate((fi['time_start'],   fi['time_end']))
        fi['first_time'] = np.min(t)
        fi['last_time'] = np.max(t)
        fi['duration'] = fi['last_time'] - fi['first_time']
        fi['hydro_model_time_step'] = fi['duration'] / fi['n_time_steps_in_hindcast']

        # datetime versions for reference
        fi['date_start'] = time_util.seconds_to_datetime64(fi['time_start'])
        fi['date_end'] = time_util.seconds_to_datetime64(fi['time_end'])
        fi['first_date'] = time_util.seconds_to_datetime64(fi['first_time'])
        fi['last_date'] = time_util.seconds_to_datetime64(fi['last_time'])
        fi['hydro_model_timedelta'] = time_util.seconds_to_pretty_duration_string(fi['hydro_model_time_step'] )

        # checks on hindcast
        if fi['n_time_steps_in_hindcast'] < 2:
            msg_logger.msg('Hindcast must have at least two time steps, found ' + str(fi['n_time_steps_in_hindcast']), fatal_error=True)

        # check for large time gaps between files
        # check if time diff between starts of file and end of last are larger than average time step
        if len(fi['time_start']) > 1:
            dt_gaps = fi['time_start'][1:] - fi['time_end'][:-1]
            sel = np.abs(dt_gaps) > 2.5* fi['hydro_model_time_step']
            if np.any(sel):
                msg_logger.msg('Some time gaps between hydro-model files is are > 2.5 times average time step, check hindcast files are all present??', hint='check hindcast files are all present and times in files consistent', warning=True)
                for n in np.flatnonzero(sel):
                    msg_logger.msg(' large time gaps between file ' + fi['names'][n] + ' and ' + fi['names'][n + 1], tabs=1)

        msg_logger.exit_if_prior_errors('exiting from _get_hindcast_files_info, in setting up readers')
        return fi





    def is_3D_variable(self,nc, var_name):
        # is variable 3D
        return  nc.is_var_dim(var_name,self.params['dimension_map']['z'])


    def build_hori_grid(self, nc, grid):
        # read nodal values and triangles
        params = self.params
        ml = self.shared_info.msg_logger
        grid_map= params['grid_variable_map']

        for v in grid_map['x'] + [grid_map['triangles'], grid_map['time']]:
            if not nc.is_var(v):
                ml.msg(f'Cannot find variable "{v}" in file "{nc.file_name}" ', crumbs='in grid set', fatal_error=True)
                return
        grid =  {}

        # read nodal x's

        grid = self.read_grid_coords(nc, grid)
        grid['x'] = grid['x'].astype(np.float64)

        grid = self.read_triangles_as_int32(nc, grid)
        # ensure np.int32 values
        grid['triangles']=grid['triangles'].astype(np.int32)
        grid['quad_cells_to_split'] = grid['quad_cells_to_split'].astype(np.int32)

        return grid

    def field_var_info(self,nc,file_var_map):
        si = self.shared_info
        params = self.params
        dim_map= params['dimension_map']
        grid = self.grid
        info = self.info
        ml = si.msg_logger

        # get dim sized from  vectors and scalers
        if type(file_var_map) != list : file_var_map = [file_var_map]
        var_list = [v for v in file_var_map if v != None]

        is_vector = len(var_list) > 1
        for v in var_list:
            if not nc.is_var(v):
                ml.msg(f'Cannot find variable "{v}" in file "{nc.file_name}" ', crumbs='in reader set up fields', fatal_error=True)
                continue
            if dim_map['vector2D'] in nc.all_var_dims(v) or dim_map['vector3D'] in nc.all_var_dims(v):
                is_vector = True

        out = dict(time_varying=dim_map['time'] in nc.all_var_dims(var_list[0]),
                 is3D= self.is_3D_variable(nc, var_list[0]),
                 is_vector= is_vector)

        return out



    # Below are basic variable read methods for any new reader
    #---------------------------------------------------------
    def is_hindcast3D(self, nc):
       # look for 3D vel variabel, if not use 2D version

        si = self.shared_info
        params = self.params
        vm = params['field_variable_map']

        if nc.is_var_dim(params['field_variable_map']['water_velocity'][0], params['dimension_map']['z']):
            is3D_hydro = True
        else:
            is3D_hydro = False
            params['field_variable_map']['water_velocity'] = params['field_variable_map']['water_velocity'][:2] # remove vertical velocity if given

        return is3D_hydro


    def read_time_sec_since_1970(self, nc, file_index=None):
        vname = self.params['grid_variable_map']['time']
        if file_index is None: file_index = np.arange(nc.var_shape(vname)[0])

        time = nc.read_a_variable(vname, sel=file_index)

        if self.params['isodate_of_hindcast_time_zero'] is not None:
            time += time_util.isostr_to_seconds(self.params['isodate_of_hindcast_time_zero'])
        return time

    def read_grid_coords(self, nc, grid):
        params= self.params
        var_name = params['grid_variable_map']['x']
        grid['x'] = np.column_stack((nc.read_a_variable(var_name[0]), nc.read_a_variable(var_name[1]))).astype(np.float64)

        if self.params['cords_in_lat_long']:
            grid['x'] = self.convert_lon_lat_to_meters_grid(grid['x'])

        return grid

    def read_triangles_as_int32(self, nc, grid):
        # return triangulation
        # if triangualur has /quad cells
        params = self.params
        var_name = params['grid_variable_map']['triangles']
        grid['triangles'] = nc.read_a_variable(var_name).astype(np.int32)

        if params['one_based_indices']:  grid['triangles'] -= 1

        # note indices of any triangles neeeding splitting
        grid['quad_cells_to_split'] =  np.full((0,),0, np.int32)

        if self.detect_lonlat_grid(grid['x']):
            # try auto detection
            grid['is_lon_lat'] = True
        else:
            grid['is_lon_lat'] = self.params['cords_in_lat_long']

        return grid







    def set_up_uniform_sigma(self, nc, grid):
        # read z fractions into grid , for later use in vertical regridding, and set up the uniform sigma to be used
        si = self.shared_info
        # read first zlevel time step
        zlevel = nc.read_a_variable(self.params['grid_variable_map']['zlevel'], sel=0)
        bottom_cell_index = self.read_bottom_cell_index_as_int32(nc).astype(np.int32)
        # use node with thinest top/bot layers as template for all sigma levels

        node_min, grid['zlevel_fractions'] = hydromodel_grid_transforms.find_node_with_smallest_bot_layer(zlevel, bottom_cell_index, si.z0)

        # use layer fractions from this node to give layer fractions everywhere
        # in LSC grid this requires stretching a bit to give same number max numb. of depth cells
        nz_bottom = bottom_cell_index[node_min]

        # stretch sigma out to same number of depth cells,
        # needed for LSC grid if node_min profile is not full number of cells
        zf_model = grid['zlevel_fractions'][node_min, nz_bottom:]
        nz = grid['zlevel_fractions'].shape[1]
        nz_fractions = nz - nz_bottom
        grid['sigma'] = np.interp(np.arange(nz) / nz, np.arange(nz_fractions) / nz_fractions, zf_model)

        return grid


    def assemble_field_components(self,nc, grid, name, field, file_index=None):
        # read scalar fields / join together the components which make vector from component list
        params = self.params

        s= list(field.data.shape)
        s[0] = 1 if file_index is None else file_index.size
        out  = np.zeros(s,dtype=np.float32) #todo faster make a generic  buffer at start

        m= 0 # num of vector components read so far

        var_names = params['field_variable_map'][name] if type(params['field_variable_map'][name]) ==list  else [params['field_variable_map'][name]]

        for var_name in var_names:
            if var_name is None: continue
            data = self.read_file_var_as_4D_nodal_values(nc, grid, var_name, file_index)
            comp_per_var = data.shape[3]
            m1 = m + comp_per_var
            # get view of where in buffer data is to be placed
            out[:, :, :, m:m1] = data
            m += comp_per_var
        return out

    def read_file_var_as_4D_nodal_values(self,nc, grid, var_name, file_index=None):
        # read variable into 4D ( time, node, depth, comp) format
        # assumes same variable order in the file
        dm = self.params['dimension_map']
        data = nc.read_a_variable(var_name, sel=file_index)
        # get 4d size
        s= [0,0,0,0]
        s[0] = data.shape[0] if nc.is_var_dim(var_name,dm['time']) else 1
        s[1] = nc.dim_size(self.params['dimension_map']['node'])

        # see if z or z water level  in variable
        if  nc.is_var_dim(var_name,dm['z']) :
            s[2] = nc.dim_size(self.params['dimension_map']['z'])

        elif nc.is_var_dim(var_name, dm['z_water_velocity']):
            s[2] = nc.dim_size(self.params['dimension_map']['z_water_velocity'])
        else:
            s[2] = 1

        if nc.is_var_dim(var_name, dm['vector2D']):
            s[3] = 2
        elif  nc.is_var_dim(var_name, dm['vector3D']):
            s[3] = 3
        else:
            s[3] = 1

        return data.reshape(s)


    def read_dry_cell_data(self,nc,grid, fields, file_index,is_dry_cell_buffer, buffer_index):
        # calculate dry cell flags, if any cell node is dry
        si = self.shared_info

        if self.params['grid_variable_map']['is_dry_cell'] is None:
            if grid['zlevel'] is None:
                reader_util.set_dry_cell_flag_from_tide( grid['triangles'],
                                                        fields['tide'].data, fields['water_depth'].data,
                                                        si.minimum_total_water_depth, is_dry_cell_buffer,buffer_index)
            else:
                reader_util.set_dry_cell_flag_from_zlevel( grid['triangles'],
                                                          grid['zlevel'], grid['bottom_cell_index'],
                                                          si.minimum_total_water_depth, is_dry_cell_buffer,buffer_index)
        else:
            # get dry cells for each triangle allowing for splitting quad cells
            data_added_to_buffer = nc.read_a_variable(self.params['grid_variable_map']['is_dry_cell'], file_index)
            is_dry_cell_buffer[buffer_index, :] = append_split_cell_data(grid, data_added_to_buffer, axis=1)



    def read_zlevel_as_float32(self, nc,grid,fields, file_index, zlevel_buffer, buffer_index):
        # read in place
        zlevel_buffer[buffer_index,...] = nc.read_a_variable('zcor', sel=file_index).astype(np.float32)


    # convert, time etc to hindcast/ buffer index
    def time_to_hydro_model_index(self, time_sec):
        #convert date time to global time step in hindcast just before/after when forward/backtracking
        # always move forward through buffer, but file info is always forward in time
        si = self.shared_info
        fi = self.info['file_info']

        hindcast_fraction= (time_sec - fi['first_time']) / (fi['last_time'] - fi['first_time'])
        nt = (fi['n_time_steps_in_hindcast'] - 1) *  hindcast_fraction

        # if back tracking round up as moving backwards through buffer, forward round down
        return np.int32(np.floor(nt*si.model_direction)*si.model_direction)

    def hydro_model_index_to_buffer_offset(self, nt_hindcast):
        # ring buffer mapping
        return nt_hindcast % self.info['buffer_info']['buffer_size']

    def are_time_steps_in_buffer(self, time_sec):
        # check if next two steps of remaining  hindcast time steps required to run  are in the buffer
        si = self.shared_info
        bi = self.info['buffer_info']
        model_dir = si.model_direction

        # get hindcast time step at current time
        nt_hindcast = self.time_to_hydro_model_index(time_sec)

        return  nt_hindcast in bi['time_steps_in_buffer'] and nt_hindcast + model_dir in bi['time_steps_in_buffer']


    def convert_lon_lat_to_meters_grid(self, x):

        if self.params['CRS_transform_code'] is None:
            x_out = cord_transforms.WGS84_to_UTM( x, out=None)
        else:
            #todo make it work with users transform?
            x_out = cord_transforms.WGS84_to_UTM(x, out=None)
        return x_out


    def close(self):
       pass