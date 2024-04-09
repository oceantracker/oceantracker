import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC, ParameterTimeChecker as PTC
from oceantracker.util import time_util
from os import path
from oceantracker.util.ncdf_util import NetCDFhandler
from time import perf_counter
from oceantracker.util.basic_util import nopass
import oceantracker.reader.util.hydromodel_grid_transforms as hydromodel_grid_transforms

from oceantracker.util.cord_transforms import get_Metcator_info
from oceantracker.util import triangle_utilities

from oceantracker.reader.util import reader_util
from pathlib import Path as pathlib_Path
from oceantracker.definitions import node_types

from oceantracker.shared_info import SharedInfo as si

class _BaseReader(ParameterBaseClass):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({
            'input_dir': PVC(None, str, is_required=True),
            'file_mask': PVC(None, str, is_required=True, doc_str='Mask for file names, eg "scout*.nc", finds all files matching in  "input_dir" and its sub dirs that match the file_mask pattern'),
            'hydro_model_cords_in_lat_long': PVC(False, bool, doc_str='Force conversion given nodal lat longs to a UTM metres grid, only used if lat long coordinates not auto detected'),
            'vertical_regrid': PVC(True, bool, doc_str='Convert vertical grid to same sigma levels across domain'),
            'time_buffer_size': PVC(24, int, min=2),
            'load_fields': PLC(None, [str],
                               doc_str=' A list of names of any additional variables to read and interplolate to give particle values, eg. a concentration field (water_veloctiy, tide and water_depth fields are always loaded). If a given name is in field_variable_map, then the mapped file variables will be used internally and in output. If not the given file variable name will be used internally and in particle property output. For any additional vector fields user must supply a file variable map in the "field_variable_map" parameter',
                               make_list_unique=True),
            'field_variables': PLC(None, [str], obsolete=' parameter obsolete, use "load_fields" parameter, with field_variable_map if needed',                              make_list_unique=True),
            'field_variable_map': {'water_velocity': PLC(None, [str, None], fixed_len=3, is_required=True, doc_str='maps standard internal field name to file variable names for velocity components'),
                                   'tide': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                                   'water_depth': PVC(None, str, is_required=True, doc_str='maps standard internal field name to file variable name'),
                                   'A_Z_profile': PVC(None, str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                   'water_temperature': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                                   'salinity': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                                   'wind_stress': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                                   'bottom_stress': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                                   'water_velocity_depth_averaged': PLC(None, [str], fixed_len=2,
                                                                        doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
            'EPSG': PVC(None, int, doc_str='integer code for coordinate transform of hydro-model, only used if running in  lon-lat mode and code not in hindcast, eg. EPSG for New Zealand Transverse Mercator 2000 = 2193, find codes at https://spatialreference.org/'),
            'max_numb_files_to_load': PVC(10 ** 7, int, min=1, doc_str='Only read no more than this number of hindcast files, useful when setting up to speed run'),
            'dev_test_time' :PTC(expert=True)
        })  # list of normal required dimensions

        self.info['buffer_info'] = {}

    # Below are required  methods for any new reader
    # ---------------------------------------------------------

    def is_hindcast3D(self, nc):  nopass()

    def number_hindcast_zlayers(self, nc):  nopass()

    def read_time_sec_since_1970(self, nc, file_index=None):    nopass()

    def read_horizontal_grid_coords(self, nc, grid):   nopass()

    def read_triangles_as_int32(self, nc, grid):     nopass()

    # work out if field varible is ti depennt, 3D or a vector
    def get_field_params(self,nc, name):
        # returns    dict(time_varying= True/False,
        #                         is3D=True/False,
        #                         is_vector= True/False,
        #                         )
        nopass()

    def read_zlevel_as_float32(self, nc, grid,fields, file_index, zlevel_buffer, buffer_index):   nopass()

    def read_dry_cell_data(self, nc,grid,fields,  file_index, is_dry_cell_buffer, buffer_index):
        # read dry cell as =1 wet = 0
        nopass()

    def set_up_uniform_sigma(self,nc, grid):nopass()

    def get_file_list(self):

        params = self.params
        file_list = []
        for fn in pathlib_Path(params['input_dir']).rglob(params['file_mask']):
            file_list.append(path.abspath(fn))

        return file_list

    # default setup
    def setup_water_velocity(self,nc,grid):
        # tweak to be depth avearged
        fm = self.params['field_variable_map']

        if nc.is_var(fm['water_velocity'][0]):
            # check if vertical vel variable in file
            if not nc.is_var(fm['water_velocity'][1]):
                fm['water_velocity'] = [fm['water_velocity'][0]]
        else:
            # is depth averaged schism run
            fm['water_velocity'] =fm['water_velocity_depth_averaged']


    def preprocess_field_variable(self, nc, name,grid, data): return data


    # calculate dry cell flags, if any cell node is dry
    # not required but have defaults
    def read_bottom_cell_index_as_int32(self, nc, grid):
        # assume  not LSc grid, so bottom cel is zero
        grid['bottom_cell_index'] = np.full((grid['x'].shape[0],), 0, dtype=np.int32)
        return grid

    def read_open_boundary_data_as_boolean(self, grid):
        is_open_boundary_node = np.full((grid['x'].shape[0],), False)
        return is_open_boundary_node

    def read_file_var_as_4D_nodal_values(self, nc, grid, var_name, file_index=None): nopass()
    def read_field_var(self, nc, var_file_name, sel=None):
        # read sel time steps of field variable
        data = nc.read_a_variable(var_file_name, sel=sel)
        return data, nc.all_var_dims(var_file_name)

    # optional methods
    #-------------------------------------
    # checks on first hindcast file
    def additional_setup_and_hindcast_file_checks(self, nc,msg_logger): pass

    # -------------------------------------------------
    # core reader processes

    def initial_setup(self,file_info):
        # map variable internal names to names in NETCDF file
        # set update default value and vector variables map  based on given list
        ml = si.msg_logger
        info = self.info
        self.info['file_info'] = file_info  # add file_info to reader info

        # set up ring buffer  info
        bi = self.info['buffer_info']
        bi['n_filled'] = 0
        bi['buffer_size'] = self.params['time_buffer_size']
        bi['time_steps_in_buffer'] = []
        bi['buffer_available'] = bi['buffer_size']
        bi['nt_buffer0'] = 0



    def final_setup(self):      pass
    def set_up_grid(self, nc):
        grid={}
        is3D_hydro = self.is_hindcast3D(nc)
        grid = self.build_hori_grid(nc, grid)
        grid = self.construct_grid_variables(grid)

        pass
        if si.settings['display_grid_at_start']:
            from plot_oceantracker.plot_utilities import  display_grid
            display_grid(grid,1)

            pass


        if is3D_hydro:
            grid = self.build_vertical_grid(nc, grid)

        else:
            # 2D
            grid['zlevel'] = None
            grid['nz'] = 1  # only one z

        # check key data types, so that numba runs cleanly
        for name in ['x']:
            v= grid[name]
            if v.dtype != np.float64:
                si.msg_logger.msg(f'Reader type error {name} must be dtype {np.float64} ', warning=True)

        for name in ['zlevel', 'zlevel_fractions']:
            if name in grid: 
                v = grid[name]
                if v is not None and v.dtype != np.float32:
                    si.msg_logger.msg(f'Reader type error {name} must be dtype {np.float64} ', warning=True)
                
        for name in ['triangles','bottom_cell_index','quad_cells_to_split']:
            if name in grid :
                v= grid[name]
                if v.dtype != np.int32:
                    si.msg_logger.msg(f'Reader type error {name} must be dtype {np.int32} ', warning=True)

        return grid, is3D_hydro


    def sort_files_by_time(self, file_list, msg_logger):
        # get time sorted list of files matching mask
        fi = {'names': file_list, 'time_steps_per_file': [], 'file_start_times': [], 'file_end_times': []}
        for n, fn in enumerate(file_list):
            # get first/second/last time from each file,
            nc = self._open_file(fn)
            time = self.read_time_sec_since_1970(nc)
            nc.close()
            fi['file_start_times'].append(time[0])
            fi['file_end_times'].append(time[-1])  # -1 guards against there being only one time step in the file
            fi['time_steps_per_file'].append(time.shape[0])
            if n + 1 >= self.params['max_numb_files_to_load']: break

        # check some files found
        if len(fi['names']) == 0:
            msg_logger.msg('reader: cannot find any files matching mask "' + self.params['file_mask']
                           + '"  in input_dir : "' + self.params['input_dir'] + '"',
                   caller=self, fatal_error=True)

        # convert file info to numpy arrays for sorting
        keys = ['names', 'time_steps_per_file', 'file_start_times', 'file_end_times']
        for key in keys:
            fi[key] = np.asarray(fi[key])

        # sort files into order based on start time
        s = np.argsort(fi['file_start_times'])
        for key in fi.keys():
            if isinstance(fi[key], np.ndarray):
                fi[key] = fi[key][s]

        # tidy up file info
        fi['names'] = fi['names'].tolist()

        # get time step index at start and end on files
        cs = np.cumsum(fi['time_steps_per_file'])
        fi['nt_starts'] = cs - fi['time_steps_per_file']
        fi['time_steps_in_hindcast'] = np.sum(fi['time_steps_per_file'], axis=0)
        fi['nt_ends'] = fi['nt_starts'] + fi['time_steps_per_file'] - 1

        self.info['file_info'] = fi

        return fi

    def open_first_file(self):
        fi = self.info['file_info']
        nc = self._open_file(fi['names'][0])
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

        # checks on hindcast
        if fi['time_steps_in_hindcast'] < 2:
            msg_logger.msg('Hindcast must have at least two time steps, found ' + str(fi['time_steps_in_hindcast']),
                     fatal_error=True, exit_now=True, caller=self)


        t = np.stack((fi['file_start_times'], fi['file_end_times']), axis=1)
        fi['first_time'] = np.min(t[:,0])
        fi['last_time'] = np.max(t[:,1])
        fi['duration'] = abs(fi['last_time'] - fi['first_time'])
        fi['hydro_model_time_step'] = fi['duration'] / (fi['time_steps_in_hindcast']-1)

        # datetime versions for reference
        fi['file_start_dates'] = time_util.seconds_to_datetime64(fi['file_start_times'])
        fi['file_end_dates'] = time_util.seconds_to_datetime64(fi['file_end_times'])
        fi['first_date'] = time_util.seconds_to_datetime64(fi['first_time'])
        fi['last_date'] = time_util.seconds_to_datetime64(fi['last_time'])
        fi['hydro_model_timedelta'] = time_util.seconds_to_pretty_duration_string(fi['hydro_model_time_step'])

        # check for large time gaps between files
        # check if time diff between starts of file and end of last are larger than average time step
        if len(fi['file_start_times']) > 1:
            dt_gaps = fi['file_start_times'][1:] - fi['file_end_times'][:-1]
            sel = np.abs(dt_gaps) > 3. * fi['hydro_model_time_step']

            if np.any(sel):
                msg_logger.msg('Some time gaps between hydro-model files is are > 2.5 times average time step, check hindcast files are all present??', hint='check hindcast files are all present and times in files consistent', warning=True)
                for n in np.flatnonzero(sel):
                    msg_logger.msg(' large time gaps between file ' + fi['names'][n] + ' and ' + fi['names'][n + 1], tabs=1, warning=True,
                                   hint =f' first {1} ')

        msg_logger.exit_if_prior_errors('exiting from _get_hindcast_files_info, in setting up readers')
        return fi

    def build_hori_grid(self, nc, grid):
        # read nodal values and triangles
        params = self.params
        ml = si.msg_logger

        # read nodal x's

        grid = self.read_horizontal_grid_coords(nc, grid)
        grid = self.read_triangles_as_int32(nc, grid)

        # get dergees per m at mercator coords for triangle area calcs
        #dev code testing global lon_lat particle converting delta in m to degrees
        if  False and grid['hydro_model_cords_in_lat_long']:
            grid['deg_per_m'], grid['x_mercator'] = get_Metcator_info((grid['lon_lat']))

            # checks on area calac
            from oceantracker.util.triangle_utilities  import calcuate_triangle_areas
            a1= calcuate_triangle_areas(grid['x'], grid['triangles'])
            a2 = calcuate_triangle_areas(grid['x_mercator'], grid['triangles'])
            rm = a2 / a1

            xutm = si._transform_lon_lat_to_meters(grid['lon_lat'])
            a3= calcuate_triangle_areas(xutm, grid['triangles'])
            ru = a3 / a1
            pass




        return grid

    def construct_grid_variables(self, grid):
        # set up grid variables which don't vary in time and are shared by all case runners and main
        # add to reader build info
        info = self.info
        msg_logger = si.msg_logger
        msg_logger.progress_marker('Starting grid setup')

        # node to cell map
        t0 = perf_counter()
        grid['node_to_tri_map'], grid['tri_per_node'] = triangle_utilities.build_node_to_triangle_map(grid['triangles'], grid['x'])
        msg_logger.progress_marker('built node to triangles map', start_time=t0)

        # adjacency map
        t0 = perf_counter()
        grid['adjacency'] = triangle_utilities.build_adjacency_from_node_tri_map(grid['node_to_tri_map'], grid['tri_per_node'], grid['triangles'])
        msg_logger.progress_marker('built triangle adjacency matrix', start_time=t0)

        # boundary triangles
        t0 = perf_counter()
        grid['is_boundary_triangle'] = triangle_utilities.get_boundary_triangles(grid['adjacency'])
        msg_logger.progress_marker('found boundary triangles', start_time=t0)
        t0 = perf_counter()
        grid['grid_outline'] = triangle_utilities.build_grid_outlines(grid['triangles'], grid['adjacency'],
                                                                         grid['is_boundary_triangle'], grid['node_to_tri_map'], grid['x'])

        msg_logger.progress_marker('built domain and island outlines', start_time=t0)

        # make island and domain nodes, not in regular grid some nodes may be unsed so mark as land
        grid['node_type'] = np.full(grid['x'].shape[0],  node_types['land'],dtype=np.int8) # mark all as land

        # now mark all active nodes, those in a triangle,  as inside model
        grid['node_type'][np.unique(grid['triangles'])] = node_types['interior']

        # now mark boundary nodes
        for c in grid['grid_outline']['islands']:
            grid['node_type'][c['nodes']] = node_types['island_boundary']

        grid['node_type'][grid['grid_outline']['domain']['nodes']] = node_types['domain_boundary']

        t0 = perf_counter()
        grid['triangle_area'] = triangle_utilities.calcuate_triangle_areas(grid['x'], grid['triangles'])
        msg_logger.progress_marker('calculated triangle areas', start_time=t0)
        msg_logger.progress_marker('Finished grid setup')

        # adjust node type and adjacent for open boundaries
        # todo define node and adjacent type values in dict, for single definition and case info output?
        is_open_boundary_node = self.read_open_boundary_data_as_boolean(grid)
        grid['node_type'][is_open_boundary_node] = node_types['open_boundary']

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

        # make nodal version of water depth for faster interpolation in vertical cell search
        #grid['water_depth_at_nodes'] = np.full((grid['x'].shape[0],3), 0, dtype=np.float32)
        for n  in range(3):
            pass
        return grid

    def build_vertical_grid(self, nc, grid):
        # setup transforms on the data, eg regrid vertical if 3D to same sigma levels
        params = self.params
        info = self.info

        grid = self.read_bottom_cell_index_as_int32(nc, grid)

        # set up zlevel
        if si.settings['regrid_z_to_uniform_sigma_levels']:
            # setup  regrid grid equal time invariace sigma layers
            # based on profile with thiniest top nad bootm layers
            grid= self._make_sigma_depth_cell_search_map(nc, grid)
            grid['nz'] = grid['sigma'].size
        else:
            # native  vertical grid option, could be  Schisim LCS vertical grid

            grid['nz'] = self.number_hindcast_zlayers(nc)  # used to size field data arrays
            s = [self.params['time_buffer_size'], grid['x'].shape[0], grid['nz']]
            grid['zlevel'] = np.zeros(s, dtype=np.float32, order='c')

        return grid

    def _make_sigma_depth_cell_search_map(self,nc, grid):
        grid = self.set_up_uniform_sigma(nc, grid)

        # build lookup map
        # setup lookup nz interval map of zfraction into with equal dz for finding vertical cell
        # the smalest sigms later thickness is at the bottom
        dz = 0.66 * abs(np.diff(grid['sigma'][:2]))  # smlated dz
        nz_map = int(np.ceil(1.0 / dz))  # number of cells in map
        grid['sigma_map_z'] = np.arange(nz_map) / (nz_map - 1)  # zlevels at the map intervals
        grid['sigma_map_dz'] = np.diff(grid['sigma_map_z']).mean()  # exact dz

        # make evenly spaced map which gives cells contating a sigma level
        grid['sigma_map_nz_interval_with_sigma'] = np.zeros((nz_map,), dtype=np.int32)
        interval_with_sigma_level = (grid['sigma'] * nz_map).astype(np.int32)

        # omit sigma = 0 and 1 from intervals, to ensurethey fall in first and last intervals
        grid['sigma_map_nz_interval_with_sigma'][interval_with_sigma_level[1:-1]] = 1
        grid['sigma_map_nz_interval_with_sigma'] = grid['sigma_map_nz_interval_with_sigma'].cumsum()
        return grid

    #@function_profiler(__name__)
    def fill_time_buffer(self,fields, grid, time_sec):
        # fill as much of  hindcast buffer as possible starting at global hindcast time step nt0_buffer
        # fill buffer starting at hindcast time step nt0_buffer
        # todo change so does not read current step again after first fill of buffer

        params = self.params
        md = si.run_info.model_direction
        t0 = perf_counter()

        info = self.info
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
        n_file = np.argmax(np.logical_and(nt0_hindcast >= fi['nt_starts'] * md, nt0_hindcast <= fi['nt_ends']))

        # get required time step and trim to size of hindcast
        nt_hindcast_required = nt0_hindcast + md * np.arange(min(fi['time_steps_in_hindcast'], buffer_size))
        sel = np.logical_and(0 <= nt_hindcast_required, nt_hindcast_required < fi['time_steps_in_hindcast'])
        nt_hindcast_required = nt_hindcast_required[sel]

        bi['time_steps_in_buffer'] = []

        while len(nt_hindcast_required) > 0 and 0 <= n_file < len(fi['names']):

            nc = self._open_file(fi['names'][n_file])

            # find time steps in current file,accounting for direction
            sel = np.logical_and(nt_hindcast_required >= fi['nt_starts'][n_file],
                                 nt_hindcast_required <= fi['nt_ends'][n_file])
            num_read = np.count_nonzero(sel)
            nt_file = nt_hindcast_required[sel]  # hindcast steps in this file

            file_index = nt_file - fi['nt_starts'][n_file]
            buffer_index = self.hydro_model_index_to_buffer_offset(nt_file)
            s = f'Reading-file-{(n_file):02d}  {path.basename(fi["names"][n_file])}, steps in file {fi["time_steps_per_file"][n_file]:3d},'
            s += f' steps  available {fi["nt_starts"][n_file]:03d}:{fi["nt_starts"][n_file] + fi["time_steps_per_file"][n_file] - 1:03d}, '
            s += f'reading  {num_read:2d} of {bi["buffer_available"]:2d} steps, '
            s += f' for hydo-model time steps {nt_file[0]:02d}:{nt_file[-1]:02d}, '
            s += f' from file offsets {file_index[0]:02d}:{file_index[-1]:02d}, '
            s += f' into ring buffer offsets {buffer_index[0]:03}:{buffer_index[-1]:03d} '
            si.msg_logger.progress_marker(s)

            grid['nt_hindcast'][buffer_index] = nt_hindcast_required[:num_read]  # add a grid variable with global hindcast time steps


            # read grid time, zlevel
            # do this after reading fields as some hindcasts required tide field to get zlevel, eg FVCOM
            self.read_time_variable_grid_variables(nc,grid,fields, buffer_index, file_index)

            # read time varying vector and scalar reader fields
            # do this in order set above
            for name, field in fields.items():

                if not field.is_time_varying() or field.info['type'] != 'reader_field': continue

                data = self.assemble_field_components(nc, grid, name, field, file_index=file_index)

                junk = data
                if field.is3D() and si.settings['regrid_z_to_uniform_sigma_levels']:
                    s = list(np.asarray(data.shape, dtype=np.int32))
                    s[2] = grid['sigma'].size
                    out = np.full(tuple(s), np.nan, dtype=np.float32)
                    data = hydromodel_grid_transforms.interp_4D_field_to_fixed_sigma_values(
                                        grid['zlevel_fractions'], grid['bottom_cell_index'],
                                        grid['sigma'],
                                        fields['water_depth'].data, fields['tide'].data,
                                        si.settings.z0, si.settings.minimum_total_water_depth,
                                        data, out,
                                        name == 'water_velocity')

                # read dry cels which may need tide and water depth
                self.read_dry_cell_data(nc, grid, fields, file_index, grid['is_dry_cell'], buffer_index)

                # o = reader_util.get_values_at_bottom(junk, grid['bottom_cell_index'])
                # pass

                # insert data
                field.data[buffer_index, ...] = data

                if si.settings['dev_debug_plots']:
                    # check overplots of regridding
                    from matplotlib import pyplot as plt
                    nn = 300  # for test hindcats
                    nn = 1000
                    plt.plot(grid['zlevel_fractions'][nn, :], junk[0, nn, :, 0], c='g')
                    plt.plot(grid['zlevel_fractions'][nn, :], junk[0, nn, :, 0], 'g.')
                    plt.plot(grid['sigma'], data[0, nn, :, 0], 'r--')
                    plt.plot(grid['sigma'], data[0, nn, :, 0], 'rx')
                    # plt.show(block= True)
                    plt.savefig('\myfig.png')

            nc.close()

            # now all  data has been read from file, now
            # update user fields from newly read fields and data
            for name, field in fields.items():
                if field.is_time_varying() and field.info['type'] == 'custom_field':
                    field.update(fields,grid,buffer_index)

            total_read += num_read

            # set up for next step

            bi['buffer_available'] -= num_read
            n_file += md
            nt_hindcast_required = nt_hindcast_required[num_read:]
            bi['time_steps_in_buffer'] += nt_file.tolist()

        si.msg_logger.progress_marker(f' read {total_read:3d} time steps in  {perf_counter() - t0:3.1f} sec', tabs=2)
        # record useful info/diagnostics
        bi['n_filled'] = total_read

    def assemble_field_components(self, nc, grid, name, field, file_index=None):
        # read scalar fields / join together the components which make vector from component list

        params = self.params

        s = list(field.data.shape)
        s[0] = 1 if file_index is None else file_index.size
        out = np.zeros(s, dtype=np.float32)  # todo faster make a generic  buffer at start

        m = 0  # num of vector components read so far

        var_names = params['field_variable_map'][name] if type(params['field_variable_map'][name]) == list else [params['field_variable_map'][name]]

        for var_name in var_names:
            if var_name is None: continue
            data = self.read_file_var_as_4D_nodal_values(nc, grid, var_name, file_index)
            comp_per_var = data.shape[3]
            m1 = m + comp_per_var
            # get view of where in buffer data is to be placed
            out[:, :, :, m:m1] = data
            m += comp_per_var

        # any tweaks required before use
        out =  self.preprocess_field_variable(nc, name, grid, out)


        return out

    def read_time_variable_grid_variables(self, nc,grid, fields, buffer_index, file_index):
        # read time and  grid variables, eg time,dry cell
        grid['time'][buffer_index] = self.read_time_sec_since_1970(nc, file_index=file_index)

        # add date for convenience
        grid['date'][buffer_index] = time_util.seconds_to_datetime64(grid['time'][buffer_index])


        if si.run_info.is3D_run:
            # read zlevel inplace to save memory?
            if 'sigma' not in grid:
                # native zlevel grid and used for regidding in sigma
                self.read_zlevel_as_float32(nc,grid,fields, file_index, grid['zlevel'], buffer_index)



    # convert, time etc to hindcast/ buffer index
    def time_to_hydro_model_index(self, time_sec):
        # convert date time to global time step in hindcast just before/after when forward/backtracking
        # always move forward through buffer, but file info is always forward in time
        fi = self.info['file_info']
        model_dir = si.run_info.model_direction

        hindcast_fraction = (time_sec - fi['first_time']) / (fi['last_time'] - fi['first_time'])
        nt = (fi['time_steps_in_hindcast'] - 1) * hindcast_fraction

        # if back tracking ronud up as moving backwards through buffer, forward round down
        return np.int32(np.floor(nt * model_dir) * model_dir)

    def hydro_model_index_to_buffer_offset(self, nt_hindcast):
        # ring buffer mapping
        return nt_hindcast % self.info['buffer_info']['buffer_size']


    def are_time_steps_in_buffer(self, time_sec):
        # check if next two steps of remaining  hindcast time steps required to run  are in the buffer
        bi = self.info['buffer_info']
        model_dir = si.run_info.model_direction

        # get hindcast time step at current time
        nt_hindcast = self.time_to_hydro_model_index(time_sec)

        return nt_hindcast in bi['time_steps_in_buffer'] and nt_hindcast + model_dir in bi['time_steps_in_buffer']



    def detect_lonlat_grid(self, xgrid):
        # look at range to see if too small to be meters grid
        islatlong=  (np.nanmax(xgrid[:,0])- np.nanmin(xgrid[:,0]) < 360) or (np.nanmax(xgrid[:,0])- np.nanmin(xgrid[:,0]) < 360)

        if islatlong:
            si.msg_logger.msg('Reader auto-detected lon-lat grid, as grid span  < 360, so not a meters grid ', warning=True)
        return islatlong

    def _open_file(self,file_name):
        # open net cdf file for readin
        return NetCDFhandler(file_name, 'r')

    def close(self):
        pass
