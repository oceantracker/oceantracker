import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass, make_class_instance_from_params
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.message_and_error_logging import append_message, GracefulExitError
from oceantracker.util import time_util
from os import path, walk
from glob import glob
from oceantracker.util.ncdf_util import NetCDFhandler
from time import perf_counter
from oceantracker.fields.util import fields_util
from oceantracker.util.basic_util import nopass
from oceantracker.util.triangle_utilities_code import append_split_cell_data
from oceantracker.fields.util.fields_util import depth_aver_SlayerLSC_in4D
from copy import copy ,deepcopy
from oceantracker.util import  shared_memory
from oceantracker.reader.util import reader_util

class _BaseReader(ParameterBaseClass):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({'input_dir': PVC(None, str),
                                 'file_mask': PVC(None, str, is_required=True, doc_str='Mask for file names, eg "scout*.nc", is joined with "input_dir" to give full file names'),
                                 'grid_file': PVC(None, str, doc_str='File name with hydrodynamic grid data, as path relative to input_dir, default is get grid from first hindasct file'),
                                 'share_reader': PVC(False, bool),
                                 'minimum_total_water_depth': PVC(0.25, float, min=0.0,doc_str= 'Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering'),
                                 'time_zone': PVC(None, int, min=-12, max=23),
                                 'cords_in_lat_long': PVC(False, bool),
                                 'time_buffer_size': PVC(48, int, min=2),
                                 'depth_average': PVC(False, bool),  # turns 3D hindcast into a 2D one
                                 'field_variables_to_depth_average': PLC([], [str]),  # list of field_variables that are depth averaged on the fly
                                 'one_based_indices' :  PVC(False, bool,doc_str='indcies in hindcast start at 1, not zero, eg. triangulation nodes start at 1 not zero as in python'),
                                 'grid_variables': {'time': PVC('time', str, is_required=True),
                                                    'x': PLC(['x', 'y'], [str], fixed_len=2),
                                                    'zlevel': PVC(None, str),
                                                    'bottom_cell_index': PVC(None, str),
                                                    'is_dry_cell': PVC(None, np.int8, doc_str='Time variable flag of when cell is dry, 1= is dry cell')},

                                 'field_variables': {'water_velocity': PLC(['u', 'v', None], [str, None], fixed_len=3,is_required=True),
                                                     'water_depth': PVC(None, str),
                                                     'tide': PVC(None, str),
                                                     'water_temperature': PVC(None, str),
                                                     'salinity': PVC(None, str)},

                                 'dimension_map': {'time': PVC('time', str), 'node': PVC('node', str), 'z': PVC(None, str),
                                                   'vector2Ddim': PVC(None, str), 'vector3Ddim': PVC(None, str)},
                                 'isodate_of_hindcast_time_zero': PVC('1970-01-01', 'iso8601date'),
                                 'search_sub_dirs': PVC(False, bool),
                                 'max_numb_files_to_load': PVC(10 ** 7, int, min=1)
                                 })  # list of normal required dimensions
        self.info['buffer_info'] = {'n_filled': None }
        self.grid = {}
        self.grid_time_buffers = {} # for time varying grid variables

        # store instances of shared memory classes for variables shared between processes
        self.shared_memory= {'grid' :{}, 'fields':{},'control':{}}

    #required read methods non time dependent variables
    def read_nodal_x_float32(self, nc): nopass('reader method: read_x is required')
    def read_bottom_cell_index_as_int32(self, nc):nopass('reader method: read_bottom_cell_index_as_int32 is required for 3D hindcasts')

    # required methods time dependent variables, also require a set up method
    def read_zlevel_as_float32(self, nc, file_index, zlevel_buffer, buffer_index): nopass('reader method: read_zlevel_as_float32 is required for 3D hindcasts')

    def _file_checks(self, file_name, msg_list): pass

    def make_non_time_varying_grid(self,nc, grid): nopass('setup_grid required')

    # required variable  structure query methods
    def is_var_in_file_3D(self, nc, var_name_in_file):
        return self.params['dimension_map']['z'] is not None and nc.is_var_dim(var_name_in_file, self.params['dimension_map']['z'])

    def get_num_vector_components_in_file_variable(self,nc,file_var_name):
        dm = self.params['dimension_map']
        if dm[ 'vector2Ddim'] is not None and  nc.is_var_dim(file_var_name, dm['vector2Ddim']):
            n_comp = 2
        elif dm[ 'vector3Ddim'] is not None and  nc.is_var_dim(file_var_name, dm['vector3Ddim']):
            n_comp = 3
        else:
            n_comp = 1
        return  n_comp

    def is_file_variable_time_varying(self,nc, var_name_in_file): return nc.is_var_dim(var_name_in_file, self.params['dimension_map']['time'])

    def get_number_of_z_levels(self,nc): return nc.get_dim_size(self.params['dimension_map']['z'])

    def is_hindcast3D(self, nc):
        zdim=self.params['dimension_map']['z']
        return  zdim is not None and zdim in nc.get_var_dims(self.params['water_velocity'][0])

    # working methods

    def preprocess_field_variable(self, nc,name, data): return data # allows tweaks to named fields, eg if name=='depth:

    def _add_grid_attributes(self, grid): pass

    def initialize(self):
        # map variable internal names to names in NETCDF file
        # set update default value and vector variables map  based on given list
        si = self.shared_info

    def get_list_of_files_and_hindcast_times(self, input_dir):
        # get list of files matching mask
        if self.params['search_sub_dirs']:
            # search hindcast sub dirs
            file_names = []
            for root, dirs, files in walk(input_dir):
                # add matching files in root folder to list
                new_files = glob(path.join(root, self.params['file_mask']))
                if len(new_files) > 0: file_names += new_files
        else:
            file_names = glob(path.normpath(path.join(input_dir, self.params['file_mask'])))

        file_info = {'names': file_names, 'n_time_steps': [], 'time_start': [], 'time_end': [], 'time_step': []}
        for n, fn in enumerate(file_names):
            # get first/second/last time from each file,
            nc = NetCDFhandler(fn, 'r')
            time = self.read_time(nc)
            nc.close()
            file_info['time_start'].append(time[0])
            file_info['time_end'].append(time[-1])
            file_info['time_step'].append(time[1] - time[0])
            file_info['n_time_steps'].append(time.shape[0])
            if n + 1 >= self.params['max_numb_files_to_load']: break

        return file_info

    def make_grid_builder(self, grid,grid_time_buffers,reader_build_info):

        # make share memory builder for the non time varying grid variables
        reader_build_info['grid_constant_arrays_builder'] = {}
        for key, item in grid.items():
            if item is not None and type(item) == np.ndarray:
                sm = shared_memory.SharedMemArray(values=item)
                self.shared_memory['grid'][key] = sm  # retains a reference to keep sm alive in windows, othewise will quickly be deleted
                reader_build_info['grid_constant_arrays_builder'][key] = sm.get_shared_mem_map()

        # now make info to build time buffers, eg time, zlevel
        reader_build_info['grid_time_buffers_builder'] = {}
        for key, item in grid_time_buffers.items():
            if self.params['share_reader']:  # make shared moemory for shared_reader
                sm = shared_memory.SharedMemArray(values=item)
                self.shared_memory['grid'][key] = sm  # retains a reference to keep sm alive in windows, othewise will quickly be deleted
                reader_build_info['grid_time_buffers_builder'][key] = sm.get_shared_mem_map()
            else:
                reader_build_info['grid_time_buffers_builder'][key] = {'shape': item.shape, 'dtype': item.dtype}

        return reader_build_info

    def maker_field_builder(self,nc, reader_build_info):
        # loop over reader field params
        reader_build_info['field_builder'] ={}
        for name, field_variable_comps in self.params['field_variables'].items():
            if field_variable_comps is not None:
                field_params, comp_info = self.get_field_variable_info(nc, name, field_variable_comps)
                reader_build_info['field_builder'][name] = {'field_params': field_params,'variable_info': comp_info}
                pass

        return reader_build_info


    def setup_reader_fields(self, reader_build_info):
        si = self.shared_info
        fm = si.classes['field_group_manager']
        self.code_timer.start('build_hindcast_reader')
        nc = NetCDFhandler(reader_build_info['sorted_file_info']['names'][0], 'r')

        # setup reader fields from their named components in field_variables param ( water depth ad tide done earlier from grid variables)
        for name, item in reader_build_info['field_builder'].items():
            i, msg_list = make_class_instance_from_params(item['field_params'])
            i.info['variable_info']= item['variable_info']
            si.add_class_instance_to_interator_lists('fields', 'from_reader_field', i, crumbs='Adding Reader Field "' + name + '"')
            i.initialize()  # require variable_info to initialise

            if self.params['share_reader']:
                #todo make this part of reader field intialize
                self.shared_memory['fields'][name] = shared_memory.SharedMemArray(values=i.data)

            if not i.params['is_time_varying']:
                # if not time dependent field read in now,
                data = self.assemble_field_components(nc, i)
                data = self.preprocess_field_variable(nc,name, data)
                i.data[:] = data

            # set up depth averaged version if requested
            if name in self.params['field_variables_to_depth_average']:
                # tweak shape to fit depth average of scalar or 3D vector
                p = {'class_name':'oceantracker.fields.reader_field.DepthAveragedReaderField',
                     'name': name + '_depth_average','num_components': min(2, i.params['num_components']),
                     'is_time_varying': i.params['is_time_varying'],
                    'is3D': False}
                i2, msg_list = make_class_instance_from_params(p,msg_list=msg_list)
                si.add_class_instance_to_interator_lists('fields', 'depth_averaged_from_reader_field', i2,
                                                         crumbs='Adding Reader Depth Averaged Field "' + name + '"')
                i2.initialize()
        nc.close()

        # needed for force read at first time step read to make
        self.buffer_info['n_filled'] = 0
        self.buffer_info['nt_buffer0'] = 0

        self.code_timer.stop('build_hindcast_reader')

    def _file_checks(self, file_name, msg_list):
        # check named variables are in first file
        si = self.shared_info
        nc = NetCDFhandler(file_name, 'r')

        # check dim
        for name, d in self.params['dimension_map'].items():
            if d is not None and not nc.is_dim(d):
                append_message(msg_list, 'Cannot find dimension_map dimension "' + name + ' ", file dimension given is "' + d + '"', exception=GracefulExitError)

        # check variables are there
        for vm in ['grid_variables', 'field_variables']:
            for name, d in self.params[vm].items():
                if type(d)== list:
                    for vf in d:
                        if vf is not None and not nc.is_var(vf):
                            append_message(msg_list,' For  "' + vm + '" for param   "' + name + ' ",  cannot find variable in file  "' + vf + '"', exception=GracefulExitError)

                elif d is not None and not nc.is_var(d) :
                    append_message(msg_list,'For "' + vm + '" for param,  "' + name + ' ", cannot find variable in file "' + str(d) + '"', exception=GracefulExitError)
        nc.close()
        return msg_list

    def get_field_variable_info(self, nc, name,var_list):
        # get info from list of component eg ['temp'], ['u','v']
        si= self.shared_info

        if type(var_list) is not list: var_list=[var_list] # if a string make a list of 1
        var_list = [v for v in var_list if v != None]
        var_file_name0=var_list[0]

        is3D_in_file = self.is_var_in_file_3D(nc, var_file_name0)
        is_time_varying = self.is_file_variable_time_varying(nc, var_file_name0)

        var_info= { 'component_list':[],
                    'is3D_in_file': is3D_in_file,
                    'is_time_varying': is_time_varying,
                    'requires_depth_averaging': self.params['depth_average'] and is3D_in_file}

        # work out number of components in list of variables
        n_total_comp=0
        for file_var_name in var_list:
            n_comp =self.get_num_vector_components_in_file_variable(nc,file_var_name)
            n_total_comp += n_comp
            var_info['component_list'].append({'name_in_file':file_var_name, 'num_components': n_comp })

        # if a 3D var and vector then it must have  3D components
        # eg this allows for missing vertical velocity, to have zeros in water_velocity
        if is3D_in_file and n_total_comp> 1: n_total_comp =3

        params = {'name': name,
                  'class_name':'oceantracker.fields.reader_field.ReaderField',
             'is_time_varying':  is_time_varying,
             'num_components' : n_total_comp,
             'is3D' :  False if var_info['requires_depth_averaging'] else is3D_in_file
            }

        return params, var_info
    

    def time_steps_in_buffer(self, nt_hindcast_remaining):
        # check if next two steps of remaining  hindcast time steps required to run  are in the buffer
        nt_hindcast = self.grid_time_buffers['nt_hindcast']
        return np.any(nt_hindcast == nt_hindcast_remaining[0]) and np.any(nt_hindcast == nt_hindcast_remaining[1])

    def fill_time_buffer(self, nt_hindcast_remaining):
        # fil buffer with as much of  nt_hindcast as possible, nt
        si = self.shared_info
        # check if first and second nt's are  in buffer
        info= self.info

        # fill buffer starting at nt_hindcast_remaining[0]
        self.code_timer.start('reading_to_fill_time_buffer')
        si = self.shared_info
        grid = self.grid
        grid_time_buffers = self.grid_time_buffers

        fi = self.reader_build_info['sorted_file_info']

        # get hindcast global time indices of first block
        nt_required = nt_hindcast_remaining[:self.params['time_buffer_size']].copy()

        t0 = perf_counter()
        b0 = 0
        total_read = 0

        while len(nt_required) > 0:
            # find block of time step with same file number as that of first required time step
            n_file = fi['file_number'][nt_required[0]]  # nt_hindcast to file map
            nt_available = nt_required[fi['file_number'][nt_required] == n_file]  # todo smarter/faster way to do this wayglobal time steps to loadtodo,

            # use list with groups of nt to map each file to the nt it holds, ie a file to nt map
            # read from this file
            nc = NetCDFhandler(fi['names'][n_file], 'r')

            num_read = len(nt_available)
            buffer_index = b0 + np.arange(num_read)
            file_index = fi['file_offset'][nt_available]

            s =  f'Reading-file-{(n_file+1):02}' + path.basename(fi['names'][n_file]) + f'{file_index[0]:04}:{file_index[-1]:04}'
            s += f' Steps in file {fi["n_time_steps"][-1]:4} nt available {nt_available[0]:03} :{nt_available[-1]:03},'
            s += f' file offsets {file_index[0]:4} : {file_index[-1]:4}  nt required {nt_required[0]:4}:{nt_required[-1]:4}, number required: {nt_required.shape[0]:4}'

            si.case_log.write_progress_marker(s)

            grid_time_buffers['nt_hindcast'][buffer_index] = nt_available  # add a grid variable with buffer time steps

            # read time varying vector and scalar reader fields
            for name, field in si.class_interators_using_name['fields']['from_reader_field'].items():
                if field.is_time_varying():
                    data_added_to_buffer = self.assemble_field_components(nc, field, buffer_index=buffer_index, file_index=file_index)
                    data_added_to_buffer = self.preprocess_field_variable(nc, name, data_added_to_buffer) # do any customised tweaks

                    field.data[buffer_index, ...] = data_added_to_buffer

                    if name in self.params['field_variables_to_depth_average']:
                       si.classes['fields'][name + '_depth_average'].data[buffer_index, ...] = fields_util.depth_aver_SlayerLSC_in4D(data_added_to_buffer, grid_time_buffers['zlevel'], grid['bottom_cell_index'])

            # read grid time, zlevel
            # do after reading fields as some hindcasts required tide filed to get zlevel, eg FVCOM
            self.read_time_variable_grid_variables(nc, buffer_index,file_index)

            nc.close()

            # now all  data has been read from file, now
            # update user fields from newly read fields and data
            for field_types in ['derived_from_reader_field','user']:
                for field in si.class_interators_using_name['fields'][field_types].values():
                    if field.is_time_varying():
                        field.update(buffer_index)

            total_read += num_read
            s = '    read file at time ' + time_util.seconds_to_pretty_str(grid_time_buffers['time'][buffer_index[0]])
            s += f' file offsets {file_index[0] :04}:{file_index[-1]:04}'
            s += f' buffer offsets {buffer_index[0]:03}:{buffer_index[-1]:03}'
            s += f' Read:{num_read:4}  time: {int(1000. * (perf_counter() - t0)):3} ms'

            si.case_log.write_progress_marker(s)
            b0 += num_read
            n_file += int(si.model_direction)
            nt_required = nt_required[num_read:]

        # record useful info/diagnostics
        buffer_info = info['buffer_info']
        buffer_info['n_filled'] = total_read
        buffer_info['first_nt_hindcast_in_buffer'] = grid_time_buffers['nt_hindcast'][0]  # global index of buffer zero
        buffer_info['last_nt_hindcast_in_buffer']  = grid_time_buffers['nt_hindcast'][total_read-1]

        self.code_timer.stop('reading_to_fill_time_buffer')

    def assemble_field_components(self,nc, field, buffer_index=None, file_index=None):
        # read scalar fields / join together the components which make vector from component list

        grid = self.grid
        grid_time_buffers = self.grid_time_buffers

        m= 0 # num of vector components read so far
        var_info = field.info['variable_info']
        for component_info in var_info['component_list']:
            data = self.read_file_field_variable_as4D(nc, component_info,var_info['is_time_varying'], file_index)

            if var_info['requires_depth_averaging']:
                data = fields_util.depth_aver_SlayerLSC_in4D(data, grid_time_buffers['zlevel'], grid['bottom_cell_index'])

            m1 = m + component_info['num_components']

            # get view of where in buffer data is to be placed
            if var_info['is_time_varying']:
                field.data[buffer_index, :, :, m:m1] = data
            else:
                field.data[0, :, :, m:m1] = data

            m += component_info['num_components']

        # return a view of data added to buffer to allow pre-processing
        data_added_to_buffer= field.data[buffer_index, ...] if field.params['is_time_varying'] else field.data[0,...]
        return data_added_to_buffer

    def read_file_field_variable_as4D(self, nc, file_var_info,is_time_varying, file_index=None):
        # reformat file variable into 4D time,node,depth, components  form
        var_name= file_var_info['name_in_file']

        data = nc.read_a_variable(var_name, sel= file_index if is_time_varying else None).astype(np.float32) # allow for time independent data

        # reorder dim to time,node,depth, components order, if present
        # default is in correct order

        # now reshape in 4D
        if not self.is_file_variable_time_varying(nc,var_name): data = data[np.newaxis,...]
        if not self.is_var_in_file_3D(nc, var_name):    data = data[:, :, np.newaxis,...]
        if file_var_info['num_components'] == 1:             data = data[:, :, :, np.newaxis]

        return data

    def global_index_to_buffer_index(self, nt):
        if self.shared_info.backtracking:
            # nt decreases through model run, but buffer goes forward through buffer
            return self.buffer_info['nt_buffer0'] - nt
        else:
            # nt increases through model run
            return nt - self.buffer_info['nt_buffer0']


    def read_dry_cell_data(self,nc,file_index,is_dry_cell_buffer, buffer_index):
        # calculate dry cell flags, if any cell node is dry
        si = self.shared_info
        grid = self.grid
        grid_time_buffers = self.grid_time_buffers
        fields = si.classes['fields']

        if self.params['grid_variables']['is_dry_cell'] is None:
            if grid_time_buffers['zlevel'] is None:
                reader_util.set_dry_cell_flag_from_tide( grid['triangles'],
                                                        fields['tide'].data, fields['water_depth'].data,
                                                        si.minimum_total_water_depth, is_dry_cell_buffer,buffer_index)
            else:
                reader_util.set_dry_cell_flag_from_zlevel( grid['triangles'],
                                                          grid_time_buffers['zlevel'], grid['bottom_cell_index'],
                                                          si.minimum_total_water_depth, is_dry_cell_buffer,buffer_index)
        else:
            # get dry cells for each triangle allowing for splitting quad cells
            data_added_to_buffer = nc.read_a_variable(self.params['grid_variables']['is_dry_cell'], file_index)
            is_dry_cell_buffer[buffer_index, :] = append_split_cell_data(grid, data_added_to_buffer, axis=1)
            #grid['is_dry_cell'][buffer_index, :] =  np.concatenate((data_added_to_buffer, data_added_to_buffer[:, grid['quad_cell_to_split_index']]), axis=1)

    def read_open_boundary_data(self, grid):
        open_boundary_nodes = np.full((grid['x'].shape[0]),0,np.int8)
        open_boundary_adjacency= np.full_like(grid['triangles'],0,dtype=np.int8)
        return open_boundary_nodes, open_boundary_adjacency


    def get_first_time_in_hindcast(self):
        return self.reader_build_info['sorted_file_info']['time_start'][0]

    def get_last_time_in_hindcast(self):
        return self.reader_build_info['sorted_file_info']['time_end'][-1]

    def get_hindcast_duration(self):
        return abs(self.get_last_time_in_hindcast() - self.get_first_time_in_hindcast())

    def time_to_global_time_step(self, t):
        si = self.shared_info
        fi = self.reader_build_info['sorted_file_info']
        nt = (fi['n_time_steps_in_hindcast'] - 1) * (t - self.get_first_time_in_hindcast()) / (self.get_last_time_in_hindcast() - self.get_first_time_in_hindcast())
        if si.backtracking:
            nt = np.ceil(nt)
        else:
            nt = np.floor(nt)
        return int(nt)

    def get_hindcast_info(self):
        d={'time_zone':  self.params['time_zone'],
           'hindcast_starts': time_util.seconds_to_iso8601str(self.get_first_time_in_hindcast()),
           'hindcast_ends':time_util.seconds_to_iso8601str(self.get_last_time_in_hindcast()),
           'hindcast_duration_days':(self.get_last_time_in_hindcast() - self.get_first_time_in_hindcast())/24/3600.,  # info_file = BuildCaseInfoFile()
           'hindcast_timestep': self.reader_build_info['sorted_file_info']['time_step'],
           'input_dir' : self.params['input_dir'],
           'first_file': self.reader_build_info['sorted_file_info']['names'][0],
           'last_file' : self.reader_build_info['sorted_file_info']['names'][-1]
           }

        return d

    def _open_grid_file(self,reader_build_info):
        if self.params['grid_file']:
            file_name = path.join(self.params['input_dir'],self.params['grid_file'])
        else:
            file_name= reader_build_info['sorted_file_info']['names'][0]

        nc =NetCDFhandler(file_name, 'r')
        return nc

    def set_up_shared_grid_memory(self, reader_build_info):
        if 'shared_memory' not in reader_build_info:
            # build shared memory and add to reader_build_info
            reader_build_info['shared_memory'] = {'grid': {},'fields':{}}
            for key, item in self.grid.items():
                if item is not None:
                    sm = shared_memory.SharedMemArray(values=item)
                    self.shared_memory['grid'][key] = sm
                    reader_build_info['shared_memory']['grid'][key] = sm.get_shared_mem_map()
        else:
            # build grid variables from reader_build_info shared_memory info
            for key, item in reader_build_info['shared_memory']['grid'].items():
                self.shared_memory['grid'][key] = shared_memory.SharedMemArray(sm_map=item)
                self.grid[key] = self.shared_memory['grid'][key].data  # grid variables is shared version

    def close(self):
        # release any shared memory
        sm_info=self.shared_memory
        for sm in list(sm_info['grid'].values())+ list(sm_info['grid'].values()):
            sm.delete()



