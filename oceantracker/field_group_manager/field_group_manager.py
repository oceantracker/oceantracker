from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC

from oceantracker.field_group_manager.util import  field_group_manager_util
import numpy as np
from oceantracker.util import time_util, ncdf_util, json_util
from datetime import datetime
from oceantracker.util.profiling_util import function_profiler
from oceantracker.common_info_default_param_dict_templates import  cell_search_status_flags, node_types
from os import path
from  oceantracker.interpolator.util.triangle_eval_interp import time_independent_2Dfield_scalar, time_dependent_2Dfield_scalar

from time import  perf_counter
from copy import deepcopy
from oceantracker.shared_info import SharedInfo as si

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
        ml.msg(f'Hydro-model is "{"3D" if info["is3D"] else "2D"}"  type "{reader.__class__.__name__}"', note=True,
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
                   warning=True)

        self.interpolator.final_setup(self.grid)
        self.info['has_open_boundary_nodes'] = np.any(self.grid['node_type'] == node_types['open_boundary'])
        self.info['open_boundary_type'] = si.settings['open_boundary_type']

        # add tidal stranding class
        i = si.class_importer.new_make_class_instance_from_params(si.working_params['core_classes']['tidal_stranding'],'tidal_stranding',                                                 default_classID='tidal_stranding',
                                                crumbs=f'field Group Manager>setup_hydro_fields> tidal standing setup ')
        i.initial_setup()
        self.tidal_stranding = i

        # initialize user supplied custom fields calculated from other fields which may depend on reader fields, eg friction velocity from velocity
        for name, params in si.working_params['class_dicts']['fields'].items():
            self.add_custom_field(name, params, crumbs=f'adding custom field {name}')



    def add_part_prop_from_fields_plus_book_keeping(self):

        pgm = si.classes['particle_group_manager']

        self.interpolator.add_part_prop_for_book_keeping()

        # add part prop for reader and custom fields
        for name, i in self.fields.items():
            if i.params['create_particle_property_with_same_name']:
                pgm.add_particle_property(name, 'from_fields', dict(
                                            write=i.params['write_interp_particle_prop_to_tracks_file'],
                                            vector_dim = i.get_number_components(),
                                            time_varying=True, dtype=np.float64, initial_value=0.))
    def update_reader(self, time_sec):
        # check if all interpolators have the time steps they need

        reader = self.reader
        if not reader.are_time_steps_in_buffer(time_sec):
            t0 = perf_counter()
            reader.fill_time_buffer(self.fields, self.grid, time_sec)  # get next steps into buffer if not in buffer
            si.block_timer('Fill reader buffers',t0)

    def update_tidal_stranding_status(self, time_sec, alive):
        self.tidal_stranding.update(self.grid, time_sec, alive)

    def setup_time_step(self, time_sec, xq, active, fix_bad=True):
        # set up stuff needed by all fields before any 2D interpolation
        # eg query point and nt the current global time step, from which we are making nt+1
        # if fix bad, then blocked and cells are corrected, for RK steps want to delay this till sub-steps are complete, so set fix_bad = false

        part_prop = si.classes['particle_properties']
        info = self.info
        interp = self.interpolator
        grid = self.grid
        fields= self.fields


        # set buffer index from this time and next inside stepinfo
        # get next two buffer time steps around the given time in reader ring buffer
        # plus global time step locations and time ftactions od timre step
        # put results in interpolators step info numpy structure
        info['current_hydro_model_step'], info['current_buffer_steps'], info['fractional_time_steps']= self.time_step_and_buffer_offsets(time_sec)

        if fix_bad:
            # record current cell and location so they can be fixed
            part_prop['cell_search_status'].set_values(cell_search_status_flags['ok'], active)

        # find cell for xq, node list and weight for interp at calls
        interp.find_hori_cell(grid,fields, xq,info['current_buffer_steps'],info['fractional_time_steps'],self.info['open_boundary_type'], active)

        if info['is3D']:
            interp.find_vertical_cell(grid,fields, xq, info['current_buffer_steps'], info['fractional_time_steps'], active)

        if fix_bad:
            interp.fix_bad_cell_search(info['current_buffer_steps'],info['fractional_time_steps'],self.info['open_boundary_type'], active)

    def time_step_and_buffer_offsets(self, time_sec):

        grid= self.grid
        fi = self.info['file_info']
        bi = self.info['buffer_info']

        fractional_time_steps= np.zeros((2,), dtype=np.float64)
        current_buffer_steps = np.zeros((2,), dtype=np.int32)

        hindcast_fraction = (time_sec - fi['first_time']) / (fi['last_time'] - fi['first_time'])
        current_hydro_model_step = int((fi['n_time_steps_in_hindcast'] - 1) * hindcast_fraction)  # global hindcast time step

        # ring buffer locations of surounding steps
        current_buffer_steps[0] = current_hydro_model_step % bi['buffer_size']
        current_buffer_steps[1] = (current_hydro_model_step + int(si.model_direction)) % bi['buffer_size']

        time_hindcast = grid['time'][current_buffer_steps[0]]

        # sets the fraction of time step that current time is between
        # surrounding hindcast time steps
        # abs makes it work when backtracking
        s = abs(time_sec - time_hindcast) / fi['hydro_model_time_step']
        fractional_time_steps[0] = 1.0 - s
        fractional_time_steps[1] = s

        return current_hydro_model_step, current_buffer_steps, fractional_time_steps

    def fix_time_step(self, active):
        # fix any bad walks etc.
        # currently only sets up primary interpolator
        info = self.info
        #todo pass info as s
        self.interpolator.fix_bad_cell_search(info['current_buffer_steps'],info['fractional_time_steps'],info['open_boundary_type'], active)
        return active


    #@function_profiler(__name__)
    def interp_field_at_particle_locations(self, field_name, active, output=None):
        # in place evaluation of field interpolation
        # interp reader field_name inplace to particle locations to same time and memory
        # output can optionally be redirected to another particle property name different from  reader's field_name
        # particle_prop_name


        info= self.info
        grid = self.grid

        part_prop = si.classes['particle_properties']
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

        current_hydro_model_step, current_buffer_steps, fractional_time_steps = self.time_step_and_buffer_offsets(time_sec)

        part_prop = si.classes['particle_properties']

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
        self.reader  = si.class_importer.new_make_class_instance_from_params(reader_builder['params'],'reader',  crumbs=f'field Group Manager>setup_hydro_fields> reader class  ')

        reader = self.reader
        reader.initial_setup(reader_builder['file_info'])
        # give acces to reader info
        info['file_info']= reader.info['file_info']
        info['buffer_info']= reader.info['buffer_info']

        nc = reader.open_first_file()
        #reader.info['variables'] = nc.variable_info  # note all variable names
        #self.info['variables'] = nc.variable_info # note all variable names

        self.grid, self.info['is3D'] = reader.set_up_grid(nc)
        grid = self.grid
        si.hydro_model_cords_in_lat_long = grid['hydro_model_cords_in_lat_long']

        reader.setup_water_velocity(nc,grid)



        # setup request to load compulsory fields
        reader.params['load_fields'] = list(set(['water_velocity'] + reader.params['load_fields']))
        if info['is3D']:
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


    def set_up_interpolator(self):

        i = si.class_importer.new_make_class_instance_from_params(si.working_params['core_classes']['interpolator'],'interpolator',
                                                default_classID='interpolator',
                                                crumbs=f'field Group Manager>setup_hydro_fields> interpolator class  ')
        i.initial_setup(self.grid)
        self.interpolator = i

    def setup_dispersion_and_resuspension(self):
        # these depend on which variables are available inb the hydro file
        reader = self.reader
        fmap = reader.params['field_variable_map']
        info = self.info

        nc = reader.open_first_file()

        # set up dispersion using vertical profiles of A_Z if available
        self._setup_dispersion_params(nc)
        si.add_core_class('dispersion',si.working_params['core_classes']['dispersion'],
                            default_classID='dispersion_random_walk', initialise=True)

        # add resuspension based on friction velocity
        if info['is3D']:
            # add friction velocity from bottom stress or near seabed vel
            self._setup_resupension_params(nc)
            si.add_core_class('resuspension', si.working_params['core_classes']['resuspension'],
                              default_classID='resuspension_basic', initialise=True)

        nc.close()

    def _setup_dispersion_params(self, nc,  has_A_Z_profile=None):

        ml = si.msg_logger
        info = self.info
        fmap = self.reader.params['field_variable_map']

        # has_A_Z_profile can optionally be set by nested readers if all
        # hindcasts have A_Z_profile

        info['has_A_Z_profile'] = False

        if not info['is3D']:
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

    def _setup_resupension_params(self, nc, has_bottom_stress=None):
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
        fmap = reader.params['field_variable_map']
        if name not in fmap or fmap[name] is None:  fmap[name] = name  # if no field map given to use given name as field map
        if type(fmap[name]) != list: fmap[name] = [fmap[name]]  # make a list so all maps the same

        field_params = reader.get_field_params(nc, name)
        field_params['write_interp_particle_prop_to_tracks_file'] =write_interp_particle_prop_to_tracks_file
        i = si.class_importer.new_make_class_instance_from_params(field_params,'fields', name=name, default_classID='field_reader',
                                                crumbs=f'Field Group Manager > adding reader field "{name}"')
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
        si.msg_logger.exit_if_prior_errors()
        # read data if not time varying
        if not i.is_time_varying():
            i.data[0, ...] = reader.assemble_field_components(nc, self.grid, name, i)

        self.fields[name] = i

    def add_custom_field(self, name,  params={}, crumbs='', default_classID=None):
        # class name given or default_classID specified to get from defaults in common_info


        i = si.class_importer.new_make_class_instance_from_params(params,'fields', name,   default_classID=default_classID,
                                                crumbs=crumbs+ f'Field group manager > custom field setup > "{name}"')
        i.info['type'] = 'custom_field'
        i.initial_setup(self.grid, self.fields)
        self.fields[name] = i
        return i

    def update_dry_cell_index(self):
        # update 0-255 dry cell index for each interpolator

        info= self.info
        self.interpolator.update_dry_cell_index(self.grid, info['current_buffer_steps'], info['fractional_time_steps'],)

    def get_hydro_model_info(self):
        d = dict(start_time=self.reader.info['file_info']['first_time'],
                 end_time =self.reader.info['file_info']['last_time'],
                 time_step =self.reader.info['file_info']['hydro_model_time_step']
                 )
        d['duration'] = d['end_time']- d['start_time']
        d['start_date'] = time_util.seconds_to_isostr(d['start_time'])
        d['end_date'] = time_util.seconds_to_isostr(d['end_time'])
        return d

    def write_hydro_model_grid(self, gridID=None):
        # write a netcdf of the grid from first hindcast file

        grid = self.grid
        output_files = si.output_files

        # write grid file
        key = 'grid' if gridID is None or gridID < 1 else f'grid{gridID:02d}'
        output_files[key] = output_files['output_file_base'] + '_'+  key +'.nc'

        nc = ncdf_util.NetCDFhandler(path.join(output_files['run_output_dir'], output_files[key]), 'w')
        nc.write_global_attribute('index_note', ' all indices are zero based')
        nc.write_global_attribute('created', str(datetime.now().isoformat()))

        nc.write_a_new_variable('x', grid['x'], ('node_dim', 'vector2D'))
        nc.write_a_new_variable('triangles', grid['triangles'], ('triangle_dim', 'vertex'))
        nc.write_a_new_variable('triangle_area', grid['triangle_area'], ('triangle_dim',))
        nc.write_a_new_variable('adjacency', grid['adjacency'], ('triangle_dim', 'vertex'))
        nc.write_a_new_variable('node_type', grid['node_type'], ('node_dim',), attributes={'node_types': ' 0 = interior, 1 = island, 2=domain, 3=open boundary'})
        nc.write_a_new_variable('is_boundary_triangle', grid['is_boundary_triangle'], ('triangle_dim',))

        if 'water_depth' in self.fields:
            nc.write_a_new_variable('water_depth', self.fields['water_depth'].data.ravel(), ('node_dim',))
        nc.close()

        output_files['grid_outline'] = output_files['output_file_base'] + '_' + key + '_outline.json'
        json_util.write_JSON(path.join(output_files['run_output_dir'], output_files['grid_outline']), grid['grid_outline'])

    def screen_info(self):
        info = self.info
        s = f':H{info["current_hydro_model_step"]:04d}b{info["current_buffer_steps"][0]:02d}-{info["current_buffer_steps"][1]:02d}'
        return s

    def are_points_inside_domain(self,x, include_dry_cells):
        # only primary/outer grid
        is_inside, part_data = self.interpolator.are_points_inside_domain(self.grid,x)
        n = x.shape[0]
        part_data['hydro_model_gridID'] = np.zeros((n,), dtype=np.int8)

        # get tide and water depth at particle locations

        if not include_dry_cells:
            # only  keep those in wet cells at this time
            is_inside = np.logical_and(is_inside , ~self.are_dry_cells(part_data['n_cell'] ))
        return is_inside, part_data

    def get_grid_limits(self):
        # extend of grid, eg used for outer bounds of gridded stats,
        grid = self.grid
        x = grid['x']
        xlims = [np.amin(x[:, 0]), np.amax(x[:, 0]), np.amin(x[:, 1]), np.amax(x[:, 1])]
        return  xlims

    def are_dry_cells(self, n_cell):
        sel = self.grid['dry_cell_index'][n_cell] > 128  # those dry
        return sel
    
    def close(self):

        self.info.update(self.reader.info)

