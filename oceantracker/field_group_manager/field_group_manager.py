from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC

from oceantracker.particle_properties._base_particle_properties import  FieldParticleProperty
import numpy as np
from oceantracker.util import time_util, ncdf_util, json_util
from datetime import datetime
from oceantracker.util.profiling_util import function_profiler

from os import path
from  oceantracker.interpolator.util.triangle_eval_interp import time_independent_2Dfield_scalar, time_dependent_2Dfield_scalar
from oceantracker.field_group_manager.util import field_group_manager_util
from time import  perf_counter
from copy import deepcopy
from oceantracker.shared_info import SharedInfo as si
from  oceantracker.definitions import  node_types, cell_search_status_flags
from oceantracker.util.polygon_util import make_domain_mask

#TODO allow fields to be spread across mutiple files and file types
# todo  have field manager with each field having its own reader, grid and interpolator

class FieldGroupManager(ParameterBaseClass):
    # class holding data in file and ability to spatially interpolate fields that it holds
    #   all the fields in a file and interpolation which belongs to the set of fields (rather than individual variable)
    # works with 2D or 3D  with appropriate interplotor
    known_field_types=['reader_field','custom_field']
    # todo distingish between hydro model reader fields and auxilary fields, eg waves from another reader
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.n_buffer = np.zeros((2, ), dtype=np.int32)
        self.fields={}

        info = self.info
        info['current_hydro_model_step']= 0
        info['fractional_time_steps']= np.zeros((2,), dtype=np.float64)
        info['current_buffer_steps'] = np.zeros((2,), dtype=np.int32)

    def initial_setup(self):
        ml = si.msg_logger
        params= self.params
        info = self.info

        self._setup_hydro_reader(si.run_builder['reader_builder'])

        grid = self.grid
        # write info about reader grid
        bounds = [grid['x'].min(axis=0), grid['x'].max(axis=0)]


        reader= self.reader
        ml.msg(f'Hydro-model is "{"3D" if grid["is3D"] else "2D"}"  type "{reader.__class__.__name__}"', note=True,
                          hint=f'Files found dir and sub-dirs of "{reader.params["input_dir"]}"')

        # note coord system
        if si.hydro_model_cords_in_lat_long:
            b = f'{np.array2string(bounds[0], precision=4, floatmode="fixed")} to {np.array2string(bounds[1], precision=2, floatmode="fixed")}'
        else:
            b = f'{np.array2string(bounds[0], precision=1, floatmode="fixed")} to {np.array2string(bounds[1], precision=1, floatmode="fixed")}'
        ml.msg('grid bounding box = ' + b, tabs=2)

        self.set_up_interpolator()

    def final_setup(self):
        ml = si.msg_logger
        info = self.info
        grid = self.grid
        reader = self.reader
        fmap = reader.params["field_variable_map"]

        reader.final_setup()

        # note dispersion type
        if info['has_A_Z_profile']:
            ml.msg('Found vertical diffusivity profile in hydro-model files', note=True)

        if si.settings['use_A_Z_profile']:
            ml.msg('Using vertical diffusivity profile in hydro-model for vertical random walk', note=True)
        else:
            ml.msg(f'Using constant vertical dispersion, as 2D hydro-model A_Z, ie not using A_Z_profile as option set False or cannot find hydro-file variable {fmap["A_Z_profile"]} mapped to A_Z_profile', note=True)


        if  si.hydro_model_cords_in_lat_long:
            ml.msg(f'Hydro-model grid in (lon,lat) cords, all cords should be in (lon,lat), e.g. release group locations, gridded_stats grid',
                   warning=True)
        else:
            ml.msg(f'Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid',
                   note=True)

        self.info['has_open_boundary_nodes'] = np.any(self.grid['node_type'] == node_types.open_boundary)
        self.info['open_boundary_type'] = si.settings.open_boundary_type

        # set up dry cell adjacency space for triangle walk
        grid['adjacency_with_dry_edges'] = grid['adjacency'].copy()  # working space to add dry cell boundaries to

        self.interpolator.final_setup()

        # add tidal stranding class
        i = si.add_class('tidal_stranding', {}, crumbs=f'field Group Manager>setup_hydro_fields> tidal standing setup ', caller=self)
        self.tidal_stranding = i

        # initialize user supplied custom fields calculated from other fields which may depend on reader fields, eg friction velocity from velocity
        for n,  params in enumerate(si.working_params['roles']['fields']):
            self.add_custom_field(params, crumbs=f'adding custom field #{n:d}')
    def add_part_prop_from_fields_plus_book_keeping(self):

        pgm = si.core_roles.particle_group_manager

        # add part prop for reader and custom fields
        for name, i in self.fields.items():
            if i.params['create_particle_property_with_same_name']:
                si.add_class('particle_properties', class_name='FieldParticleProperty', name=name,
                                            write=i.params['write_interp_particle_prop_to_tracks_file'],
                                            vector_dim = i.get_number_components(),
                                            time_varying=True, dtype='float64', initial_value=0.)
    def update_reader(self, time_sec):
        # check if all interpolators have the time steps they need

        reader = self.reader
        if not reader.are_time_steps_in_buffer(time_sec):
            t0 = perf_counter()
            reader.start_update_timer()
            reader.fill_time_buffer(self.fields, self.grid, time_sec)  # get next steps into buffer if not in buffer
            si.block_timer('Fill reader buffers',t0)
            reader.stop_update_timer()

    def update_tidal_stranding_status(self, time_sec, alive):
        i = self.tidal_stranding
        i.start_update_timer()
        i.update(self.grid, time_sec, alive)
        i.stop_update_timer()

    def setup_time_step(self, time_sec, xq, active,apply_open_boundary_condition=True):

        # set buffer index from this time and next inside stepinfo
        # get next two buffer time steps around the given time in reader ring buffer
        # plus global time step locations and time ftactions od timre step and put results in interpolators step info numpy structure
        info = self.info
        grid =self.grid
        info['current_hydro_model_step'], info['current_buffer_steps'], info['fractional_time_steps']= self._time_step_and_buffer_offsets(time_sec)
        part_prop = si.roles.particle_properties

        # find hori cell
        self._find_hori_cell(time_sec, xq, active)

        # all those that need fixing, lateral boundaries and bad, ie cell_status < blocked_dry_cell
        sel_fix = part_prop['cell_search_status'].find_subset_where(active, 'lt', cell_search_status_flags.ok, out=self.get_partID_subset_buffer('B1'))

        self._apply_domain_boundary_condition(sel_fix)

        if si.settings.block_dry_cells:
            self._apply_dry_cell_boundary_condition(sel_fix)

        # only fix if single grid, nested grids get fixed by nested grid manager
        if apply_open_boundary_condition:
            self._apply_open_boundary_condition(sel_fix)# fix outside boundary

        # finally move back bad cell searches, nan etc
        sel = part_prop['cell_search_status'].find_subset_where(active, 'lt', cell_search_status_flags.dry_cell_edge, out=self.get_partID_subset_buffer('B2'))
        self._move_back(sel) # those still bad, eg nan etc

        if grid['is3D']:
            self._find_vertical_cell(time_sec, xq, active)

    def _find_hori_cell(self, time_sec, xq, active):
        # find horizontal cell for xq, node list and weight for interp at calls

        info = self.info
        self.interpolator.find_hori_cell(self.grid, self.fields, xq, info['current_buffer_steps'],
                                         info['fractional_time_steps'], self.info['open_boundary_type'], active)
    def _apply_domain_boundary_condition(self, sel_bad):
        part_prop = si.roles.particle_properties

        # lateral boundary
        sel = part_prop['cell_search_status'].find_subset_where(sel_bad, 'eq', cell_search_status_flags.domain_edge, out=self.get_partID_subset_buffer('B2'))
        self._move_back(sel)

    def _apply_dry_cell_boundary_condition(self, sel_bad):
        # dry cell boundary
        part_prop = si.roles.particle_properties
        sel = part_prop['cell_search_status'].find_subset_where(sel_bad, 'eq', cell_search_status_flags.dry_cell_edge, out=self.get_partID_subset_buffer('B2'))
        self._move_back(sel)

    def _apply_open_boundary_condition(self, active):
        part_prop = si.roles.particle_properties

        # deal with open boundary
        sel = part_prop['cell_search_status'].find_subset_where(active, 'eq', cell_search_status_flags.open_boundary_edge, out=self.get_partID_subset_buffer('B1'))
        if sel.size > 0:
            if self.info['has_open_boundary_nodes'] and si.settings.open_boundary_type > 0:
                part_prop['status'].set_values(si.particle_status_flags['outside_open_boundary'], sel)
                part_prop['n_cell'].copy('n_cell_last_good', sel)  # move back the cell, but not the location
            else:
                # outside and no open boundary somove back
                self._move_back(sel)

    def _move_back(self, sel):
        # do move backs for blocked and bad
        part_prop = si.roles.particle_properties
        if sel.size > 0:
            part_prop['x'].copy('x_last_good', sel)  # move back location
            part_prop['n_cell'].copy('n_cell_last_good', sel)  # move back the cell

        # debug_util.plot_walk_step(xq, si.core_roles.reader.grid, part_prop)


    def _find_vertical_cell(self, time_sec, xq, active):
        # find vertical cell
        info = self.info
        self.interpolator.find_vertical_cell(self.grid, self.fields, xq, info['current_buffer_steps'], info['fractional_time_steps'], active)


    def _time_step_and_buffer_offsets(self, time_sec):

        grid= self.grid
        fi = self.info['file_info']
        bi = self.info['buffer_info']

        fractional_time_steps= np.zeros((2,), dtype=np.float64)
        current_buffer_steps = np.zeros((2,), dtype=np.int32)

        hindcast_fraction = (time_sec - fi['first_time']) / (fi['last_time'] - fi['first_time'])
        current_hydro_model_step = int((fi['time_steps_in_hindcast'] - 1) * hindcast_fraction)  # global hindcast time step

        # ring buffer locations of surounding steps
        current_buffer_steps[0] = current_hydro_model_step % bi['buffer_size']
        current_buffer_steps[1] = (current_hydro_model_step + int(si.run_info.model_direction)) % bi['buffer_size']

        time_hindcast = grid['time'][current_buffer_steps[0]]

        # sets the fraction of time step that current time is between
        # surrounding hindcast time steps
        # abs makes it work when backtracking
        s = abs(time_sec - time_hindcast) / fi['hydro_model_time_step']
        fractional_time_steps[0] = 1.0 - s
        fractional_time_steps[1] = s

        return current_hydro_model_step, current_buffer_steps, fractional_time_steps

    #@function_profiler(__name__)
    def interp_field_at_particle_locations(self, field_name, active, output=None):
        # in place evaluation of field interpolation
        # interp reader field_name inplace to particle locations to same time and memory
        # output can optionally be redirected to another particle property name different from  reader's field_name
        # particle_prop_name


        info= self.info
        grid = self.grid

        part_prop = si.roles.particle_properties
        n_cell = part_prop['n_cell'].data
        bc_cords = part_prop['bc_cords'].data

        if output is None:
            # over write current values
            output = part_prop[field_name].used_buffer()
        field_instance = self.fields[field_name]

        if field_instance.is3D():
            # fractions for water vel. are log layer in bottom cell
            nz_cell = part_prop['nz_cell'].data
            z_fraction = part_prop['z_fraction_water_velocity'].data if field_name == 'water_velocity' else part_prop['z_fraction'].data

            self.interpolator._interp_field3D(field_name, field_instance,grid, info['current_buffer_steps'], info['fractional_time_steps'],
                                              n_cell, nz_cell, z_fraction, bc_cords,
                                              output, active)
        else:
            self.interpolator._interp_field2D(field_name, field_instance,grid,info['current_buffer_steps'], info['fractional_time_steps'],
                                              n_cell, bc_cords,
                                              output, active)
            # print('xx interp',field_name, output[:5])


    def interp_named_field_at_given_locations_and_time(self, field_name, x, time_sec= None, n_cell=None,bc_cords=None, output=None, hydro_model_gridID=None):
        # interp reader field_name at specfied locations,  not particle locations
        # output can optionally be redirected to another particle property name different from  reader's field_name
        # particle_prop_name
        #todo move interp function into here

        info = self.info

        field_instance = self.fields[field_name]


        if time_sec is None:
            # dummy time
            time_sec= self.reader.info['file_info']['first_time']

        current_hydro_model_step, current_buffer_steps, fractional_time_steps = self._time_step_and_buffer_offsets(time_sec)

        part_prop = si.roles.particle_properties

        # is no output name given particle property for output is same as hindcast field_name
        if output is None:
            output = np.full((x.shape[0], field_instance.data.shape[3]), np.nan) if field_instance.data.shape[3] > 1 else np.full((x.shape[0],), np.nan)

        if n_cell is None:
            n_cell = self.interpolator.initial_horizontal_cell(self.grid, x)

        if bc_cords is None:
            bc_cords = self.interpolator.get_bc_cords(self.grid, x, n_cell)

        active = np.arange(x.shape[0])

        if field_instance.is3D():
            # fractions for water vel. are log layer in bottom cell
            #todo 3D not working, needs nz cell and z fraction
            z_fraction = junk if field_name == 'water_velocity' else junk

            self.interpolator._interp_field3D(field_name, field_instance, self.grid, current_buffer_steps, fractional_time_steps,
                                              n_cell, nz_cell, z_fraction, bc_cords,
                                              output, active)
        else:
            self.interpolator._interp_field2D(field_name, field_instance, self.grid, current_buffer_steps, fractional_time_steps,
                                              n_cell, bc_cords,
                                              output, active)

        return output

    def _setup_hydro_reader(self,reader_builder):

        info = self.info

        self.reader  = si.add_class('reader', reader_builder['params'],
                                caller=self, crumbs=f'setup_hydro_fields> reader class ')

        # give acces to reader info
        reader = self.reader

        info['file_info'] = reader.info['file_info']
        info['buffer_info'] = reader.info['buffer_info']

        nc = reader.open_first_file()
        # see if mapped any feilds are present
        f = {}
        for name, item in reader.params['field_variable_map'].items():
            if item is None or (type(item)==list and len(item)==0): continue # pass oif not given
            file_var_name = item[0] if type(item) ==list else  item # only check first item for vectors
            f[name] = True if nc.is_var(file_var_name) else False
        info['found_mapped_fields'] = f

        #reader.info['variables'] = nc.variable_info  # note all variable names
        #self.info['variables'] = nc.variable_info # note all variable names

        self.grid = reader.set_up_grid(nc)
        grid = self.grid
        si.hydro_model_cords_in_lat_long = grid['hydro_model_cords_in_lat_long']

        reader.setup_water_velocity(nc,grid)

        # setup request to load compulsory fields
        reader.params['load_fields'] = list(set(['water_velocity'] + reader.params['load_fields']))
        if grid['is3D']:
            # request load of water depth and tide fields which are required  in 3D
            reader.params['load_fields'] = list(set(['tide', 'water_depth'] + reader.params['load_fields']))
        else:
            # add tide and water depth if available which may be used in dry cell claculation
            fm = reader.params['field_variable_map']
            if nc.is_var(fm['tide']) and nc.is_var(fm['water_depth']):
                reader.params['load_fields'] = list(set(['tide', 'water_depth'] + reader.params['load_fields']))

        # add all reader/file fields
        for name in  reader.params['load_fields']:
            self.add_reader_field( name, nc)

        nc.close()

    def is_field(self, name): return  name in self.fields

    def set_up_interpolator(self):

        i = si.add_class('interpolator', si.working_params['core_roles']['interpolator'],initialize=False,
                                             default_classID='interpolator', caller= self,
                                             crumbs=f'field Group Manager>setup_hydro_fields> interpolator class  ')
        i.initial_setup(self.grid)
        self.interpolator = i

    def setup_dispersion_and_resuspension_fields(self):
        # these depend on which variables are available inb the hydro file
        reader = self.reader
        fmap = reader.params['field_variable_map']
        grid= self.grid

        nc = reader.open_first_file()

        # set up dispersion using vertical profiles of A_Z if available
        self._setup_required_dispersion_fields(nc)

        # add resuspension based on friction velocity
        if grid['is3D']:
            # add friction velocity from bottom stress or near seabed vel
            self._setup_required_resupension_fields(nc)

        nc.close()

    def _setup_required_dispersion_fields(self, nc, has_A_Z_profile=None):

        ml = si.msg_logger
        info = self.info
        grid = self.grid
        fmap = self.reader.params['field_variable_map']

        # has_A_Z_profile can optionally be set by nested readers if all
        # hindcasts have A_Z_profile

        info['has_A_Z_profile'] = False

        if not grid['is3D']:
            si.settings['use_A_Z_profile'] = False
            return

        if has_A_Z_profile is None:
            has_A_Z_profile = 'A_Z_profile' in fmap \
                            and (fmap['A_Z_profile'] is not None \
                            and nc.is_var(fmap['A_Z_profile']))

        if has_A_Z_profile:
            self.add_reader_field( 'A_Z_profile',nc,write_interp_particle_prop_to_tracks_file=False)
            self.add_custom_field( 'A_Z_profile_vertical_gradient',  dict(name_of_field= 'A_Z_profile',write_interp_particle_prop_to_tracks_file=False),
                                   default_classID='field_A_Z_profile_vertical_gradient',
                                   crumbs='random walk > Adding A_Z_vertical_gradient field, for using_AZ_profile')
            info['has_A_Z_profile'] = True
            si.settings['use_A_Z_profile'] = si.settings['use_A_Z_profile'] and info['has_A_Z_profile']
        else:
            si.settings['use_A_Z_profile'] = False


        return

    def _setup_required_resupension_fields(self, nc, has_bottom_stress=None):
        # get fields needed to calculate friction velocity field, needed for suspension

        ml = si.msg_logger
        fmap = self.reader.params['field_variable_map']

        # has_bottom_stress can optinaly be set by nested readers if all
        # hindcasts have botton stress data
        if has_bottom_stress is None:
            has_bottom_stress = 'bottom_stress' in fmap \
                                and fmap['bottom_stress'] is not None \
                                and nc.is_var(fmap['bottom_stress'])
        if has_bottom_stress:
            self.add_reader_field('bottom_stress', nc,write_interp_particle_prop_to_tracks_file=False) # set up reading from file
            self.add_custom_field('friction_velocity',dict(write_interp_particle_prop_to_tracks_file=False), default_classID='field_friction_velocity_from_bottom_stress',
                              crumbs='initializing resuspension class using bottom stress')
            ml.msg('Found bottom stress in hydro-files, using it to calculate friction velocity for particle resuspension', note=True)
        else:
            self.add_custom_field('friction_velocity',dict(write_interp_particle_prop_to_tracks_file=False),default_classID='field_friction_velocity_from_near_sea_bed_velocity',
                                                    crumbs='initializing friction velocity field used by resuspension class with near bottom velocity')
            ml.msg('No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension', note=True)

    def add_reader_field(self, name, nc,write_interp_particle_prop_to_tracks_file=True):

        ml = si.msg_logger
        reader= self.reader

        # ensure all field maps are lists, and if not given use name as the field map
        fmap = deepcopy(reader.params['field_variable_map'])
        if name not in fmap or fmap[name] is None:  fmap[name] = name  # if no field map given to use given name as field map
        if type(fmap[name]) != list: fmap[name] = [fmap[name]]  # make a list so all maps the same

        field_params = reader.get_field_params(nc, name)
        field_params['name'] = name
        field_params['write_interp_particle_prop_to_tracks_file'] = write_interp_particle_prop_to_tracks_file

        i =  si._class_importer.new_make_class_instance_from_params('fields',field_params,default_classID='field_reader',
                                caller=self,   crumbs=f'Field Group Manager > adding reader field "{name}"')

        i.info['type'] = 'reader_field'
        i.initial_setup(self.grid, self.fields)


        # it not field map given then add a map based on name, so only works for scalars
        fm = reader.params['field_variable_map']
        if name not in fm:
            reader.params['field_variable_map'][name] = name
            ml.msg(f'No field map given for variable named "{name}" in reader "load_fields" parameter, assuming hydro-files have variable with this name, which is a scalar variable',
                         hint='if not a scalar, or need to use another name internally, then  then add a map to reader "field_variable_map parameter"',
                         crumbs ='field_group_manager> adding reader fields',
                              note=True )

        # check if variables are in file
        for file_var_name in fm[name] if type(fm[name]) == list else [fm[name]]:
            if not nc.is_var(file_var_name):
                ml.msg(f'Cannot find field variable named "{file_var_name}" in hydro-file mapped to  field "{name}" ',
                                hint=f'variable is not in file, currently variable map is = "{fm[name]}"',
                                  fatal_error=True)
        si.msg_logger.exit_if_prior_errors('errors setting up fields')
        # read data if not time varying
        if not i.is_time_varying():
            i.data[0, ...] = reader.assemble_field_components(nc, self.grid, name, i)

        self.fields[name] = i

    def add_custom_field(self, name,  params={}, crumbs='', default_classID=None):
        # class name given or default_classID specified to get from defaults in common_info

        i = si._class_importer.new_make_class_instance_from_params('fields', params,   default_classID=default_classID,
                        caller = self, crumbs=crumbs+ f'Field group manager > custom field setup > "{name}"')
        i.info['type'] = 'custom_field'
        i.params['name'] = name
        i.initial_setup(self.grid, self.fields)
        self.fields[name] = i
        return i

    def update_dry_cell_values(self):
        # update 0-255 dry cell index for each interpolator
        grid = self.grid
        info= self.info
        field_group_manager_util.update_dry_cell_index( grid['is_dry_cell_buffer'], grid['dry_cell_index'],
                                                   info['current_buffer_steps'], info['fractional_time_steps'])

        # dev copy adjacency matrix and include dry cell lateral boundaries
        #field_group_manager_util.update_dry_cell_adjacency(grid['adjacency'], grid['dry_cell_index'], grid['adjacency_with_dry_edges'])
        #print('xx', np.count_nonzero(grid['adjacency_with_dry_edges']==-3))
        pass

    def get_hindcast_info(self):
        d = dict(start_time=self.reader.info['file_info']['first_time'],
                 end_time =self.reader.info['file_info']['last_time'],
                 time_step =self.reader.info['file_info']['hydro_model_time_step']
                 )
        d['duration'] = d['end_time']- d['start_time']
        d['start_date'] = time_util.seconds_to_isostr(d['start_time'])
        d['end_date'] = time_util.seconds_to_isostr(d['end_time'])
        d['date_span'] = time_util.seconds_to_pretty_duration_string( abs(d['end_time']-d['start_time']) )
        x= self.grid['x'][:,:2]
        d['bounding_box'] = np.asarray([x.min(axis=0).tolist(),x.max(axis=0).tolist()])
        return d

    def write_hydro_model_grid(self, gridID=None):
        # write a netcdf of the grid from first hindcast file

        grid = self.grid
        output_files = si.output_files

        # add to list of outptut files
        if gridID is None or gridID ==0:
            # primary/outer grid
            f_name= output_files['raw_output_file_base'] + '_grid.nc'
            output_files['grid'] = f_name
        else:
            if 'nested_grid' not in output_files: output_files['nested_grid'] = []
            f_name = output_files['raw_output_file_base'] + f'_grid{gridID:03d}.nc'
            output_files['nested_grids'].append(f_name)

        # only  write grid for first parallel cases
        if si.run_info.caseID > 0: return

        nc = ncdf_util.NetCDFhandler(path.join(output_files['run_output_dir'], f_name), 'w')
        nc.write_global_attribute('index_note', ' all indices are zero based')
        nc.write_global_attribute('created', str(datetime.now().isoformat()))

        nc.write_a_new_variable('x', grid['x'], ('node_dim', 'vector2D'))
        nc.write_a_new_variable('triangles', grid['triangles'], ('triangle_dim', 'vertex'))
        nc.write_a_new_variable('triangle_area', grid['triangle_area'], ('triangle_dim',))
        nc.write_a_new_variable('adjacency', grid['adjacency'], ('triangle_dim', 'vertex'),description= 'number of triangle adjacent to each face, if <0 then is a lateral boundary' + str(cell_search_status_flags.get_edge_vars()))
        nc.write_a_new_variable('node_type', grid['node_type'], ('node_dim',), attributes={'node_types': str(node_types.asdict())}, description='type of node, types are' + str(node_types.asdict()))
        nc.write_a_new_variable('is_boundary_triangle', grid['is_boundary_triangle'], ('triangle_dim',))



        if 'water_depth' in self.fields:
            nc.write_a_new_variable('water_depth', self.fields['water_depth'].data.ravel(), ('node_dim',))

        domain_nodes= grid['grid_outline']['domain']['nodes']
        nc.write_a_new_variable('domain_outline_nodes', domain_nodes, ('domain_outline_nodes_dim',),
                                description='node numbers in order around outer model domain')
        domain_xy=  grid['x'][domain_nodes,:]
        nc.write_a_new_variable('domain_outline_x', domain_xy, ('domain_outline_nodes_dim','vector2D'),
                                description='coords of domain  a columns (x,y)', units='m')
        domain_mask_xy = make_domain_mask(domain_xy)

        nc.write_a_new_variable('domain_mask_x', domain_mask_xy, ('domain_mask_dim', 'vector2D'),
                                description='coords of fillable mask of area outside the domain as columns (x,y)', units='m')

        if len( grid['grid_outline']['islands']) > 0:
            # write any islands
            array_list = [ a['nodes'] for a in grid['grid_outline']['islands']]
            nc.write_packed_1Darrays('island_outline_nodes', array_list, description='node numbers in order around islands')


        nc.close()
        # pre version 0.5 json outline
        #output_files['grid_outline'] = output_files['output_file_base'] + '_' + key + '_outline.json'
        #json_util.write_JSON(path.join(output_files['run_output_dir'], output_files['grid_outline']), grid['grid_outline'])

    def screen_info(self):
        info = self.info
        s = f':H{info["current_hydro_model_step"]:04d}b{info["current_buffer_steps"][0]:02d}-{info["current_buffer_steps"][1]:02d}'
        return s

    def are_points_inside_domain(self,x, include_dry_cells):
        # only primary/outer grid
        is_inside, part_data = self.interpolator.are_points_inside_domain(self.grid, x)
        n = x.shape[0]
        part_data['hydro_model_gridID'] = np.zeros((n,), dtype=np.int8)

        # get tide and water depth at particle locations

        if not include_dry_cells:
            # only  keep those in wet cells at this time
            is_inside = np.logical_and(is_inside , ~self.are_dry_cells(part_data['n_cell'] ))
        return is_inside, part_data


    def are_dry_cells(self, n_cell):
        sel = self.grid['dry_cell_index'][n_cell] > 128  # those dry
        return sel
    
    def close(self):
        self.info.update(self.reader.info)

