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

class _BaseReader(ParameterBaseClass):

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
            'field_variables': PLC([], [str], obsolete=' parameter obsolete, use "load_fields" parameter, with field_variable_map if needed',
                                   make_list_unique=True),
            'field_variable_map': {'water_velocity': PLC(['u', 'v', 'w'], [str, None], fixed_len=3, is_required=True, doc_str='maps standard internal field name to file variable names for velocity components'),
                                'tide': PVC('elev', str, doc_str='maps standard internal field name to file variable name'),
                                'water_depth': PVC('depth', str, is_required=True,doc_str='maps standard internal field name to file variable name'),
                                'water_temperature': PVC('temp', str,doc_str='maps standard internal field name to file variable name'),
                                'salinity': PVC(None, str,doc_str='maps standard internal field name to file variable name'),
                                'wind_stress': PVC(None, str,doc_str='maps standard internal field name to file variable name'),
                                'bottom_stress': PVC(None, str,doc_str='maps standard internal field name to file variable name'),
                                'water_velocity_depth_averaged': PLC([], [str, None],fixed_len=2,
                                                                     doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available',
                                                                     make_list_unique=True)
                                },
            'dimension_map': {'time': PVC('time', str, is_required=True),
                              'node': PVC('node', str),
                              'z': PVC(None, str,doc_str='name of dim for vertical layer boundaries'),
                              'vector2D': PVC(None, str),
                              'vector3D': PVC(None, str)},
            'CRS_transform_code':  PVC(None, int, doc_str='CRY code for coordinate conversion of hydro-model lon-lat to a meters grid , eg. CRS for NZTM is 2193'),

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

        grid = self.read_2Dgrid(nc)
        self.grid= self.build_2Dgrid(grid)

        if si.is3D_run:
            grid = self.build_vertical_grid(nc, grid)
        else:
            #2D
            grid['zlevel'] = None
            grid['nz'] = 1  # only one z

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

    def final_setup(self):
        # set up particle properties accocated with fields
        si = self.shared_info
        for name, i in si.classes['fields'].items():
            if i.params['create_particle_property_with_same_name']:
                si.classes['particle_group_manager'].add_particle_property(name, 'from_fields',
                        dict(time_varying=i.is_time_varying(),
                         vector_dim=i.get_number_components()),
                        crumbs= f' reader field setup > "{name}"'
                        )

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

    def open_first_file(self):
        si = self.shared_info

        fi= si.working_params['file_info']
        nc = NetCDFhandler(fi['names'][0], 'r')
        return nc

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
            sel = np.abs(dt_gaps) > 2.5* fi['hydro_model_time_step']
            if np.any(sel):
                msg_logger.msg('Some time gaps between hydro-model files is are > 2.5 times average time step, check hindcast files are all present??', hint='check hindcast files are all present and times in files consistent', warning=True)
                for n in np.flatnonzero(sel):
                    msg_logger.msg(' large time gaps between file ' + fi['names'][n] + ' and ' + fi['names'][n + 1], tabs=1)

        msg_logger.exit_if_prior_errors('exiting from _get_hindcast_files_info, in setting up readers')
        return fi



    def is_3D_hydromodel(self,nc):
        return  True if nc.is_var_dim( self.params['field_variable_map']['water_velocity'][0],self.params['dimension_map']['z_water_velocity'] ) else False

    def is_3D_variable(self,nc, var_name):
        # is variable 3D
        return  nc.is_var_dim(var_name,self.params['dimension_map']['z'])


    def read_2Dgrid(self, nc):
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

        grid = self.read_nodal_x(nc, grid)
        grid['x'] = grid['x'].astype(np.float64)

        grid = self.read_triangles(nc, grid)
        # ensure np.int32 values
        grid['triangles']=grid['triangles'].astype(np.int32)
        grid['quad_cells_to_split'] = grid['quad_cells_to_split'].astype(np.int32)

        return grid

    def build_2Dgrid(self, grid):
        # set up grid variables which don't vary in time and are shared by all case runners and main
        # add to reader build info
        si = self.shared_info
        info = self.info
        msg_logger = self.msg_logger
        msg_logger.progress_marker('Starting grid setup')

        # node to cell map
        t0 = perf_counter()
        grid['node_to_tri_map'], grid['tri_per_node'] = triangle_utilities_code.build_node_to_triangle_map(grid['triangles'], grid['x'])
        msg_logger.progress_marker('built node to triangles map', start_time=t0)

        # adjacency map
        t0 = perf_counter()
        grid['adjacency'] = triangle_utilities_code.build_adjacency_from_node_tri_map(grid['node_to_tri_map'], grid['tri_per_node'], grid['triangles'])
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

        # space for dry cell info
        grid['is_dry_cell'] = np.full((self.params['time_buffer_size'], grid['triangles'].shape[0]), 1, np.int8)

        # reader working space for 0-255 index of how dry each cell is currently, used in stranding, dry cell blocking, and plots
        grid['dry_cell_index'] = np.full((grid['triangles'].shape[0],), 0, np.uint8)


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


    def setup_fields(self, nc):

        si= self.shared_info
        fgm = si.classes['field_group_manager']
        vi = self.info['field_variable_info']
        grid = self.grid

        info=self.info
        params = self.params

        # setup compulsory fields, plus others required
        params['load_fields'] = list(set(['water_velocity','tide','water_depth'] + params['load_fields'] ))
        for name in  params['load_fields'] :
            if name in params['field_variable_map']:
                file_var_map = params['field_variable_map'][name]
            else:
                file_var_map = name # assume given field variable is in the file
            vi[name] =self.field_var_info(nc,file_var_map )
            fgm.add_reader_field(name, self, vi[name] , crumbs='Reader Field' )

        # add core total water depth property
        fgm.add_custom_field('total_water_depth',
                dict( class_name= 'oceantracker.fields.total_water_depth.TotalWaterDepth',time_varying=True,write_interp_particle_prop_to_tracks_file =False),
                                           crumbs='initializing core TotalWaterDepth class ')

        # read time independent vector and scalar reader fields
        for name, field in si.classes['fields'].items():
            if not field.is_time_varying() and isinstance(field,ReaderField):
                data = self.assemble_field_components(nc, name)
                field.data[0, ...] = data

    def build_vertical_grid(self, nc, grid):
        # setup transforms on the data, eg regrid vertical if 3D to same sigma levels
        si= self.shared_info
        params = self.params
        info = self.info

        grid['bottom_cell_index'] = self.read_bottom_cell_index(nc).astype(np.int32)

        # set up zlevel
        if si.settings['regrid_z_to_uniform_sigma_levels']:
            # setup  regrid grid equal time invariace sigma layers
            # based on profile with thiniest top nad bootm layers

            # read first zlevel time step
            zlevel = nc.read_a_variable(params['grid_variable_map']['zlevel'], sel=0)
            # use node with thinest top/bot layers as template for all sigma levels

            node_min, grid['zlevel_fractions'] = hydromodel_grid_transforms.find_node_with_smallest_top_bot_layer(zlevel, grid['bottom_cell_index'],si.z0)

            # use layer fractions from this node to give layer fractions everywhere
            # in LSC grid this requires stretching a bit to give same number max numb. of depth cells
            nz_bottom = grid['bottom_cell_index'][node_min]

            # stretch sigma out to same number of depth cells,
            # needed for LSC grid if node_min profile is not full number of cells
            zf_model= grid['zlevel_fractions'][node_min,nz_bottom:]
            nz = grid['zlevel_fractions'].shape[1]
            nz_fractions = nz - nz_bottom
            grid['sigma']  =np.interp(np.arange(nz)/nz,  np.arange(nz_fractions)/nz_fractions,zf_model)
            grid['nz'] =grid['sigma'].size # used to size field data arrays

            # setup lookup nz interval map of zfraction into with equal dz for finding vertical cell
            # need to check if zq > ['sigma_map_z'][nz+1] to see if nz must be increased by 1 tp get sigma interval
            dz = 0.66*abs(np.diff(grid['sigma']).min()) # approx dz
            nz_map = int(np.ceil(1.0/dz))  # number of cells in map
            grid['sigma_map_z'] =  np.arange(nz_map)/(nz_map-1) # zlevels at the map intervals
            grid['sigma_map_dz'] = np.diff(grid['sigma_map_z']).mean() # exact dz

            # make evenly spaced map which gives cells contating a sigma level
            grid['sigma_map_nz_interval_with_sigma'] = np.zeros((nz_map,), dtype=np.int32)
            interval_with_sigma_level = (grid['sigma']*nz_map).astype(np.int32)
            
            # omit sigma = 0 and 1 from intervals, to ensurethey fall in first and last intervals
            grid['sigma_map_nz_interval_with_sigma'][ interval_with_sigma_level[1:-1] ] = 1
            grid['sigma_map_nz_interval_with_sigma'] =  grid['sigma_map_nz_interval_with_sigma'].cumsum()

        else:
            # native  vertical grid option, could be  Schisim LCS vertical grid
            grid['nz']= nc.dim_size(params['dimension_map']['z'])  # used to size field data arrays
            s = [self.params['time_buffer_size'], grid['x'].shape[0], grid['nz']]
            grid['zlevel'] = np.zeros(s, dtype=np.float32, order='c')

        return grid


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

    def read_nodal_x(self, nc, grid):
        params= self.params
        var_name = params['grid_variable_map']['x']
        grid['x'] = np.column_stack((nc.read_a_variable(var_name[0]), nc.read_a_variable(var_name[1])))

        if self.params['cords_in_lat_long']:
            grid['x'] = self.convert_lon_lat_to_meters_grid(grid['x'])

        return grid

    def read_triangles(self, nc, grid):
        # return triangulation
        # if triangualur has /quad cells
        params = self.params
        var_name = params['grid_variable_map']['triangles']
        grid['triangles'] = nc.read_a_variable(var_name).astype(np.int32)

        if params['one_based_indices']:  grid['triangles'] -= 1

        # note indices of any triangles neeeding splitting
        grid['triangles_to_split'] =  np.full((0,),0,np.int32)
        return grid

    def preprocess_field_variable(self, nc, name, data): return data

    # checks on first hindcast file
    def additional_setup_and_hindcast_file_checks(self, nc,msg_logger): pass


    #@function_profiler(__name__)
    def fill_time_buffer(self, time_sec):
        # fill as much of  hindcast buffer as possible starting at global hindcast time step nt0_buffer
        # fill buffer starting at hindcast time step nt0_buffer
        # todo change so does not read current step again after first fill of buffer

        si = self.shared_info
        params = self.params
        fields = si.classes['fields']
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

        # need tide and water depth at front of order, before water velocity, to read fields to regrid in vertical
        field_names = list(fields.keys())
        for name in ['tide', 'water_depth','water_velocity']:
            field_names.remove(name)
            field_names.insert(0, name)

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
            # do this in order set above
            for name in field_names:
                field = fields[name]
                if field.is_time_varying() and field.info['group'] =='reader_field':
                    data  = self.assemble_field_components(nc, name, file_index=file_index)
                    data = self.preprocess_field_variable(nc, name, data) # in place tweaks, eg zero vel at bottom

                    junk = data
                    if field.is3D() and si.settings['regrid_z_to_uniform_sigma_levels']:
                        s = list(np.asarray(data.shape, dtype=np.int32))
                        s[2] = grid['sigma'].size
                        out = np.full(tuple(s), np.nan, dtype=np.float32)
                        data = hydromodel_grid_transforms.interp_4D_field_to_fixed_sigma_values(
                                    grid['zlevel_fractions'], grid['bottom_cell_index'],
                                    grid['sigma'],
                                    fields['water_depth'].data, fields['tide'].data,
                                    si.z0, si.minimum_total_water_depth,
                                    data, out,
                                    name=='water_velocity')

                    #o = reader_util.get_values_at_bottom(junk, grid['bottom_cell_index'])
                    #pass

                    # insert data
                    field.data[buffer_index, ...] = data

                    if False:
                        # check overplots of regridding
                        from matplotlib import pyplot as plt
                        nn= 300  # for test hindcats
                        nn = 1000
                        plt.plot(grid['zlevel_fractions'][nn,:],junk[0,nn,:,0],c='g')
                        plt.plot(grid['zlevel_fractions'][nn, :], junk[0, nn, :, 0], 'g.')
                        plt.plot(grid['sigma'], data[0, nn, :, 0], 'r--')
                        plt.plot(grid['sigma'], data[0, nn, :, 0],'rx')
                        #plt.show(block= True)
                        plt.savefig('\myfig.png')



            # read grid time, zlevel
            # do this after reading fields as some hindcasts required tide field to get zlevel, eg FVCOM
            self.read_time_variable_grid_variables(nc, buffer_index,file_index)

            nc.close()

            # now all  data has been read from file, now
            # update user fields from newly read fields and data
            for name, field in fields.items():
                if field.is_time_varying() and field.info['group']=='custom_field':
                    field.update(buffer_index)

            total_read += num_read

            # set up for next step

            bi['buffer_available'] -= num_read
            n_file += si.model_direction
            nt_hindcast_required = nt_hindcast_required[num_read:]
            bi['time_steps_in_buffer'] += nt_file.tolist()

        si.msg_logger.progress_marker(f' read {total_read:3d} time steps in  {perf_counter() - t0:3.1f} sec', tabs=2)
        # record useful info/diagnostics
        bi['n_filled'] = total_read

    def assemble_field_components(self,nc, name, file_index=None):
        # read scalar fields / join together the components which make vector from component list
        si = self.shared_info
        field = si.classes['fields'][name]

        params = self.params

        s= list(field.data.shape)
        s[0] = 1 if file_index is None else file_index.size
        out  = np.zeros(s,dtype=np.float32) #todo faster make a generic  buffer at start

        m= 0 # num of vector components read so far

        var_names = params['field_variable_map'][name] if type(params['field_variable_map'][name]) ==list  else [params['field_variable_map'][name]]

        for var_name in var_names:
            if var_name is None: continue
            data = self.read_file_var_as_4D_nodal_values(nc, var_name, file_index)
            comp_per_var = data.shape[3]
            m1 = m + comp_per_var
            # get view of where in buffer data is to be placed
            out[:, :, :, m:m1] = data
            m += comp_per_var
        return out

    def read_file_var_as_4D_nodal_values(self,nc,var_name, file_index=None):
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

    def read_time_variable_grid_variables(self, nc, buffer_index, file_index):
        # read time and  grid variables, eg time,dry cell
        si = self.shared_info
        grid = self.grid

        grid['time'][buffer_index] = self.read_time_sec_since_1970(nc, file_index=file_index)

        # do time zone adjustment
        if self.params['time_zone'] is not None:
            grid['time'][buffer_index] += self.params['time_zone'] * 3600.

        # add date for convenience
        grid['date'][buffer_index] = time_util.seconds_to_datetime64(grid['time'][buffer_index])

        self.read_dry_cell_data(nc, file_index, grid['is_dry_cell'], buffer_index)

        if si.is3D_run:
            # grid['total_water_depth'][buffer_index,:]= np.squeeze(si.classes['fields']['tide'].data[buffer_index,:] + si.classes['fields']['water_depth'].data)
            # read zlevel inplace to save memory?
            if not si.settings['regrid_z_to_uniform_sigma_levels']:
                # native zlevel grid and used for regidding in sigma
                self.read_zlevel_as_float32(nc, file_index, grid['zlevel'], buffer_index)


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


    def read_bottom_cell_index(self, nc):
        # assume  not LSc grid, so bottom cel is zero
        return np.full((self.grid['x'].shape[0],),0, dtype=np.int32)


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

        if self.params['CRS_transform_code'] is None:
            x_out = cord_transforms.WGS84_to_UTM( x, out=None)
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
        nc.write_a_new_variable('water_depth', si.classes['fields']['water_depth'].data.ravel(), ('node_dim',))
        nc.close()

        output_files['grid_outline'] = output_files['output_file_base'] + '_grid_outline.json'
        json_util.write_JSON(path.join(output_files['run_output_dir'], output_files['grid_outline']), grid['grid_outline'])


    def close(self):
       pass