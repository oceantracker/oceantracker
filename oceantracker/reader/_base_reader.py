import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util
from os import path, walk
from glob import glob
from oceantracker.util.ncdf_util import NetCDFhandler
from time import perf_counter
from oceantracker.util.basic_util import nopass
from oceantracker.reader.util.reader_util import append_split_cell_data
from oceantracker.util import  cord_transforms
from oceantracker.reader.util import shared_reader_memory_util
from oceantracker.util.profiling_util import function_profiler

from oceantracker.reader.util import reader_util

class _BaseReader(ParameterBaseClass):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({'input_dir': PVC(None, str),
                                 'file_mask': PVC(None, str, is_required=True, doc_str='Mask for file names, eg "scout*.nc", is joined with "input_dir" to give full file names'),
                                 'grid_file': PVC(None, str, doc_str='File name with hydrodynamic grid data, as path relative to input_dir, default is get grid from first hindasct file'),
                                 'time_zone': PVC(None, int, min=-12, max=12,doc_str='time zone in hours relative to UTC/GMT , eg NZ standard time is time zone 12'),
                                 'cords_in_lat_long': PVC(False, bool),
                                 'time_buffer_size': PVC(48, int, min=2),
                                 'required_file_variables' :PLC([], [str]),
                                 'required_file_dimensions': PLC([], [str]),
                                 'water_density': PVC(48, int, min=2),
                                 'field_variables_to_depth_average': PLC([], [str]),  # list of field_variables that are depth averaged on the fly
                                 'one_based_indices' :  PVC(False, bool,doc_str='indices in hindcast start at 1, not zero, eg. triangulation nodes start at 1 not zero as in python'),
                                 'EPSG_transform_code' : PVC(None, int, min=0,
                                                   doc_str='Integer code needed to enable transformation from/to meters to/from lat/lon (see https://epsg.io/ to find EPSG code for hydro-models meters grid)'),
                                 'grid_variables': {'time': PVC('time', str, is_required=True),
                                                    'x': PLC(['x', 'y'], [str], fixed_len=2),
                                                    'zlevel': PVC(None, str),
                                                    'bottom_cell_index': PVC(None, str),
                                                    'is_dry_cell': PVC(None, np.int8, doc_str='Time variable flag of when cell is dry, 1= is dry cell')},
                                 'field_variables': {'water_velocity': PLC(['u', 'v', None], [str, None], fixed_len=3,is_required=True),
                                                     'water_depth': PVC(None, str),
                                                     'tide': PVC(None, str),
                                                     'water_temperature': PVC(None, str),
                                                     'salinity': PVC(None, str),
                                                     'wind_stress': PVC(None, str),
                                                     'bottom_stress': PVC(None, str),
                                                     },

                                 'dimension_map': {'time': PVC('time', str, is_required=True), 'node': PVC('node', str), 'z': PVC(None, str),
                                                   'vector2Ddim': PVC(None, str), 'vector3Ddim': PVC(None, str)},
                                 'isodate_of_hindcast_time_zero': PVC('1970-01-01', 'iso8601date'),
                                 'search_sub_dirs': PVC(True, bool),
                                 'max_numb_files_to_load': PVC(10 ** 7, int, min=1)
                                 })  # list of normal required dimensions

        # store instances of shared memory classes for variables shared between processes
        self.shared_memory= {'grid' :{}, 'fields':{},'control':{}}
        self.grid={}

    def initial_setup(self):
        si = self.shared_info
        self.file_info = si.working_params['file_info']
        nc= self._open_first_file(self.file_info)

        self.grid = self.build_grid(nc, self.grid)

        nc.close()


    def read_nodal_x_as_float64(self, nc): nopass('reader method: read_x is required')
    def read_bottom_cell_index_as_int32(self, nc):nopass('reader method: read_bottom_cell_index_as_int32 is required for 3D hindcasts')

    # required methods time dependent variables, also require a set up method
    def read_zlevel_as_float32(self, nc, file_index, zlevel_buffer, buffer_index): nopass('reader method: read_zlevel_as_float32 is required for 3D hindcasts')

    # checks on first hindcast file
    def additional_setup_and_hindcast_file_checks(self, nc,msg_logger): pass

    def build_grid(self, nc, grid): nopass('setup_grid required')

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

    def is_hindcast3D(self, nc): nopass('must define method to test if hindcast is 3D')

    # working methods

    def preprocess_field_variable(self, nc,name, data): return data # allows tweaks to named fields, eg if name=='depth:

    def _add_grid_attributes(self, grid): pass

    def initial_setup(self):
        # map variable internal names to names in NETCDF file
        # set update default value and vector variables map  based on given list
        si = self.shared_info
        grid = self.grid
        self.info['file_info']= si.working_params['file_info'] # add file_info to reader info

        nc = self._open_first_file(self.info['file_info'])
        grid = self.build_grid(nc, grid)

        # set up reader fields, using shared memory if requested
        self.setup_reader_fields(nc)
        nc.close()

    def get_list_of_files_and_hindcast_times(self):
        # get time sorted list of files matching mask

        input_dir= self.params['input_dir']

        if self.params['search_sub_dirs']:
            # search hindcast sub dirs
            file_names = []
            for root, dirs, files in walk(input_dir):
                # add matching files in root folder to list
                new_files = glob(path.join(root, self.params['file_mask']))
                if len(new_files) > 0: file_names += new_files
        else:
            file_names = glob(path.normpath(path.join(input_dir, self.params['file_mask'])))

        fi = {'names': file_names, 'n_time_steps': [], 'time_start': [], 'time_end': []}
        for n, fn in enumerate(file_names):
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
            self.msg_logger.msg('reader: cannot find any files matching mask "' + self.params['file_mask']
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

        return fi

    def get_hindcast_files_info(self):
        # read through files to get start and finish times of each file
        # create a time sorted list of files given by file mask in file_info dictionary
        # note this is only called once by OceantrackRunner to form file info list,
        # which is then passed to  OceanTrackerCaseRunner
        msg_logger = self.msg_logger
        # build a dummy non-initialise reader to get some methods and full params
        # add defaults from template, ie get reader class_name default, no warnings, but get these below
        # check cals name
        fi = self.get_list_of_files_and_hindcast_times()

        # checks on hindcast using first hindcast file
        nc = NetCDFhandler(fi['names'][0], 'r')
        self._basic_file_checks(nc, msg_logger)
        self.additional_setup_and_hindcast_file_checks(nc, msg_logger)
        hindcast_is3D = self.is_hindcast3D(nc)
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
        return fi, hindcast_is3D


    #@function_profiler(__name__)
    def setup_reader_fields(self, nc ):
        si = self.shared_info
        fgm = si.classes['field_group_manager']

        # setup reader fields from their named components in field_variables param ( water depth ad tide done earlier from grid variables)
        for name, item in self.params['field_variables'].items():
            if item is None : continue
            field_params,field_info =self.get_field_variable_info(nc,name,item)
            i = fgm.create_field('from_reader_field',field_params, crumbs='Reader - making reader field ')
            i.info['variable_info'] = field_info #needed to unpack reader variables

            if not i.params['is_time_varying']:
                # if not time dependent field read in now,
                data = self.assemble_field_components(nc, i)
                data = self.preprocess_field_variable(nc,name, data)
                i.data[:] = data

            # set up depth averaged version if requested
            if name in self.params['field_variables_to_depth_average']:
                # tweak shape to fit depth average of scalar or 3D vector
                p = {'class_name':'oceantracker.fields._base_field._BaseField',
                     'name': name + '_depth_average','num_components': min(2, i.params['num_components']),
                     'is_time_varying': i.params['is_time_varying'],
                    'is3D': False}
                fgm.create_field('depth_averaged_from_reader_field', p, crumbs='Reader - making depth averged version of reader field')

        # rinf buffer ono, needed to force read at first time step read to make
        bi = self.info['buffer_info']
        bi['n_filled'] = 0

        bi['buffer_size'] = self.params['time_buffer_size']
        bi['time_steps_in_buffer'] = []
        bi['buffer_available'] = bi['buffer_size']
        bi['nt_buffer0'] = 0


    def _basic_file_checks(self, nc, msg_logger):
        # check named variables are in first file
        # check dim
        for name, d in self.params['dimension_map'].items():
            if d is not None and not nc.is_dim(d):
                msg_logger.msg('Cannot find dimension_map dimension "' + name + ' ", file dimension given is "' + d + '"',
                               hint='Dimensions in hydro-model file = ' + str(nc.get_dims()),
                               fatal_error=True)

        # check variables are there
        for vm in ['grid_variables', 'field_variables']:
            for name, d in self.params[vm].items():
                if type(d)== list:
                    for vf in d:
                        if vf is not None and not nc.is_var(vf):
                            msg_logger.msg(' For  "' + vm + '" for param   "' + name + ' ",  cannot find variable in file  "' + vf + '"', fatal_error=True)

                elif d is not None and not nc.is_var(d) :
                    msg_logger.msg('For "' + vm + '" for param,  "' + name + ' ", cannot find variable in file "' + str(d) + '"', fatal_error=True)


        # check if all required dims and non-feilds variables present
        for v in self.params[ 'required_file_variables']:
            if not nc.is_var(v):
                msg_logger.msg('Cannot find required variable in hydro model output file "' + v + '"', fatal_error=True)

        for v in self.params[ 'required_file_dimensions']:
            if not nc.is_dim(v):
                msg_logger.msg( 'Cannot find required dimension in hydro model outptut file "' + v + '"', fatal_error=True)


    def get_field_variable_info(self, nc, name,var_list):
        # get info from list of component eg ['temp'], ['u','v']
        depth_averaging = self.shared_info.settings['run_as_depth_averaged']
        if type(var_list) is not list: var_list=[var_list] # if a string make a list of 1
        var_list = [v for v in var_list if v != None]
        var_file_name0=var_list[0]

        is3D_in_file = self.is_var_in_file_3D(nc, var_file_name0)
        is_time_varying = self.is_file_variable_time_varying(nc, var_file_name0)

        var_info= { 'component_list':[],
                    'is3D_in_file': is3D_in_file,
                    'is_time_varying': is_time_varying,
                    'requires_depth_averaging': depth_averaging and is3D_in_file}

        # work out number of components in list of variables
        n_total_comp=0
        for file_var_name in var_list:
            n_comp =self.get_num_vector_components_in_file_variable(nc,file_var_name)
            n_total_comp += n_comp
            var_info['component_list'].append({'name_in_file':file_var_name, 'num_components': n_comp })

        # if a 3D var and vector then it must have  3D components
        # eg this allows for missing vertical velocity, to have zeros in water_velocity
        if is3D_in_file and n_total_comp > 1: n_total_comp = 3  #todo not sure this is always safe

        # if depth averaging reduce to at most a 2D buffer
        if depth_averaging :  n_total_comp = min(2, n_total_comp)

        params = {'name': name,
                  'class_name': 'oceantracker.fields._base_field._BaseField' ,#'oceantracker.fields.reader_field.ReaderField',
             'is_time_varying':  is_time_varying,
             'num_components' : n_total_comp,
             'is3D' :  False if var_info['requires_depth_averaging'] else is3D_in_file
            }

        return params, var_info

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
                if field.is_time_varying() and field.info['field_type'] == 'from_reader_field':
                    data_added_to_buffer = self.assemble_field_components(nc, field, buffer_index=buffer_index, file_index=file_index)
                    data_added_to_buffer = self.preprocess_field_variable(nc, name, data_added_to_buffer) # do any customised tweaks

                    field.data[buffer_index, ...] = data_added_to_buffer

                    if name in self.params['field_variables_to_depth_average']:
                       si.classes['fields'][name + '_depth_average'].data[buffer_index, ...] = reader_util.depth_aver_SlayerLSC_in4D(data_added_to_buffer, grid['zlevel'], grid['bottom_cell_index'])

            # read grid time, zlevel
            # do this after reading fields as some hindcasts required tide field to get zlevel, eg FVCOM
            self.read_time_variable_grid_variables(nc, buffer_index,file_index)

            nc.close()

            # now all  data has been read from file, now
            # update user fields from newly read fields and data
            for name, i in si.classes['fields'].items():
                if i.is_time_varying() and i.info['field_type'] in ['derived_from_reader_field','user']:
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


    def assemble_field_components(self,nc, field, buffer_index=None, file_index=None):
        # read scalar fields / join together the components which make vector from component list

        grid = self.grid

        m= 0 # num of vector components read so far
        var_info = field.info['variable_info']
        for component_info in var_info['component_list']:
            data = self.read_file_field_variable_as4D(nc, component_info,var_info['is_time_varying'], file_index)

            if var_info['requires_depth_averaging']:
                data = reader_util.depth_aver_SlayerLSC_in4D(data, grid['zlevel'], grid['bottom_cell_index'])

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


    def read_dry_cell_data(self,nc,file_index,is_dry_cell_buffer, buffer_index):
        # calculate dry cell flags, if any cell node is dry
        grid = self.grid
        si = self.shared_info
        fields = si.classes['fields']

        if self.params['grid_variables']['is_dry_cell'] is None:
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
            data_added_to_buffer = nc.read_a_variable(self.params['grid_variables']['is_dry_cell'], file_index)
            is_dry_cell_buffer[buffer_index, :] = append_split_cell_data(grid, data_added_to_buffer, axis=1)

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

    def close(self):
        # release any shared memory
        sm_info=self.shared_memory
        for sm in list(sm_info['grid'].values())+ list(sm_info['grid'].values()):
            sm.delete()