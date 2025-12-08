import numpy as np
from copy import deepcopy
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParameterListChecker as PLC
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterTimeChecker as PTC
from oceantracker.fields.reader_field import  ReaderField
from oceantracker.util import time_util, ncdf_util, numba_util
from datetime import datetime
from os import path
from time import perf_counter
from oceantracker.util.basic_util import nopass
import oceantracker.reader.util.hydromodel_grid_transforms as hydromodel_grid_transforms
from oceantracker.util.triangle_utilities import split_quad_cells
from oceantracker.util.cord_transforms import fix_any_spanning180east
from oceantracker.util import triangle_utilities, basic_util, cord_transforms


from oceantracker.reader.util import reader_util

from oceantracker.shared_info import shared_info as si

class _BaseReader(ParameterBaseClass):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params(
            input_dir= PVC(None, str, is_required=True),
            file_mask= PVC(None, str, is_required=True, doc_str='Mask for file names, eg "scout*.nc", finds all files matching in  "input_dir" and its sub dirs that match the file_mask pattern'),
            geographic_coords= PVC(False, bool, doc_str='Read file coords as geographic values,normaly auto-detects if in geographic coords, using this setting  forces reading as geograraphic coord if auto-dectect fails',
                                     expert=True),
            time_buffer_size= PVC(24, int, min=2, doc_str='This reader parameter has be removed,  now a top level setting , use  setting "time_buffer_size"', obsolete=True),
            load_fields= PLC(None, str,
                               doc_str=' A list of names of any additional variables to read and interplolate to give particle values, eg. a concentration field (water_veloctiy, tide and water_depth fields are always loaded). If a given name is in field_variable_map, then the mapped file variables will be used internally and in output. If not the given file variable name will be used internally and in particle property output. For any additional vector fields user must supply a file variable map in the "field_variable_map" parameter',
                               make_list_unique=True),
            one_based_indices= PVC(False, bool, doc_str='File has indices starting at 1, not pythons zero, eg node numbers in triangulation/simplex'),
            EPSG_code= PVC(None, int, doc_str='integer code for coordinate transform of hydro-model, only used if setting "use_geographic_coords"= True and hindcast not in geographic coords, EPSG for New Zealand Transverse Mercator 2000 = 2193, find codes at https://spatialreference.org/'),
            max_numb_files_to_load= PVC(10 ** 7, int, min=1,
                                        doc_str='Only read no more than this number of hindcast files, useful when setting up to speed run'),
            variable_signature = PLC(None, str, doc_str='Variable names used to test if file is this format', is_required=True),
            grid_variable_map= dict(
                            time=PVC('time', str, doc_str='Name of time variable in hindcast',is_required=True),
                            x=PVC(None, str, doc_str='x location of nodes', is_required=True),
                            y=PVC(None, str, doc_str='y location of nodes', is_required=True),
                            ),
            field_variable_map= dict(
                            water_depth=PVC(None, str, doc_str='maps standard internal field name to file variable name',
                                ),
                water_velocity=PLC(['not_given'], str, doc_str='maps standard internal field name to file variable name'),
                water_velocity_depth_averaged=PLC(['not_given'], str, doc_str='maps standard internal field name to file variable name'),
                            ),
            dimension_map= dict(
                            vector2D=PVC(None, str, doc_str='name of dimension names for 2D vectors'),
                            vector3D=PVC(None, str, doc_str='name of dimension names for 3D vectors'),
                            z=PVC( None, str, doc_str='name of dimensions for z layer boundaries '),
                            all_z_dims=PLC(None, str, doc_str='All z dims, used to identify  3D variables', is_required=True),
                            ),
        field_variables= PLC(None, str, obsolete=True, doc_str=' parameter obsolete, use "load_fields" parameter, with field_variable_map if needed', make_list_unique=True),
        drop_variables= PLC(None, str, expert=True, doc_str='List of problematic file variable names to ignore, eg non-critcal variables not present in all files/all times', make_list_unique=True),
        regrid_z_to_sigma_levels = PVC(True, bool,
                doc_str='much faster 3D runs by re-griding hydo-model fields for S-layer or LSC vertical grids (eg. SCHISM),  into uniform sigma levels on read based on sigma most curve z_interface profile. Some hydo-model are already uniform sigma, so this param is ignored, eg ROMS')

        )  # list of normal required dimensions

        self.info['buffer_info'] = dict( time_steps_in_buffer = [])
        self.info["vert_grid_type"] = None
        self.grid={}
        self.fields ={}

        self.si = si


    # Below are required  methods for any new reader
    # ---------------------------------------------------------


    def add_hindcast_info(self): nopass()
    # get is 3D, vertical grid type and

    def read_horizontal_grid_coords(self, grid):   nopass()

    def read_triangles(self, grid):     nopass('need a read_triangle methods for both structured (which makes trianglation from mesh) and unstructured grids')

    def read_z_interface(self, nt):   pass

    def read_dry_cell_data(self, nt_index, buffer_index):
        # read dry cell as =1 wet = 0
        nopass()

    def set_up_uniform_sigma(self,grid): pass

    def preprocess_field_variable(self, name,grid, data): return data

    def read_bottom_interface_index(self, grid):
        # dummy bottom cell
        bottom_interface_index = np.zeros((self.info['num_nodes'],), dtype=np.int32)
        return bottom_interface_index

    def read_open_boundary_data_as_boolean(self, grid):
        is_open_boundary_node = np.full((grid['x'].shape[0],), False)
        return is_open_boundary_node

    def read_file_var_as_4D_nodal_values(self, var_name, var_info, nt=None): nopass()


    # optional methods
    #-------------------------------------
    # checks on first hindcast file
    def additional_setup_and_hindcast_file_checks(self, nc,msg_logger): pass

    # -------------------------------------------------
    # core reader processes

    def initial_setup(self):
        # build data set from reader builder catalog

        # map variable internal names to names in NETCDF file
        # set update default value and vector variables map  based on given list
        # first build data set

        self._build_hori_and_vert_grids()

        pass


    def build_fields(self):
        info = self.info
        # make grid


        self._set_up_interpolator()
        self._setup_fields()

        # set up ring buffer  info
        bi = self.info['buffer_info']
        bi['n_filled'] = 0
        bi['time_buffer_size'] = si.settings.time_buffer_size
        bi['buffer_available'] = si.settings.time_buffer_size
        bi['nt_buffer0'] = 0


    def final_setup(self):      pass

    def _build_hori_and_vert_grids(self, ):
        params = self.params
        grid= self.grid
        info = self.info
        self.build_hori_grid(grid)
        self._construct_hori_grid_variables()
        si.msg_logger.hori_line('Hindcast info')
        si.msg_logger.msg(f'Hydro-model is "{"3D" if info["is3D"] else "2D"}", type "{self.__class__.__name__}"',
                          tabs=2, hint=f'Files found in dir and sub-dirs of "{self.params["input_dir"]}"')
        si.msg_logger.msg(f'Geographic coords = "{info["geographic_coords"]}" ', tabs=4)
        si.msg_logger.msg(f'Hindcast start: {info["start_date"]}  end:  {info["end_date"]}', tabs=4)
        dt = time_util.seconds_to_pretty_duration_string(info['time_step'])
        si.msg_logger.msg(f'time step = {dt}, number of time steps= {info["total_time_steps"]} ',
                          tabs=5)
        si.msg_logger.msg('grid bounding box = ' + info['bounding_box'], tabs=5)

        si.msg_logger.msg(
            f"has:  A_Z profile={info['has_A_Z_profile']},  bottom stress={info['has_bottom_stress']}, regrid to sigma={params['regrid_z_to_sigma_levels']} ",
            tabs=5)


        if self.info['is3D']:
            self.build_vertical_grid()
        else:
            # 2D
            grid['z_interface'] = None

        si.msg_logger.msg(f'vertical grid type = "{info["vert_grid_type_in_files"]}", using vertical grid  "{info["vert_grid_type"]}"', tabs=5)
        si.msg_logger.hori_line()

        #todo is below cneeded???
        for name in ['z_interface', 'z_interface_fractions']:
            if name in grid:
                v = grid[name]
                if v is not None and v.dtype != np.float32:
                    si.msg_logger.msg(f'Reader type error {name} must be dtype {np.float64} ', warning=True)

        pass



    def build_hori_grid(self, grid):
        # read nodal values and triangles
        params = self.params
        info = self.info

        self.read_horizontal_grid_coords(grid) # read nodal x's

        if si.settings.use_geographic_coords or info['geographic_coords']:
            if not info['geographic_coords']:
                # if not already in geographic
                if params['EPSG_code'] is None:
                    si.msg_logger.msg(
                        'When using geographic coords and hydromodel not already in geographic coords, Reader must have "EPSG_code" parameter set to do conversion',
                        hint='EPSG for New Zealand Transverse Mercator 2000 = 2193, find codes for hydro model at at https://spatialreference.org/',
                        caller=self, fatal_error=True)
                # do conversion
                grid['x'] = cord_transforms.convert_cords(grid['x'], params['EPSG_code'], cord_transforms.EPSG_WGS84)

            # fix any spanning 179 to -179
            fix_any_spanning180east(grid['x'], msg_logger=si.msg_logger, caller=self,
                                                crumbs=f'setting up reader in dir=  {self.params["input_dir"]}')
            # set up conversion of meters to degreees
            i = self._add_a_reader_field('degrees_per_meter', dict(time_varying=False, is3D=False, is_vector=True,
                              write_interp_particle_prop_to_tracks_file=False),  dummy=True)
            i.data[0, :, 0, :] = cord_transforms.get_degrees_per_meter(grid['x'][:,1],as_vector=True)
            si.msg_logger.msg('Converted hindcast to geographic coords',note=True)
            pass

        # get bounding box
        bounds =np.asarray( [grid['x'].min(axis=0), grid['x'].max(axis=0)])
        b = f'{np.array2string(bounds[0], precision=3, floatmode="fixed")} to {np.array2string(bounds[1], precision=3, floatmode="fixed")}'

        info['bounding_box'] = b

        # reader triangles
        self.read_triangles(grid)
        grid['quad_cells_to_split'],grid['triangles'] = self.find_and_split_quad_cells(grid['triangles'])

        # find nodes that are used in triangulation (ie not land)
        grid['active_nodes'] = np.unique(grid['triangles'])

        # ensure variables have right type
        grid['x'] = grid['x'].astype(np.float64)

    def _construct_hori_grid_variables(self):
        # set up grid variables which don't vary in time and are shared by all case runners and main
        # add to reader build info
        info = self.info
        grid = self.grid

        msg_logger = si.msg_logger
        msg_logger.progress_marker('Starting grid setup',tabs=0)

        # node to cell map
        t0 = perf_counter()
        grid['node_to_tri_map'], grid['tri_per_node'] = triangle_utilities.build_node_to_triangle_map(grid['triangles'], grid['x'])
        msg_logger.progress_marker('built node to triangles map', start_time=t0,tabs=1)

        # adjacency map
        t0 = perf_counter()
        grid['adjacency'] = triangle_utilities.build_adjacency_from_node_tri_map(grid['node_to_tri_map'], grid['tri_per_node'], grid['triangles'])
        msg_logger.progress_marker('built triangle adjacency matrix', start_time=t0,tabs=1)

        # boundary triangles
        t0 = perf_counter()
        grid['is_boundary_triangle'] = triangle_utilities.get_boundary_triangles(grid['adjacency'])
        msg_logger.progress_marker('found boundary triangles', start_time=t0,tabs=1)
        t0 = perf_counter()
        grid['grid_outline'] = triangle_utilities.build_grid_outlines(grid['triangles'], grid['adjacency'],
                                            grid['is_boundary_triangle'], grid['node_to_tri_map'], grid['x'])

        msg_logger.progress_marker('built domain and island outlines', start_time=t0,tabs=1)

        # make island and domain nodes, not in regular grid some nodes may be unsed so mark as land
        grid['node_type'] = np.full(grid['x'].shape[0],  si.node_types.land,dtype=np.int8) # mark all as land

        # now mark all active nodes, those in a triangle,  as inside model
        grid['node_type'][np.unique(grid['triangles'])] = si.node_types.interior

        # now mark boundary nodes
        for c in grid['grid_outline']['islands']:
            grid['node_type'][c['nodes']] = si.node_types.island_boundary

        grid['node_type'][grid['grid_outline']['domain']['nodes']] = si.node_types.domain_boundary

        t0 = perf_counter()
        grid['triangle_area'] = triangle_utilities.calcuate_triangle_areas(grid['x'], grid['triangles'],info['geographic_coords'])
        msg_logger.progress_marker('calculated triangle areas', start_time=t0,tabs=1)


        # adjust node type and adjacent for open boundaries
        # todo define node and adjacent type values in dict, for single definition and case info output?
        is_open_boundary_node = self.read_open_boundary_data_as_boolean(grid)
        grid['node_type'][is_open_boundary_node] = si.node_types.open_boundary
        info['has_open_boundary'] = np.any(is_open_boundary_node)

        is_open_boundary_adjacent = reader_util.find_open_boundary_faces(grid['triangles'], grid['is_boundary_triangle'], grid['adjacency'], is_open_boundary_node)

        grid['adjacency'][is_open_boundary_adjacent] = si.edge_types.open_boundary

        grid['limits'] = np.asarray([np.min(grid['x'][:, 0]), np.max(grid['x'][:, 0]), np.min(grid['x'][:, 1]), np.max(grid['x'][:, 1])])

        # now set up time buffers
        time_buffer_size = si.settings.time_buffer_size

        grid['nt_hindcast'] = np.full((time_buffer_size,), -10, dtype=np.int32)  # what global hindcast timestesps are in the buffer

        # space for dry cell info
        grid['is_dry_cell_buffer'] = np.full((time_buffer_size, grid['triangles'].shape[0]), 1, np.int8)

        # reader working space for 0-255 index of how dry each cell is currently, used in stranding, dry cell blocking, and plots
        grid['dry_cell_index'] = np.full((grid['triangles'].shape[0],), 0, np.uint8)

        # make nodal version of water depth for faster interpolation in vertical cell search
        #grid['water_depth_at_nodes'] = np.full((grid['x'].shape[0],3), 0, dtype=np.float32)
        #for n  in range(3):
        #    pass
        msg_logger.progress_marker('Finished grid setup', tabs=0)

    def build_vertical_grid(self):
        # setup transforms on the data, eg regrid vertical if 3D to same sigma levels
        params = self.params
        info = self.info
        grid = self.grid
        vgt = si.vertical_grid_types
        grid['bottom_interface_index'] = self.read_bottom_interface_index(grid).astype(np.int32)

        # allow vertical regridding to same sigma at all nodes

        if params['regrid_z_to_sigma_levels']:
            self.set_up_uniform_sigma(grid)  # add an estimated sigma to the grid


        # set up z_interfaces if needed
        info['read_zlevels'] = False
        if info['vert_grid_type'] in [vgt.LSC, vgt.Slayer]:
            # native  vertical grid option, could be  Schisim LCS vertical grid
            # used to size field data arrays
            s = [si.settings.time_buffer_size, grid['x'].shape[0], info['num_z_interfaces']]
            grid['z_interface'] = np.zeros(s, dtype=np.float32, order='c')
            info['read_zlevels'] = True

    def find_and_split_quad_cells(self, tri):
        # return indices of quad cells to split from 4th column on triangulation
        # # based on <0 missing values in 4th column
        #  adds new triangle to triangulation as needed
        quad_cells_to_split = np.full((0,), 0, dtype=np.int32)

        if tri.shape[1] == 4:
            # split quad grids by making new triangles from those where 4th column is >=0
            quad_cells_to_split = np.flatnonzero(tri[:, 3] >= 0).astype(np.int32)
            tri = split_quad_cells(tri, quad_cells_to_split) # add new triangles to triangulation

        return quad_cells_to_split, tri

    def _setup_fields(self):
        # setup field classes , ie make memory buffer
        info = self.info
        params = self.params
        fields = self.fields

        # add essential fields- water depth, tide, water velocity
        self.setup_water_depth_field()
        # add view of water depth to the grid
        self.grid['water_depth'] = fields['water_depth'].data.squeeze()

        self.setup_tide_field()
        self.setup_water_velocity_field()

        # first reader fields
        load_fields= params['load_fields']

        # add reader fields
        all_fields= list(set(load_fields))
        for name  in all_fields:
            # core fields done separately by custom methods
            if name in ['water_depth', 'tide','water_velocity']: continue

            i = self._add_a_reader_field(name)

            # read reader field now if not time varying
            if not i.is_time_varying():
                    i.data = self.read_field_data(name, i)

        si.msg_logger.progress_marker(f'Loading reader fields {str(all_fields)}')

    def _add_a_reader_field(self, name, params={},dummy=False):
        info = self.info

        params = deepcopy(params)
        params['name'] = name
        if not dummy:
            params.update(info['field_info'][name][ 'params'])

        i = si.class_importer.make_class_instance_from_params('fields', params,
                                       add_required_classes_and_settings=False,
                                        default_classID='field_reader',initialize=False,
                                        check_for_unknown_keys=False, crumbs=f'Adding reader field "{name}"')
        i.initial_setup(info)

        # add variable info on file variables list for reader fields
        if name in info['field_info']:
            i.info.update(file_vars_info=info['field_info'][name]['file_vars_info'] )

        self.fields[name] = i
        return i


    def _set_up_interpolator(self):

        if si.working_params['core_class_roles']['interpolator'] is None: si.working_params['core_class_roles']['interpolator'] = {}
        i = si.class_importer.make_class_instance_from_params('interpolator', si.working_params['core_class_roles']['interpolator'],
                                             default_classID='interpolator', caller= self,
                                             crumbs=f'field Group Manager>setup_hydro_fields> interpolator class  ')
        i.initial_setup(self)
        self.interpolator = i

    # setup and read core fields, depth, tide, water velocity
    # ----------------------------------------------------
    def setup_water_depth_field(self):
        i = self._add_a_reader_field('water_depth')
        i.data = self.read_field_data('water_depth', i) # read time in varient field

    def setup_tide_field(self):
        i = self._add_a_reader_field('tide')
        return i
    def update_tide_field(self, buffer_index, nt):
        field = self.fields['tide']
        data =  self.read_field_data('tide',field , nt)
        field.data[buffer_index, ...] = data
        return data

    def setup_water_velocity_field(self):
        info = self.info
        fi = info['field_info']
        #todo move check on whether vertical vel is in files here

        i = self._add_a_reader_field('water_velocity')

        return i

    def update_water_velocity_field(self, buffer_index, nt):
        field = self.fields['water_velocity']
        data = self.read_field_data('water_velocity', field, nt)
        params = self.params
        info = self.info

        if field.is3D():
            if params['regrid_z_to_sigma_levels']:
                # applies to LSC and Slayer grids if requested (the default)
                reader_util.ensure_velocity_at_bottom_is_zero_ragged_bottom(data, self.grid['bottom_interface_index']) # zero bottom before regrid
                data = self._vertical_regrid_Slayer_or_LSC_grid_to_uniform_sigma('water_velocity', data)

            # ensure vel at bottom is zero
            if info['vert_grid_type'] in [si.vertical_grid_types.LSC, si.vertical_grid_types.Zfixed]:
                # ragged bottom
                reader_util.ensure_velocity_at_bottom_is_zero_ragged_bottom(data, self.grid['bottom_interface_index'])
            else:
                # First  cell is at the bottom for sigma and Slayer, so set zero
                data[:, :, 0, :] = 0.

        field.data[buffer_index, ...] = data

        return data

    #------------------------------------------------------------------------------------------------
    def _time_step_and_buffer_offsets(self, time_sec):

        grid = self.grid
        info = self.info
        bi = self.info['buffer_info']

        # find time first step in numerical step within hindcast
        # version 3)  faster numpy binary search, clipped to be inside if in the last time step
        current_hydro_model_step = min(int(np.searchsorted(info['time_coord'], time_sec, side='left')), info['time_coord'].size-2)

        if si.settings.backtracking and time_sec > self.get_time(current_hydro_model_step):
            # round up  to the next time step if backtracking
            current_hydro_model_step += 1 # need next one if working backwards

        # get time at first time step
        time_hindcast = self.get_time(current_hydro_model_step)

        # ring buffer locations of surrounding steps, above if forward, below if backwards
        current_buffer_steps = np.zeros((2,), dtype=np.int32)
        current_buffer_steps[0] = current_hydro_model_step % si.settings.time_buffer_size
        current_buffer_steps[1] = (current_hydro_model_step + int(si.run_info.model_direction)) % si.settings.time_buffer_size

        # sets the fraction of time step that current time is between
        # surrounding hindcast time steps
        # abs makes it work when backtracking
        s = abs(time_sec - time_hindcast) / info['time_step']
        fractional_time_steps =  np.asarray([1.0 - s, s])

        if np.any(np.abs(fractional_time_steps) > 1.1):
            si.msg_logger.msg(f'unexpected error in times, fractional time steps is greater than 1 = {str(fractional_time_steps)}',
                              hint='Error in  decoding hindcast time? hindcast files not properly sorted in time order? or code bug?',
                              warning=True, caller = self)

        return current_hydro_model_step, current_buffer_steps, fractional_time_steps

    def update(self, time_sec):
        # check if all interpolators have the time steps they need

        if not self.are_time_steps_in_buffer(time_sec):

            self.start_update_timer()
            self.fill_time_buffer(time_sec)  # get next steps into buffer if not in buffer

            self.stop_update_timer()

    def fill_time_buffer(self,time_sec):
        # fill as much of  hindcast buffer as possible starting at global hindcast time step nt0_buffer
        # fill buffer starting at hindcast time step nt0_buffer
        # todo change so does not read current step again after first fill of buffer

        params = self.params
        md = si.run_info.model_direction
        t0 = perf_counter()

        info = self.info
        bi = info['buffer_info']
        buffer_size = si.settings.time_buffer_size

        bi['buffer_available'] = buffer_size
        nt0_hindcast = self.time_to_hydro_model_index(time_sec)
        bi['nt_buffer0'] = nt0_hindcast  # nw start of buffer

        # get hindcast global time indices of first block, loads in model order
        # ie if backtracking are still moving forward in buffer

        # get required time step and trim to size of hindcast
        nt_available = nt0_hindcast + md * np.arange(buffer_size)
        nt_available = self.dataset.time_steps_available(nt_available) # trim to fit hindcast

        buffer_index = self.hydro_model_index_to_buffer_index(nt_available)
        s = f' Reading {buffer_index.size:2d} time steps, '
        s += f' for hindcast time steps {nt_available[0]:02d}:{nt_available[-1]:02d}'
        s += f' into ring buffer offsets {buffer_index[0]:03}:{buffer_index[-1]:03d} '
        s+=  f',  for run "{si.run_info.output_file_base}"'
        si.msg_logger.progress_marker(s)

        # read grid time, zlevel
        # do this after reading fields as some hindcasts required tide field to get zlevel, eg FVCOM
        self.update_tide_field(buffer_index, nt_available)
        self.read_time_varying_grid_variables(nt_available, buffer_index)

        # read fields - tide
        self.update_water_velocity_field(buffer_index, nt_available)

        # read time varying vector and scalar reader fields
        for name, field in self.fields.items():
            if not isinstance(field, ReaderField) or not field.is_time_varying() : continue
            if name in ['tide','water_velocity']: continue

            data =  self.read_field_data(name, field, nt_available)

            if field.is3D() and params['regrid_z_to_sigma_levels']:
                data = self._vertical_regrid_Slayer_or_LSC_grid_to_uniform_sigma(name, data)

            # insert data
            field.data[buffer_index, ...] = data

        # read dry cels which may need tide and water depth fields
        self.read_dry_cell_data(nt_available, buffer_index)

        # now all  data has been read from file, now
        # update custom fields from newly read fields and data
        for name, field in self.fields.items():
            if field.is_time_varying() and not isinstance(field, ReaderField):
                field.update(self.fields,self.grid, buffer_index)

        # set up for next step
        bi['time_steps_in_buffer'] = nt_available.tolist()
        num_read = nt_available.size
        bi['buffer_available'] -= num_read
        si.msg_logger.progress_marker(f' read {num_read:3d} time steps in  {perf_counter() - t0:3.1f} sec, from {info["input_dir"]} ', tabs=2)


    def read_field_data(self, name, field, nt_index=None):
        data = self._assemble_field_components(field, nt_index)
        data = self.preprocess_field_variable(name, self.grid, data)  # any tweaks required before use
        return data

    def _assemble_field_components(self, field, nt_index):
        # read scalar fields / join together the components which make vector from component list

        s = list(field.data.shape)
        s[0] = 1 if nt_index is None else nt_index.size
        out = np.zeros(s, dtype=np.float32)  # todo faster make a generic  buffer at start

        m = 0  # num of vector components read so far
        for var_name, var_info in field.info['file_vars_info'].items() :
            if var_name is None: continue
            data = self.read_file_var_as_4D_nodal_values(var_name, var_info,  nt=nt_index)
            m1 = m + var_info['vector_components_per_file_var']
            # get view of where in buffer data is to be placed
            out[:, :, :, m:m1] = data
            m += var_info['vector_components_per_file_var']
        return out

    def read_time_varying_grid_variables(self, nt, buffer_index):
        # read time and  grid variables, eg time,dry cell
        grid = self.grid

        if si.run_info.is3D_run and self.info['read_zlevels']:
            # read zlevel if native vertical grid of types Slayer or LSC
            grid['z_interface'][buffer_index,...] =  self.read_z_interface(nt)


    def decode_time(self,time):
        # decode time as numpy array in seconds since 1970, input must be xarray variable
        # defaults assumes time has units for cf complinance

        units = time.attrs['units']

        unit, date = units.split('since')
        unit= unit.strip()

        date = date.split('+')[0] # remove "+" time zone data
        date = date.strip()
        d0 = np.datetime64(date).astype('datetime64[s]').astype(np.float64) # seconds since 1970

        t = time.data
        if unit == 'seconds':
            t = t.astype(np.float64)
        elif  unit == 'minutes':
            t = t.astype(np.float64)*60.
        elif  unit == 'hours':
            t = t.astype(np.float64)*3600.
        elif unit == 'days':
            t = t.astype(np.float64) * 3600.*24.
        else:
            si.msg_logger(f'Unrecognised time unit = {unit}', hint="must be one of [seconds,minutes,hours,days]")

        t = t + d0
        return t

    def get_time(self, nt_hindcast):
        # get preloaded times at given time steps
        return  self.info['time_coord'][nt_hindcast]

    def _vertical_regrid_Slayer_or_LSC_grid_to_uniform_sigma(self, name, data):
        grid = self.grid
        fields = self.fields

        s = list(np.asarray(data.shape, dtype=np.int32))
        s[2] = grid['sigma_interface'].size
        out = np.full(tuple(s), np.nan, dtype=np.float32) # move to interp_4D_field_to_fixed_sigma_values?

        data_out = hydromodel_grid_transforms.interp_4D_field_to_fixed_sigma_values(
                            grid['z_interface_fractions'], grid['bottom_interface_index'],
                            grid['sigma_interface'],
                            fields['water_depth'].data, fields['tide'].data,
                            si.settings.z0, si.settings.minimum_total_water_depth,
                            data, out,
                            name == 'water_velocity')
        if False:
            # check regridded profiles look reasonable
            from matplotlib import  pyplot as plt
            nt = 1
            n = 75

            plt.plot(grid['z_interface_fractions'][ n, :], data[nt, n, :, 0], c='g')
            plt.plot(grid['sigma_interface'],data_out[nt,n,:,0],c='r')
            plt.show()
        return data_out

    # convert, time etc to hindcast/ buffer index
    def time_to_hydro_model_index(self, time_sec):
        # convert date time to global time step in hindcast just before/after when forward/backtracking
        # always move forward through buffer, but file info is always forward in time
        return self.dataset.get_time_step(time_sec,si.settings.backtracking)

    def hydro_model_index_to_buffer_index(self, nt_hindcast):
        # ring buffer mapping
        return nt_hindcast % si.settings.time_buffer_size


    def are_time_steps_in_buffer(self, time_sec):
        # check if next two steps of remaining  hindcast time steps required to run  are in the buffer
        bi = self.info['buffer_info']
        model_dir = si.run_info.model_direction

        # get hindcast time step at current time
        nt_hindcast = self.time_to_hydro_model_index(time_sec)
        return nt_hindcast in bi['time_steps_in_buffer'] and nt_hindcast + model_dir in bi['time_steps_in_buffer']

    def detect_lonlat_grid(self):
        x = self.dataset.read_variable(self.params['grid_variable_map']['x']).data
        # look at range to see if too small to be meters grid
        islatlong=  (np.nanmax(x)- np.nanmin(x) < 360) or (np.nanmax(x)- np.nanmin(x) < 360)

        if islatlong:
            si.msg_logger.msg('Reader auto-detected lon-lat grid, as grid span  < 360, so using a native  (lon, lat ) a grid, all input coords  should be be lon lat ', note=True,
                              caller = self)

        return islatlong

    def write_grid(self, gridID):
        # write a netcdf of the grid from first hindcast file

        grid = self.grid
        info = self.info
        if 'grid' not in si.output_files: si.output_files['grid'] = []

        f_name = si.output_files['raw_output_file_base'] + f'_grid{gridID:03d}.nc'
        si.output_files['grid'].append(f_name)

        nc = ncdf_util.NetCDFhandler(path.join(si.output_files['run_output_dir'], f_name), 'w')
        nc.create_attribute('index_note', ' all indices are zero based')
        nc.create_attribute('created', str(datetime.now().isoformat()))
        nc.create_attribute('geographic_coords_used', 1 if self.info['geographic_coords'] else 0)

        # ad node types to grid file attributes
        for nt, val in self.si.node_types.items():
            nc.create_attribute(f'node_typeID_{nt}', val)


        nc.write_variable('x', grid['x'], ('node_dim', 'vector2D'))
        nc.write_variable('triangles', grid['triangles'], ('triangle_dim', 'vertex'))
        nc.write_variable('triangle_area', grid['triangle_area'], ('triangle_dim',))
        nc.write_variable('adjacency', grid['adjacency'], ('triangle_dim', 'vertex'), description='number of triangle adjacent to each face, if <0 then is a lateral boundary' + str(si.cell_search_status_flags))
        nc.write_variable('node_type', grid['node_type'], ('node_dim',), attributes={'node_types': str(si.node_types.asdict())}, description='type of node, types are' + str(si.node_types.asdict()))
        nc.write_variable('is_boundary_triangle', grid['is_boundary_triangle'], ('triangle_dim',))
        nc.write_variable('node_to_tri_map', grid['node_to_tri_map'], ('node_dim', 'max_nodes_per_tri'))
        nc.write_variable('tri_per_node', grid['tri_per_node'], ('node_dim',))
        nc.write_variable('bc_transform', grid['bc_transform'], ('triangle_dim', 'bc_transform_rows', 'bc_transform_cols'))

        if 'water_depth' in self.fields:
            nc.write_variable('water_depth', self.fields['water_depth'].data.ravel(), ('node_dim',))

        domain_nodes= grid['grid_outline']['domain']['nodes']
        nc.write_variable('domain_outline_nodes', domain_nodes, ('domain_outline_nodes_dim',),
                          description='node numbers in order around outer model domain')
        domain_xy=  grid['x'][domain_nodes,:]
        nc.write_variable('domain_outline_x', domain_xy, ('domain_outline_nodes_dim', 'vector2D'),
                          description='coords of domain  a columns (x,y)', units='m')

        nc.write_variable('domain_masking_polygon', grid['grid_outline']['domain_masking_polygon'],
                          ('domain_mask_dim', 'vector2D'),
                          description='coords of fillable mask of area outside the domain as columns (x,y)', units='m')

        if len( grid['grid_outline']['islands']) > 0:
            # write any islands
            array_list = [ a['nodes'] for a in grid['grid_outline']['islands']]
            nc.write_packed_1Darrays('island_outline_nodes', array_list, description='node numbers in order around islands')


        nc.close()
        # pre version 0.5 json outline
        #output_files['grid_outline'] = output_files['output_file_base'] + '_' + key + '_outline.json'
        #json_util.write_JSON(path.join(output_files['run_output_dir'], output_files['grid_outline']), grid['grid_outline'])



    def close(self):
        pass
