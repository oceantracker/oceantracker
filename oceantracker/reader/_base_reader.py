import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util, json_util
from os import path, walk
from datetime import datetime

from oceantracker.util.ncdf_util import NetCDFhandler
from time import perf_counter
from oceantracker.util.basic_util import nopass
from oceantracker.reader.util.reader_util import append_split_cell_data
from oceantracker.util import  cord_transforms
from oceantracker.reader.util import shared_reader_memory_util
from oceantracker.util.profiling_util import function_profiler
from oceantracker.util import triangle_utilities_code
from oceantracker.util.triangle_utilities_code import split_quad_cells

from oceantracker.reader.util import reader_util

class _BaseReader(ParameterBaseClass):

    def __init__(self, shared_memory_info=None):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({
            'input_dir': PVC(None, str, is_required=True),
            'file_mask': PVC(None, str, is_required=True, doc_str='Mask for file names, eg "scout*.nc", finds all files matching in  "input_dir" and its sub dirs that match the file_mask pattern'),
            'time_zone': PVC(None, int, min=-12, max=12, units='hours', doc_str='time zone in hours relative to UTC/GMT , eg NZ standard time is time zone 12'),
            'cords_in_lat_long': PVC(False, bool, doc_str='Convert given nodal lat longs to a UTM metres grid'),
            'time_buffer_size': PVC(24, int, min=2),
            'grid_variable_map': {'time': PVC('time', str, is_required=True),
                               'x': PLC(['x', 'y'], [str], fixed_len=2),
                               'zlevel': PVC(None, str),
                               'triangles': PVC(None, str),
                               'bottom_cell_index': PVC(None, str),
                               'is_dry_cell': PVC(None, np.int8, doc_str='Time variable flag of when cell is dry, 1= is dry cell')},

            'field_variables': PLC(['water_velocity', 'tide','water_depth'], [str], doc_str='names of variables to read and interplate to give particle values. If name in field_variable_map, then the mapped file variables will be used. If not the given name must be a file variable name.',
                                   make_list_unique=True),
            'field_variable_map': {'water_velocity': PLC(['u', 'v', None], [str, None], fixed_len=3, is_required=True),
                                'tide': PVC('elev', str),
                                'water_depth': PVC('depth', str, is_required=True),
                                'water_temperature': PVC('temp', str),
                                'salinity': PVC(None, str),
                                'wind_stress': PVC(None, str),
                                'bottom_stress': PVC(None, str),
                                },
            'dimension_map': {'time': PVC('time', str, is_required=True),
                              'node': PVC('node', str),
                              'z': PVC(None, str),
                              'vector2Ddim': PVC(None, str),
                              'vector3Ddim': PVC(None, str)},

            'one_based_indices' :  PVC(False, bool,doc_str='indices in hindcast start at 1, not zero, eg. triangulation nodes start at 1 not zero as in python'),
            'isodate_of_hindcast_time_zero': PVC('1970-01-01', 'iso8601date'),
            'max_numb_files_to_load': PVC(10 ** 7, int, min=1, doc_str='Only read no more than this number of hindcast files, useful when setting up to speed run')
             })  # list of normal required dimensions

        self.info['field_variable_info'] = {}
        self.info['buffer_info'] ={}

    def initial_setup(self):
        # map variable internal names to names in NETCDF file
        # set update default value and vector variables map  based on given list
        si = self.shared_info
        ml= si.msg_logger
        info = self.info
        self.info['file_info'] = si.working_params['file_info']  # add file_info to reader info
        nc = NetCDFhandler(info['file_info']['names'][0])
        info['is3D']=self.is_hindcast3D(nc)
        info['nz_levels'] = nc.dim_size(self.params['dimension_map']['z']) if info['is3D']  else None

        grid = self.read_grid(nc)
        self.grid= self.build_grid(grid)
        self.setup_fields(nc)
        nc.close()

        ml.exit_if_prior_errors()

        #set up ring buffer  info
        bi = self.info['buffer_info']
        bi['n_filled'] = 0
        bi['buffer_size'] = self.params['time_buffer_size']
        bi['time_steps_in_buffer'] = []
        bi['buffer_available'] = bi['buffer_size']
        bi['nt_buffer0'] = 0

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

        # checks on hindcast using first hindcast file
        nc = NetCDFhandler(fi['names'][0], 'r')
        nc.close()

        t =  np.concatenate((fi['time_start'],   fi['time_end']))
        fi['first_time'] = np.min(t)
        fi['last_time'] = np.max(t)
        fi['duration'] = fi['last_time'] - fi['first_time']
        fi['hydro_model_time_step'] = fi['duration'] / (fi['n_time_steps_in_hindcast'] - 1)

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
            sel = np.abs(dt_gaps) > 2* fi['hydro_model_time_step']
            if np.any(sel):
                msg_logger.msg('Some time gaps between hindcast files is are > 1.8 times average time step, check hindcast files are all present??', hint='check hindcast files are all present and times in files consistent', warning=True)
                for n in np.flatnonzero(sel):
                    msg_logger.msg(' large time gaps bwteen flies > 2 time steps) for  files in squence ' + fi['names'][n] + ' and ' + fi['names'][n + 1], tabs=1)

        msg_logger.exit_if_prior_errors('exiting from _get_hindcast_files_info, in setting up readers')
        return fi

    def read_grid(self, nc):
        # read nodal values and triangles
        params = self.params
        ml = self.shared_info.msg_logger
        grid_map= params['grid_variable_map']

        # todo check variables exist


        for v in grid_map['x'] + [grid_map['triangles'], grid_map['time']]:
            if not nc.is_var(v):
                ml.msg(f'Cannot find variable "{v}" in file "{nc.file_name}" ', crumbs='in grid set', fatal_error=True)
                return
        grid =  {}
        grid['triangles'] = self.read_triangles(nc).astype(np.int32)
        grid['triangles'], grid['triangles_to_split'] = self.find_quad_cells_split_to_split(grid['triangles'])
        grid['x'] = self.read_nodal_x(nc).astype(np.float64)
        if self.info['is3D']:
            grid['bottom_cell_index'] = self.read_bottom_cell_index(nc).astype(np.int32)
        return grid

    def build_grid(self, grid):
        # set up grid variables which don't vary in time and are shared by all case runners and main
        # add to reader build info
        si = self.shared_info
        info = self.info
        msg_logger = self.msg_logger
        msg_logger.progress_marker('Starting grid setup')

        # node to cell map
        t0 = perf_counter()
        grid['node_to_tri_map'], grid['tri_per_node'] = triangle_utilities_code.build_node_to_cell_map(grid['triangles'], grid['x'])
        msg_logger.progress_marker('built node to triangles map', start_time=t0)

        # adjacency map
        t0 = perf_counter()
        grid['adjacency'] = triangle_utilities_code.build_adjacency_from_node_cell_map(grid['node_to_tri_map'], grid['tri_per_node'], grid['triangles'])
        msg_logger.progress_marker('built triangle adjacency matrix', start_time=t0)

        # boundary triangles
        t0 = perf_counter()
        grid['is_boundary_triangle'] = triangle_utilities_code.get_boundary_triangles(grid['adjacency'])
        msg_logger.progress_marker('found boundary triangles', start_time=t0)
        t0 = perf_counter()
        grid['grid_outline'] = triangle_utilities_code.build_grid_outlines(grid['triangles'], grid['adjacency'],
                                                                           grid['is_boundary_triangle'], grid['node_to_tri_map'], grid['x'])

        msg_logger.progress_marker('built domain and island outlines', start_time=t0)

        # make island and domain nodes
        grid['node_type'] = np.zeros(grid['x'].shape[0], dtype=np.int8)
        for c in grid['grid_outline']['islands']:
            grid['node_type'][c['nodes']] = 1

        grid['node_type'][grid['grid_outline']['domain']['nodes']] = 2

        t0 = perf_counter()
        grid['triangle_area'] = triangle_utilities_code.calcuate_triangle_areas(grid['x'], grid['triangles'])
        msg_logger.progress_marker('calculated triangle areas', start_time=t0)
        msg_logger.progress_marker('Finished grid setup')

        # adjust node type and adjacent for open boundaries
        # todo define node and adjacent type values in dict, for single definition and case info output?
        is_open_boundary_node = self.read_open_boundary_data_as_boolean(grid)
        grid['node_type'][is_open_boundary_node] = 3

        is_open_boundary_adjacent = reader_util.find_open_boundary_faces(grid['triangles'], grid['is_boundary_triangle'], grid['adjacency'], is_open_boundary_node)
        grid['adjacency'][is_open_boundary_adjacent] = -2
        grid['limits'] = np.asarray([np.min(grid['x'][:, 0]), np.max(grid['x'][:, 0]), np.min(grid['x'][:, 1]), np.max(grid['x'][:, 1])])

        # now set up time buffers
        time_buffer_size = self.params['time_buffer_size']
        grid['time'] = np.zeros((time_buffer_size,), dtype=np.float64)
        grid['date'] = np.zeros((time_buffer_size,), dtype='datetime64[s]')  # time buffer
        grid['nt_hindcast'] = np.full((time_buffer_size,), -10, dtype=np.int32)  # what global hindcast timestesps are in the buffer

        # set up zlevel
        if self.info['is3D']:
            s = [self.params['time_buffer_size'], grid['x'].shape[0], info['nz_levels']]
            grid['zlevel'] = np.zeros(s, dtype=np.float32, order='c')
            info['nz_levels'] = grid['zlevel'].shape[2]

            # todo dev zlevel by triangles
            s = [self.params['time_buffer_size'], grid['triangles'].shape[0], info['nz_levels'], 3]
            grid['zlevel_vertex'] = np.zeros(s, dtype=np.float32, order='c')

        else:
            grid['zlevel'] = None
            grid['nz'] = 1  # note if 3D

            # space for dry cell info
        grid['is_dry_cell'] = np.full((self.params['time_buffer_size'], grid['triangles'].shape[0]), 1, np.int8)

        # reader working space for 0-255 index of how dry each cell is currently, used in stranding, dry cell blocking, and plots
        grid['dry_cell_index'] = np.full((grid['triangles'].shape[0],), 0, np.uint8)

        # note which are time buffers

        return grid

    def find_quad_cells_split_to_split(self, triangles):
        # flag quad cells for splitting if index in 4th column
        if triangles.shape[1] == 4 and np.any(triangles > 0):
            # split quad grids buy making new triangles
            quad_cells_to_split = triangles[:, 3] > 0
            triangles = split_quad_cells(triangles, quad_cells_to_split)
        else:
            quad_cells_to_split = np.full((triangles.shape[0],), False, dtype=bool)

        return triangles, quad_cells_to_split

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

        # get require dim of field
        s=np.asarray([1,grid['x'].shape[0], 1,0],dtype=np.int32)
        component_list = []
        for v in var_list:
            if not  nc.is_var(v):
                ml.msg(f'Cannot find variable "{v}" in file "{nc.file_name}" ', crumbs='in reader set up fields',fatal_error=True)
                continue
            if dim_map['time'] in nc.all_var_dims(v): s[0] = params['time_buffer_size']
            if dim_map['z'] in nc.all_var_dims(v): s[2] = info['nz_levels']
            if dim_map['vector2Ddim'] in nc.all_var_dims(v):
                s[3] +=2
                comp_per_var =2
            elif dim_map['vector3Ddim'] in nc.all_var_dims(v):
                s[3] += 3
                comp_per_var= 3
            else:
                s[3] += 1
                comp_per_var =1
            component_list.append(dict(file_name=v,comp_per_var=comp_per_var))

        p= dict(is_time_varying = s[0] > 0, is3D = s[2] > 0, num_components= s[3])

        return dict(component_list=component_list,   params=p,comp_per_var=comp_per_var,shape_in_memory=s.tolist())

    def setup_fields(self, nc):

        si= self.shared_info
        vi = self.info['field_variable_info']

        info=self.info
        params = self.params
        field_params = dict(class_name='oceantracker.fields._base_field.ReaderField')
        for name in params['field_variables']:
            if name in params['field_variable_map']:
                file_var_map = params['field_variable_map'][name]
            else:
                file_var_map = name # assume given field variable is in the file
            vi[name] =self.field_var_info(nc,file_var_map )
            # setup field
            field_params['shape_in_memory']= vi[name]['shape_in_memory']
            si.create_class_dict_instance(name,'fields','from_reader_field',field_params, crumbs=f'Fields Setup > "{name}"',initialise=True)

        # read time independent vector and scalar reader fields
        for name, field in si.classes['fields'].items():
            if not field.is_time_varying() and field.info['group'] == 'from_reader_field':
                data = self.assemble_field_components(nc, vi[name])
                data = self.convert_field_grid(nc, name, data)  # do any customised tweaks
                field.data[0, ...] = data

    # Below are basic variable read methods for any new reader
    #---------------------------------------------------------
    def is_hindcast3D(self, nc): return nc.is_var(self.params['grid_variable_map']['zlevel'])

    def read_time_sec_since_1970(self, nc, file_index=None):
        vname = self.params['grid_variable_map']['time']
        if file_index is None: file_index = np.arange(nc.var_shape(vname)[0])

        time = nc.read_a_variable(vname, sel=file_index)

        if self.params['isodate_of_hindcast_time_zero'] is not None:
            time += time_util.isostr_to_seconds(self.params['isodate_of_hindcast_time_zero'])
        return time

    def read_nodal_x(self, nc):
        params= self.params
        var_name = params['grid_variable_map']['x']
        x = np.stack((nc.read_a_variable(var_name[0]), nc.read_a_variable(var_name[1])), axis=1)
        if self.params['cords_in_lat_long']:
            x = self.convert_lon_lat_to_meters_grid(x)
        return x

    def read_triangles(self, nc):
        # return triangulation
        # if triangualur has /quad cells
        params = self.params
        var_name = params['grid_variable_map']['triangles']
        triangles = nc.read_a_variable(var_name).astype(np.int32)

        if params['one_based_indices']: triangles -= 1
        return triangles


    # checks on first hindcast file
    def additional_setup_and_hindcast_file_checks(self, nc,msg_logger): pass


   # working methods
    def convert_field_grid(self, nc, name, data): return data # allows tweaks to grid of named fields, eg if name=='depth:

    #@function_profiler(__name__)
    def fill_time_buffer(self, time_sec):
        # fill as much of  hindcast buffer as possible starting at global hindcast time step nt0_buffer
        # fill buffer starting at hindcast time step nt0_buffer
        # todo change so does not read current step again after first fill of buffer

        si = self.shared_info
        t0 = perf_counter()

        grid = self.grid
        info= self.info
        fi = info['file_info']
        bi = info['buffer_info']
        vi = info['field_variable_info']
        buffer_size = bi['buffer_size']


        nt0_hindcast = self.time_to_hydro_model_index(time_sec)
        bi['nt_buffer0'] = nt0_hindcast  # nw start of buffer

        # get hindcast global time indices of first block, loads in model order
        # ie if backtracking are still moving forward in buffer
        total_read = 0
        bi['buffer_available'] = buffer_size

        # find first file with time step in it, if backwars files are in reverse time order
        n_file = np.argmax(np.logical_and( nt0_hindcast   >=  fi['nt_starts']* si.model_direction, nt0_hindcast  <= fi['nt_ends']))

        # get required time step and trim to size of hindcast
        nt_hindcast_required = nt0_hindcast + si.model_direction * np.arange(min(fi['n_time_steps_in_hindcast'],buffer_size))
        sel = np.logical_and( 0 <= nt_hindcast_required,  nt_hindcast_required < fi['n_time_steps_in_hindcast'])
        nt_hindcast_required = nt_hindcast_required[sel]

        bi['time_steps_in_buffer'] = []

        while len(nt_hindcast_required) > 0 and 0 <= n_file < len(fi['names']):

            nc = NetCDFhandler(fi['names'][n_file], 'r')

            # find time steps in current file,accounting for direction
            sel =  np.logical_and( nt_hindcast_required >= fi['nt_starts'][n_file],
                                   nt_hindcast_required <= fi['nt_ends'  ][n_file])
            num_read = np.count_nonzero(sel)
            nt_file = nt_hindcast_required[sel]  # hindcast steps in this file

            file_index = nt_file - fi['nt_starts'][n_file]
            buffer_index = self.hydro_model_index_to_buffer_offset(nt_file)
            s =  f'Reading-file-{(n_file):02d}  {path.basename(fi["names"][n_file])}, steps in file {fi["n_time_steps"][n_file]:3d},'
            s += f' steps  available {fi["nt_starts"][n_file]:03d}:{fi["nt_starts"][n_file]+fi["n_time_steps"][n_file]-1:03d}, '
            s += f'reading  {num_read:2d} of {bi["buffer_available"]:2d} steps, '
            s += f' for hydo-model time steps {nt_file[0]:02d}:{nt_file[-1]:02d}, '
            s += f' from file offsets {file_index[0]:02d}:{file_index[-1]:02d}, '
            s += f' into ring buffer offsets {buffer_index[0]:03}:{buffer_index[-1]:03d} '
            si.msg_logger.progress_marker(s)

            grid['nt_hindcast'][buffer_index] = nt_hindcast_required[:num_read]  # add a grid variable with global hindcast time steps

            # read time varying vector and scalar reader fields
            for name, field in si.classes['fields'].items():
                if field.is_time_varying() and field.info['group'] == 'from_reader_field':
                    data  = self.assemble_field_components(nc, vi[name], file_index=file_index)
                    data = self.convert_field_grid(nc, name, data) # do any customised tweaks
                    field.data[buffer_index, ...] = data

            # read grid time, zlevel
            # do this after reading fields as some hindcasts required tide field to get zlevel, eg FVCOM
            self.read_time_variable_grid_variables(nc, buffer_index,file_index)

            nc.close()

            # now all  data has been read from file, now
            # update user fields from newly read fields and data
            for name, i in si.classes['fields'].items():
                if i.is_time_varying() and i.info['group'] in ['derived_from_reader_field','user']:
                    i.update(buffer_index)

            total_read += num_read

            # set up for next step

            bi['buffer_available'] -= num_read
            n_file += si.model_direction
            nt_hindcast_required = nt_hindcast_required[num_read:]
            bi['time_steps_in_buffer'] += nt_file.tolist()

        si.msg_logger.progress_marker(f' read {total_read:3d} time steps in  {perf_counter() - t0:3.1f} sec', tabs=2)
        # record useful info/diagnostics
        bi['n_filled'] = total_read

    def assemble_field_components(self,nc, var_info, file_index=None):
        # read scalar fields / join together the components which make vector from component list

        grid = self.grid
        s= var_info['shape_in_memory'].copy()
        s[0] = 1 if file_index is None else file_index.size
        out  = np.zeros(s,dtype=np.float32) #todo faster make a generic  buffer at start
        m= 0 # num of vector components read so far
        for component_info in var_info['component_list']:
            data = nc.read_a_variable(component_info['file_name'], sel= file_index).astype(np.float32)
            s[3] = component_info['comp_per_var']
            data= data.reshape(s)
            m1 = m + component_info['comp_per_var']
            # get view of where in buffer data is to be placed
            out[:, :, :, m:m1] = data
            m += component_info['comp_per_var']
        return out

    def read_time_variable_grid_variables(self, nc, buffer_index, file_index):
        # read time and  grid variables, eg time, tide, zlevel
        si = self.shared_info
        grid = self.grid

        grid['time'][buffer_index] = self.read_time_sec_since_1970(nc, file_index=file_index)

        # do time zone adjustment
        if self.params['time_zone'] is not None:
            grid['time'][buffer_index] += self.params['time_zone'] * 3600.

        # add date for convenience
        grid['date'][buffer_index] = time_util.seconds_to_datetime64(grid['time'][buffer_index])

        if si.is3D_run:
            # grid['total_water_depth'][buffer_index,:]= np.squeeze(si.classes['fields']['tide'].data[buffer_index,:] + si.classes['fields']['water_depth'].data)
            # read zlevel inplace to save memory?
            self.read_zlevel_as_float32(nc, file_index, grid['zlevel'], buffer_index)

            # unpack zlevel's at each triangle's vertex
            reader_util.zlevel_node_to_vertex(grid['zlevel'], grid['triangles'], grid['zlevel_vertex'])

        self.read_dry_cell_data(nc, file_index, grid['is_dry_cell'], buffer_index)

    def read_dry_cell_data(self,nc,file_index,is_dry_cell_buffer, buffer_index):
        # calculate dry cell flags, if any cell node is dry
        grid = self.grid
        si = self.shared_info
        fields = si.classes['fields']

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

    def read_zlevel_as_float32(self, nc, file_index, zlevel_buffer, buffer_index):
        # read in place
        zlevel_buffer[buffer_index,...] = nc.read_a_variable('zcor', sel=file_index).astype(np.float32)

    def read_open_boundary_data_as_boolean(self, grid):
        is_open_boundary_node = np.full((grid['x'].shape[0],), False)
        return is_open_boundary_node

    # convert, time etc to hindcast/ buffer index
    def time_to_hydro_model_index(self, time_sec):
        #convert date time to global time step in hindcast just before/after when forward/backtracking
        # always move forward through buffer, but file info is always forward in time
        si = self.shared_info
        fi = self.info['file_info']
        model_dir = si.model_direction


        hindcast_fraction= (time_sec - fi['first_time']) / (fi['last_time'] - fi['first_time'])
        nt = (fi['n_time_steps_in_hindcast'] - 1) *  hindcast_fraction

        # if back tracking ronud up as moving backwards through buffer, forward round down
        return np.int32(np.floor(nt*model_dir)*model_dir)

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

    def _open_first_file(self,file_info):
        file_name= file_info['names'][0]
        nc =NetCDFhandler(file_name, 'r')
        return nc

    def convert_lon_lat_to_meters_grid(self, x):

        if self.params['EPSG_transform_code'] is None:
            x_out, self.cord_transformer= cord_transforms.WGS84_to_UTM( x, out=None)
        else:
            #todo make it work with users transform?
            x_out = cord_transforms.WGS84_to_UTM(x, out=None)
        return x_out

    def write_hydro_model_grid(self):
        # write a netcdf of the grid from first hindcast file
        si =self.shared_info
        output_files = si.output_files
        grid = self.grid

        # write grid file
        output_files['grid'] = output_files['output_file_base'] + '_grid.nc'
        nc = NetCDFhandler(path.join(output_files['run_output_dir'], output_files['grid'] ), 'w')
        nc.write_global_attribute('index_note', ' all indices are zero based')
        nc.write_global_attribute('created', str(datetime.now().isoformat()))

        nc.write_a_new_variable('x', grid['x'], ('node_dim', 'vector2D'))
        nc.write_a_new_variable('triangles', grid['triangles'], ('triangle_dim', 'vertex'))
        nc.write_a_new_variable('triangle_area', grid['triangle_area'], ('triangle_dim',))
        nc.write_a_new_variable('adjacency', grid['adjacency'], ('triangle_dim', 'vertex'))
        nc.write_a_new_variable('node_type', grid['node_type'], ('node_dim',), attributes={'node_types': ' 0 = interior, 1 = island, 2=domain, 3=open boundary'})
        nc.write_a_new_variable('is_boundary_triangle', grid['is_boundary_triangle'], ('triangle_dim',))
        nc.write_a_new_variable('water_depth', si.classes['fields']['water_depth'].data.squeeze(), ('node_dim',))
        nc.close()

        output_files['grid_outline'] = output_files['output_file_base'] + '_grid_outline.json'
        json_util.write_JSON(path.join(output_files['run_output_dir'], output_files['grid_outline']), grid['grid_outline'])


    def close(self):
       pass