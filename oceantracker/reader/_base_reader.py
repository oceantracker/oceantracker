import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.message_and_error_logging import append_message, GracefulExitError
from oceantracker.util import time_util
from os import path, walk
from glob import glob
from oceantracker.util.ncdf_util import NetCDFhandler
from time import perf_counter
from oceantracker.fields.util import fields_util
from oceantracker.util.basic_util import nopass
from oceantracker.fields.util.fields_util import depth_aver_SlayerLSC_in4D
from copy import copy
from oceantracker.util.cord_transforms import WGS84_to_UTM

class _BaseReader(ParameterBaseClass):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({'input_dir': PVC(None, str),
                                 'minimum_total_water_depth': PVC(0.25, float, min=0.0,doc_str= 'Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering'),
                                 'time_zone': PVC(None, int, min=-12, max=23),
                                 'cords_in_lat_long': PVC(False, bool),
                                 'time_buffer_size': PVC(48, int, min=2),
                                 'file_mask': PVC(None, str, is_required=True),
                                 'depth_average': PVC(False, bool),  # turns 3D hindcast into a 2D one
                                 'field_variables_to_depth_average': PLC(None, str),  # list of field_variables that are depth averaged on the fly
                                 'grid_variables': {'time': PVC('time', str, is_required=True),
                                                    'x': PLC(['x', 'y'], str, fixed_len=2),
                                                    'triangles': PVC(None, str, is_required=True),
                                                    'zlevel': PVC(None, str),
                                                    'bottom_cell_index': PVC(None, str),
                                                    },
                                 'field_variables': {'water_velocity': PLC(['u', 'v', None], str, fixed_len=3),
                                                     'tide': PVC(None, str),
                                                     'water_depth': PVC(None, str),
                                                     'water_temperature': PVC(None, str),
                                                     'water_salinity': PVC(None, str)},

                                 'dimension_map': {'time': PVC('time', str), 'node': PVC('node', str), 'z': PVC(None, str),
                                                   'vector2Ddim': PVC(None, str), 'vector3Ddim': PVC(None, str)},
                                 'isodate_of_hindcast_time_zero': PVC('1970-01-01', 'iso8601date'),
                                 'search_sub_dirs': PVC(False, bool),
                                 'max_numb_files_to_load': PVC(10 ** 7, int, min=1)
                                 })  # list of normal required dimensions

        self.buffer_info = {'n_filled': None}

    def _file_checks(self, file_name, msg_list): pass
    def read_hindcast_info(self,nc): pass  # read hindcast attibutes from first file, eg z transforms for ROMS files
    def _setup_grid(self, nc, reader_build_info): nopass('_setup_grid required')
    def  preprocess_field_variable(self, name, data, nc=None): return data # allows tweaks to named fields, eg if name=='depth:
    def _build_grid_attributes(self, grid): pass

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

    def get_field_variable_info(self, nc, name):
        # get info from list of component eg ['temp'], ['u','v']
        si= self.shared_info
        var_list = self.params['field_variables'][name]
        if type(var_list) is not list: var_list=[var_list] # if a string make a list of 1
        var_list = [v for v in var_list if v != None]
        var_file_name0=var_list[0]





        if self.params['dimension_map']['z'] is not None and nc.is_var_dim(var_file_name0, self.params['dimension_map']['z']):
            is3D_in_file = True
        else:
            is3D_in_file = False

        unpacking_info={'variable_list':[],
                        'is3D_in_file': is3D_in_file,
                        'requires_depth_averaging': self.params['depth_average'] and is3D_in_file}

        # work out number of components in list of variables
        dm= self.params['dimension_map']
        n_total_comp=0

        for file_var_name in var_list:
            if dm[ 'vector2Ddim'] is not None and  nc.is_var_dim(file_var_name, dm['vector2Ddim']):
                n_comp = 2
            elif dm[ 'vector3Ddim'] is not None and  nc.is_var_dim(file_var_name, dm['vector3Ddim']):
                n_comp = 3
            else:
                n_comp = 1

            n_total_comp += n_comp
            unpacking_info['variable_list'].append({'name_in_file':file_var_name, 'num_components': n_comp })

        # if a 3D var and vector then it must have  3D components
        # eg this allows for missing vertical velocity, to have zeros in water_velocity
        if is3D_in_file and n_total_comp> 1: n_total_comp =3

        params = {'name': name,
             'dtype': nc.get_var_dtype(var_file_name0),
             'is_time_varying': nc.is_var_dim(var_file_name0, self.params['dimension_map']['time']),
             'num_components' : n_total_comp,
             'is3D' :  False if unpacking_info['requires_depth_averaging'] else is3D_in_file
            }

        return params, unpacking_info

    def fill_time_buffer(self, nt):
        # fil buffer frpom global time step ntb0
        self.code_timer.start('reading_to_fill_time_buffer')
        si = self.shared_info
        grid= si.grid
        fi = self.reader_build_info['sorted_file_info']

        # get indicies of first block
        nt_required = nt[:self.params['time_buffer_size']].copy()

        # trim required global time steps to hindcast range
        nt_required = nt_required[np.logical_and(nt_required >= fi['nt'][0], nt_required <= fi['nt'][-1])]

        t0 = perf_counter()
        b0 = 0
        total_read = 0

        while len(nt_required) > 0:
            # find block of time step with same file number as that of first required time step
            n_file = fi['file_number'][nt_required[0]]
            nt_available = nt_required[fi['file_number'][nt_required] == n_file]  # global time steps to load

            # read from this file
            nc = NetCDFhandler(fi['names'][n_file], 'r')

            num_read = len(nt_available)
            buffer_index = b0 + np.arange(num_read)
            file_index = fi['file_offset'][nt_available]

            s = 'Reading-file-' + ':%1.0f-' % n_file + path.basename(fi['names'][n_file]) + ':%04.0f' % file_index[0] + ':%04.0f:' % file_index[-1]
            s += ', Steps in file %4.0f' % fi['n_time_steps'][n_file]
            s += ' nt available %4.0f' % nt_available[0] + ':%4.0f' % nt_available[-1]
            s += ' file offsets %4.0f' % file_index[0] + ':%4.0f' % file_index[-1]
            s += ' nt start of buffer-%4.0f' % nt[0]
            s += ' Required:%4.0f ' % nt_required.shape[0]

            si.case_log.write_progress_marker(s)
            self.read_time_variable_grid_variables(nc, buffer_index, file_index)

            # read time varying vector and scalar reader fields
            for name, field in si.class_list_interators['fields']['from_reader_field'].items():
                if field.is_time_varying():
                    data = self.read_field_variable_as4D(nc, field, file_index=file_index)
                    field.data[buffer_index, ...] = self.preprocess_field_variable(name, data, nc=nc)

                    if name in self.params['field_variables_to_depth_average']:
                        data = fields_util.depth_aver_SlayerLSC_in4D(data, si.grid['zlevel'], si.grid['bottom_cell_index'])
                        si.classes['fields'][name + '_depth_average'].data[buffer_index, ...] = data
            nc.close()

            # update user fields from newly read fields
            for field_types in ['derived_from_reader_field','user']:
                for field in si.class_list_interators['fields'][field_types].values():
                    if field.is_time_varying():
                        field.update(buffer_index)

            if 'total_water_depth' in si.classes['fields']:
                # calculate dry cell flags, if any cell node is dry
                si.grid['is_dry_cell'][:] = 0
                for nn in range(3):
                    sel = si.classes['fields']['total_water_depth'].data[:, si.grid['triangles'][:, nn], 0, 0] <= si.minimum_total_water_depth
                    si.grid['is_dry_cell'][sel] = 1

            total_read += num_read
            s = '    read file at time ' + time_util.seconds_to_pretty_str(si.grid['time'][buffer_index[0]])
            s += ' file offsets %4.0f' % file_index[0] + ':%4.0f' % file_index[-1]
            s += ' buffer offsets-%4.0f' % buffer_index[0] + ':%4.0f' % buffer_index[-1]
            s += ' Read:%4.0f ' % num_read + ' time:%4.0f ' % (1000. * (perf_counter() - t0)) + ' ms '

            si.case_log.write_progress_marker(s)
            b0 += num_read
            n_file += int(si.model_direction)
            nt_required = nt_required[num_read:]

        self.buffer_info['n_filled'] = total_read
        self.buffer_info['nt_buffer0'] = nt[0]  # global index of buffer zero

        self.code_timer.stop('reading_to_fill_time_buffer')
        return total_read

    def read_field_variable_as4D(self,nc, field, file_index=None):
        si= self.shared_info
        # set up space to read data into
        sd=[1,] + list(field.data.shape[1:])
        if field.info['requires_depth_averaging'] and field.info['is3D_in_file']:
            sd[2] = nc.get_dim_size(self.params['dimension_map']['z'])
        if file_index is not None: sd[0] = file_index.shape[0]

        data = np.full(sd,0, dtype=field.data.dtype)
        m = 0
        for var in field.info['variable_list']:
            s= [file_index.shape[0] if field.params['is_time_varying'] else 1,
                   si.grid['x'].shape[0],
                   si.grid['nz'] if field.info['is3D_in_file'] else 1,
                   var['num_components']]
            if  var['num_components'] == 1:
                data[:, :,:, m] = nc.read_a_variable(var['name_in_file'], file_index).reshape(s[:-1])
            else:
                data[:, :, :, range(m, m + var['num_components'])] = nc.read_a_variable(var['name_in_file'], file_index).reshape(s)
            m += var['num_components']

        if field.info['requires_depth_averaging']:
            data = depth_aver_SlayerLSC_in4D(data, si.grid['zlevel'], si.grid['bottom_cell_index'])
        return data

    def is_in_buffer(self, nt):
        return self.buffer_info['nt_buffer0'] <= nt < self.buffer_info['nt_buffer0'] + self.buffer_info['n_filled']

    def global_index_to_buffer_index(self, nt):
        if self.shared_info.backtracking:
            # nt decreases through model run, but buffer goes forward trhrough buffer
            return self.buffer_info['nt_buffer0'] - nt
        else:
            # nt increases through model run
            return nt - self.buffer_info['nt_buffer0']

    def read_x(self, nc):
        x = np.full((nc.get_dim_size(self.params['dimension_map']['node']),2),0.)
        x[:, 0] = nc.read_a_variable(self.params['grid_variables']['x'][0])
        x[:, 1] = nc.read_a_variable(self.params['grid_variables']['x'][1])
        if self.params['cords_in_lat_long']:
            x = WGS84_to_UTM(x)
        return x

    def read_open_boundary_data(self, grid):
        grid['grid_outline']['open_boundary_nodes'] = []
        return grid

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
           'hindcast_duration':time_util.duration_str_from_seconds(self.get_last_time_in_hindcast() - self.get_first_time_in_hindcast()),  # info_file = BuildCaseInfoFile()
           'hindcast_timestep': self.reader_build_info['sorted_file_info']['time_step'],
           'input_dir' : self.params['input_dir'],
           'first_file': self.reader_build_info['sorted_file_info']['names'][0],
           'last_file' : self.reader_build_info['sorted_file_info']['names'][-1]
           }

        return d

