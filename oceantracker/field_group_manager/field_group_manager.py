from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.util.parameter_util import make_class_instance_from_params
from oceantracker.field_group_manager.util import  field_group_manager_util
import numpy as np
from oceantracker.util import time_util, ncdf_util
from oceantracker.util.profiling_util import function_profiler
from oceantracker.common_info_default_param_dict_templates import  cell_search_status_flags
from os import path

from time import  perf_counter
from copy import deepcopy

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
        si= self.shared_info
        self._setup_hydro_reader(si.working_params['reader_builder'])
        self.set_up_interpolator()



    def final_setup(self):
        self.reader.final_setup()
        self.interpolator.final_setup(self.grid)


        # add tidal stranding class
        si = self.shared_info
        i = make_class_instance_from_params('tidal_stranding', si.working_params['core_classes']['tidal_stranding'], si.msg_logger,
                                            default_classID='tidal_stranding',
                                            crumbs=f'field Group Manager>setup_hydro_fields> tidal standing setup ')

        i.initial_setup()
        self.tidal_stranding = i

        # initialize user supplied custom fields calculated from other fields which may depend on reader fields, eg friction velocity from velocity
        for name, params in si.working_params['class_dicts']['fields'].items():
            i = make_class_instance_from_params(name, params, si.msg_logger, crumbs=f'Adding "fields" from user params for field "{name}"')
            i.initial_setup()
            # if not time varying can update once at start from other non-time varying fields
            if not i.is_time_varying(): i.update()
            if name in self.fields:
                si.msg_logger.msg(f'Custom field "{name}" is already a defined field ', hint='Use another unique name?', fatal_error= True, exit_now=True)
            self.fields[name] = i
        pass


    def add_part_prop_from_fields_plus_book_keeping(self):
        si = self.shared_info
        pgm = si.classes['particle_group_manager']

        self.interpolator.add_part_prop_for_book_keeping()

        # add part prop for reader and custom fields
        for name, i in self.fields.items():
            if i.params['create_particle_property_with_same_name']:
                pgm.add_particle_property(name, 'from_fields', dict(write=i.params['write_interp_particle_prop_to_tracks_file'],
                                                                    vector_dim = i.get_number_components(),
                                                                    time_varying=True, dtype=np.float32, initial_value=0.))


    def update_reader(self, time_sec):
        # check if all interpolators have the time steps they need
        si  = self.shared_info
        t0 = perf_counter()
        reader = self.reader
        if not reader.are_time_steps_in_buffer(time_sec):
                reader.fill_time_buffer(self.fields, self.grid, time_sec)  # get next steps into buffer if not in buffer
        si.block_timer('Fill reader buffers',t0)

    def update_tidal_stranding_status(self, time_sec, alive):
        self.tidal_stranding.update(self.grid, time_sec, alive)

    def setup_time_step(self, time_sec, xq, active, fix_bad=True):
        # set up stuff needed by all fields before any 2D interpolation
        # eg query point and nt the current global time step, from which we are making nt+1
        # if fix bad, then blocked and cells are corrected, for RK steps want to delay this till sub-steps are complete, so set fix_bad = false

        si = self.shared_info
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
        interp.find_hori_cell(grid,fields, xq,info['current_buffer_steps'],info['fractional_time_steps'], active)

        if si.is3D_run:
            interp.find_vertical_cell(grid,fields, xq, info['current_buffer_steps'], info['fractional_time_steps'], active)

        if fix_bad:
            interp.fix_bad_cell_search(info['current_buffer_steps'],info['fractional_time_steps'],active)

    def time_step_and_buffer_offsets(self, time_sec):
        si = self.shared_info
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
        self.interpolator.fix_bad_cell_search(info['current_buffer_steps'],info['fractional_time_steps'], active)
        return active


    #@function_profiler(__name__)
    def interp_field_at_particle_locations(self, field_name, active, output=None):
        # in place evaluation of field interpolation
        # interp reader field_name inplace to particle locations to same time and memory
        # output can optionally be redirected to another particle property name different from  reader's field_name
        # particle_prop_name

        si = self.shared_info
        info= self.info
        grid = self.grid

        part_prop = si.classes['particle_properties']
        n_cell = part_prop['n_cell'].data
        bc_cords = part_prop['bc_cords'].data


        if output is None:
            # over write current values
            output = si.classes['particle_properties'][field_name].used_buffer()
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

    def interp_named_field_at_given_locations_and_time(self, field_name, x, time_sec= None, n_cell=None,bc_cord=None, output=None):
        # interp reader field_name at specfied locations,  not particle locations
        # output can optionally be redirected to another particle property name different from  reader's field_name
        # particle_prop_name
        #todo move interp function into here
        si = self.shared_info
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
        si = self.shared_info

        self.reader  = make_class_instance_from_params('reader', reader_builder['params'], si.msg_logger,
                                            crumbs=f'field Group Manager>setup_hydro_fields> reader class  ')
        #self.reader = si.add_core_class('reader', reader_params,   crumbs=f'field Group Manager>setup_hydro_fields> reader class  ', initialise=False)

        reader = self.reader
        reader.initial_setup(reader_builder['file_info'])
        # give acces to reader info
        self.info['file_info']= reader.info['file_info']
        self.info['buffer_info']= reader.info['buffer_info']

        nc = reader.open_first_file()

        self.grid, si.is3D_run   = reader.set_up_grid(nc)
        grid = self.grid
        reader.setup_water_velocity(nc,grid)

        si.msg_logger.msg(f'Hydro files are "{"3D" if si.is3D_run else "2D"}"', note=True)

        #make_class_instance_from_params('interpolator', params, ml, default_classID=name,  crumbs=crumb_base + crumbs)
        # setup compulsory fields, plus others required

        reader.params['load_fields'] = list(set(['tide','water_depth', 'water_velocity'] + reader.params['load_fields']))

        for name in  reader.params['load_fields']:
            self.add_reader_field( name, nc)

        self.setup_dispersion(nc)

        if si.is3D_run:
            self.setup_resupension(nc)

        nc.close()

    def set_up_interpolator(self):
        si = self.shared_info
        i = make_class_instance_from_params('interpolator', si.working_params['core_classes']['interpolator'],si.msg_logger,
                                                    default_classID='interpolator',
                                                    crumbs=f'field Group Manager>setup_hydro_fields> interpolator class  ')
        i.initial_setup(self.grid)
        self.interpolator = i


    def setup_dispersion(self, nc):
        si = self.shared_info
        ml = si.msg_logger
        params = self.reader.params
        fmap = params['field_variable_map']

        if fmap['A_Z_profile'] is None:
            si.settings['use_A_Z_profile'] = False
            ml.msg('Not using A_Z_profile , using  constant A_Z instead', note=True)
            has_A_Z_profile=False

        elif not nc.is_var(fmap['A_Z_profile']) or not si.settings['use_A_Z_profile']:
            ml.msg(f'Using constant vertical dispersion, A_Z, ie not using A_Z_profile as option set False or cannot find hydro-file variable {fmap["A_Z_profile"]} mapped to A_Z_profile, using  constant A_Z instead', note=True)
            has_A_Z_profile = False
        else:
            self.add_reader_field( 'A_Z_profile',nc,write_interp_particle_prop_to_tracks_file=False)
            self.add_custom_field( 'A_Z_profile_vertical_gradient',  dict(name_of_field= 'A_Z_profile',write_interp_particle_prop_to_tracks_file=False),
                                   default_classID='field_A_Z_profile_vertical_gradient',
                                   crumbs='random walk > Adding A_Z_vertical_gradient field, for using_AZ_profile')
            has_A_Z_profile= True
            si.msg_logger.msg('Found vertical diffusivity profile in hydro-model files,  using profile for vertical random walk', note=True)

        self.info['has_A_Z_profile'] = has_A_Z_profile

    def setup_resupension(self, nc):
        # get fields needed to calulate friction velocity field, needed for resupension
        si = self.shared_info
        ml = si.msg_logger
        params = self.reader.params
        var_map = deepcopy(params['field_variable_map']['bottom_stress'])
        if type(var_map) != list: var_map=[var_map]

        if nc.is_var(var_map[0]):
            self.add_reader_field('bottom_stress', nc,write_interp_particle_prop_to_tracks_file=False) # set up reading from file
            self.add_custom_field('friction_velocity',dict(write_interp_particle_prop_to_tracks_file=False), default_classID='field_friction_velocity_from_bottom_stress',
                              crumbs='initializing resuspension class using bottom stress')
            has_bottom_stress = True
            ml.msg('Found bottom stress in hydro-files, using it to calculate friction velocity for particle resuspension', note=True)
        else:
            self.add_custom_field('friction_velocity',dict(write_interp_particle_prop_to_tracks_file=False),default_classID='field_friction_velocity_from_near_sea_bed_velocity',
                                                    crumbs='initializing friction velocity field used by resuspension class with near bottom velocity')
            has_bottom_stress = False
            ml.msg('No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension', note=True)

        self.info['has_bottom_stress'] = has_bottom_stress


    def add_reader_field(self, name, nc,write_interp_particle_prop_to_tracks_file=True):
        si = self.shared_info
        reader= self.reader
        field_params = reader.get_field_params(nc, name)
        field_params['write_interp_particle_prop_to_tracks_file'] =write_interp_particle_prop_to_tracks_file
        i = make_class_instance_from_params(name, field_params, si.msg_logger,
                                            default_classID='field_reader',
                                            crumbs=f'Field Group Manager > adding reader field "{name}"')
        i.info['type'] = 'reader_field'
        i.initial_setup(self.grid, self.fields)


        # it not field map given then add a map based on name, so only works for scalars
        if name not in reader.params['field_variable_map']:
            reader.params['field_variable_map'][name] = name
            si.msg_logger.msg(f'No field map given for variable named "{name}" in reader "load_fields" parameter, assuming hydro-files have variable with this name, which is a scalar variable',
                         hint='if not a scalar, or need to use another name internally, then  then add a map to reader "field_variable_map parameter"', note=True )

        # read data if not time varying
        if not i.is_time_varying():
            i.data[0, ...] = reader.assemble_field_components(nc, self.grid, name, i)

        self.fields[name] = i

    def add_custom_field(self, name,  params={}, crumbs='', default_classID=None):
        # class name given or default_classID specified to get from defaults in common_info
        si = self.shared_info

        i = make_class_instance_from_params(name, params, si.msg_logger,
                                            default_classID=default_classID,
                                            crumbs=crumbs+ f'Field group manager > custom field setup > "{name}"')
        i.info['type'] = 'custom_field'
        i.initial_setup(self.grid, self.fields)
        self.fields[name] = i
        return i

    def update_dry_cell_index(self):
        # update 0-255 dry cell index for each interpolator
        si =self.shared_info
        info= self.info
        self.interpolator.update_dry_cell_index(self.grid, info['current_buffer_steps'], info['fractional_time_steps'],)



    def get_hydo_model_time_step(self):
        return self.reader.info['file_info']['hydro_model_time_step']


    def get_hindcast_start_end_times(self):
        reader = self.reader
        return self.reader.info['file_info']['first_time'], reader.info['file_info']['last_time']

    def write_hydro_model_grids(self):
        si = self.shared_info
        self.reader.write_hydro_model_grid(self.grid)


    def screen_info(self):
        info = self.info
        s = f':H{info["current_hydro_model_step"]:04d}b{info["current_buffer_steps"][0]:02d}-{info["current_buffer_steps"][1]:02d}'
        return s

    def are_points_inside_domain(self,x):
        is_inside, n_cell, bc = self.interpolator.are_points_inside_domain(self.grid,x)
        return is_inside, n_cell, bc

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
        si = self.shared_info
        self.info.update(self.reader.info)

