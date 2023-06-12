from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.field_group_manager.util import  field_group_manager_util
import numpy as np
from oceantracker.util import time_util
from oceantracker.util.profiling_util import function_profiler


#TODO allow fields to be spread across mutiple files and file types
# todo  have field manager with each field having its own reader, grid and interpolator

class FieldGroupManager(ParameterBaseClass):
    # class holding data in file and ability to spatially interpolate fields that it holds
    #   all the fields in a file and interpolation which belongs to the set of fields (rather than individual variable)
    # works with 2D or 3D  with appropriate interplotor
    known_field_types = ['from_reader_field','derived_from_reader_field', 'depth_averaged_from_reader_field', 'user']

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'name': PVC('field_group_manager', str)})

        self.n_buffer = np.zeros((2, ), dtype=np.int32)


    def initial_setup(self):
        si=self.shared_info

    def fill_reader_buffers_if_needed(self,time_sec):
        # check if all interpolators have the time steps they need
        si  = self.shared_info
        si.classes['interpolator'].check_steps_in_reader_buffer(time_sec)


    def setup_time_step(self, time_sec, xq, active):
        # set up stuff needed by all fields before any  interpolation
        # eg query point and nt the current global time step, from which we are making nt+1
        si =self.shared_info
        # todo one reader/interp at the moment b    ut may be more later
        si.classes['interpolator'].setup_interp_time_step(time_sec, xq, active)
        return active

    def eval_water_velocity(self, output, active ):
        si = self.shared_info
        si.classes['interpolator'].eval_water_velocity_at_particle_locations(output, active)

    #@function_profiler(__name__)
    def interp_named_field_at_particle_locations(self, fieldName, active, output=None):
        # interp reader fieldName inplace to particle locations to same time and memory
        # output can optionally be redirected to another particle property name different from  reader's fieldName
        # particle_prop_name

        si = self.shared_info
        if output is None:
            # over write current values
            output = si.classes['particle_properties'][fieldName].used_buffer()
        i = si.classes['fields'][fieldName]
        si.classes['interpolator'].interp_field_at_current_particle_locations(i, active, output)

    def interp_named_field_at_given_locations_and_time(self, fieldName, x, time= None, n_cell=None,bc_cord=None, output=None):
        # interp reader fieldName at specfied locations,  not particle locations
        # output can optionally be redirected to another particle property name different from  reader's fieldName
        # particle_prop_name

        si = self.shared_info
        output = si.classes['interpolator'].eval_field_interpolation_at_given_locations(si.classes['fields'][fieldName], x, time,
                                                                        output=output, n_cell=n_cell)
        return output

    def create_field(self, name, field_group, field_params, crumbs=''):
        si = self.shared_info
        i = si.create_class_dict_instance(name,'fields', field_group, field_params, crumbs=crumbs + ' adding  a field ')
        i.initial_setup()
        return i


    def update_dry_cells(self):
        # update 0-255 dry cell index for each interpolator
        si =self. shared_info
        si.classes['interpolator'].update_dry_cells()



    def write_hydro_model_grids(self):
        si = self.shared_info
        si.classes['reader'].write_hydro_model_grid()
