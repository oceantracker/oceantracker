from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.field_group_manager.util import  field_group_manager_util
import numpy as np
from oceantracker.util import time_util
from oceantracker.util.profiling_util import function_profiler
from time import  perf_counter

#TODO allow fields to be spread across mutiple files and file types
# todo  have field manager with each field having its own reader, grid and interpolator

class FieldGroupManager(ParameterBaseClass):
    # class holding data in file and ability to spatially interpolate fields that it holds
    #   all the fields in a file and interpolation which belongs to the set of fields (rather than individual variable)
    # works with 2D or 3D  with appropriate interplotor
    known_field_types=['reader_field','custom_field']
    # todo distingish between hydro model reader fields and auxilary feilds, eg waves from another reader
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.n_buffer = np.zeros((2, ), dtype=np.int32)

    def initial_setup(self):

        self.initial_setup_hydro_fields()

    def final_setup(self):
        si = self.shared_info
        si.classes['reader'].final_setup()

    def add_reader_field(self, name, reader, params, crumbs=''):
        si = self.shared_info
        params['class_name'] = 'oceantracker.fields._base_field.ReaderField'
        i = si.create_class_dict_instance(name, 'fields', 'reader_field', params, crumbs=crumbs+ f' reader field setup > "{name}"', initialise=False)
        # attached reader to field
        i.reader = reader
        i.initial_setup()

        return i


    def add_custom_field(self, name,  params, crumbs=''):
        # classname must be given
        si = self.shared_info
        if 'class_name' not in params:
            si.msg_logger.msg('field+grup_manager> add_custom_field parameters must contain  "class_name"')
        i = si.create_class_dict_instance(name, 'fields', 'custom_field', params, crumbs=crumbs+ f' custom field setup > "{name}"', initialise=True)
        i.known_field_types = self.known_field_types
        return i

    def fill_reader_buffers_if_needed(self,time_sec):
        # check if all interpolators have the time steps they need
        si  = self.shared_info
        t0 = perf_counter()
        si.classes['interpolator'].check_steps_in_reader_buffer(time_sec)
        si.block_timer('Fill reader buffers',t0)

    def setup_time_step(self, time_sec, xq, active):
        # set up stuff needed by all fields before any  interpolation
        # eg query point and nt the current global time step, from which we are making nt+1
        si =self.shared_info
        # todo one reader/interp at the moment b    ut may be more later
        si.classes['interpolator'].setup_interp_time_step(time_sec, xq, active)
        return active

    #@function_profiler(__name__)
    def interp_field_at_particle_locations(self, field_name, active, output=None):
        # interp reader field_name inplace to particle locations to same time and memory
        # output can optionally be redirected to another particle property name different from  reader's field_name
        # particle_prop_name

        si = self.shared_info
        if output is None:
            # over write current values
            output = si.classes['particle_properties'][field_name].used_buffer()

        si.classes['interpolator'].interp_field_at_current_particle_locations(field_name, active, output)

    def interp_named_field_at_given_locations_and_time(self, field_name, x, time= None, n_cell=None,bc_cord=None, output=None):
        # interp reader field_name at specfied locations,  not particle locations
        # output can optionally be redirected to another particle property name different from  reader's field_name
        # particle_prop_name

        si = self.shared_info
        output = si.classes['interpolator'].eval_field_interpolation_at_given_locations(field_name,si.classes['fields'][field_name], x, time,
                                                                        output=output, n_cell=n_cell)
        return output

    def initial_setup_hydro_fields(self):
        si = self.shared_info


        reader = si.add_core_class('reader', si.working_params['core_roles']['reader'],
                                        crumbs=f'Feild Group Manager>setup_hydro_fields> reader class  ')

        # work out if 3D, by examining wter velocity
        nc = reader.open_first_file()
        vm = reader.params['field_variable_map']

        if nc.is_var(vm['water_velocity'][0]):
            # check if water vel variable has z dim
            si.is3D_run = True if nc.is_var_dim( vm['water_velocity'][0],reader.params['dimension_map']['z_water_velocity'] ) else False

        elif len(vm['water_velocity_depth_averaged']) > 0 and nc.is_var(vm['water_velocity_depth_averaged'][0]):
            # see if depth average velocity available and use it
            vm['water_velocity'] = vm['water_velocity_depth_averaged']
            si.is3D_run = False
        else:
            si.msg_logger.msg(f'Can not find water velocity variables "{str(vm["water_velocity"])}", nor depth average water velocity variables "{str(vm["water_velocity"])}" in first hydro file',
                             fatal_error=True, exit_now=True)

        nc.close()

        si.msg_logger.msg(f'Hydro files are "{"3D" if  si.is3D_run else "2D"}"', note=True)

        reader.initial_setup()


    def update_dry_cells(self):
        # update 0-255 dry cell index for each interpolator
        si =self. shared_info
        si.classes['interpolator'].update_dry_cells()

    def get_hydo_model_time_step(self):
        return self.shared_info.classes['reader'].info['file_info']['hydro_model_time_step']

    def get_hindcast_range(self):
        si = self.shared_info
        reader = si.classes['reader']
        r = [reader.info['file_info']['first_time'],reader.info['file_info']['last_time']]
        return np.asarray(r)

    def write_hydro_model_grids(self):
        si = self.shared_info
        si.classes['reader'].write_hydro_model_grid()
