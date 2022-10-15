from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from oceantracker.field_group_manager.util import field_group_manager_util
import numpy as np
#TODO allow feilds to be spread across mutiple files and file types
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

        # set up fields shared info
        si = self.shared_info

        self.n_buffer = 0


    def initialize(self):
        si=self.shared_info
        si.create_class_interator('fields', known_iteration_groups=self.known_field_types)


    def add_field(self, field_type, class_params, crumbs=None):
        si = self.shared_info
        i = si.add_class_instance_to_list_and_merge_params('fields', field_type, class_params, crumbs=crumbs)
        si.add_class_instance_to_interators(i.params['name'], 'fields', field_type, i)
        return i

    def setup_interp_time_step(self,nb, time_sec, xq, active):
        # set up stuff needed by all fields before any 2D interpolation
        # eg query point and nt the current global time step, from which we are making nt+1
        si=self.shared_info
        grid = si.classes['reader'].grid

        self.code_timer.start('setup_interp_time_step')
        self.n_buffer = nb  # buffer offset just before given time ,

        # when back tracking hindcast buffer is ordered  backwards in time, and time step is still positive
        # thus step fraction remains positive
        self.step_dt_fraction = abs(time_sec - grid['time'][nb]) / si.hindcast_time_step

        # update 0-255 dry cell index
        field_group_manager_util.update_dry_cell_index(nb, self.step_dt_fraction, grid['is_dry_cell'], grid['dry_cell_index'])

        # find cell for xq, node list and weight for interp at calls
        si.classes['interpolator'].find_cell(xq, nb, self.step_dt_fraction, active)


        self.code_timer.stop('setup_interp_time_step')

        return active

    def interp_named_field_at_particle_locations(self, fieldName, active, output=None):
        # interp reader fieldName inplace to particle locations to same time and memory
        # output can optionally be redirected to another particle property name different from  reader's fieldName
        # particle_prop_name

        self.code_timer.start('interp_named_field_at_particle_locations')
        si = self.shared_info
        if output is None:
            output = si.classes['particle_properties'][fieldName].dataInBufferPtr()

        si.classes['interpolator'].eval_field_interpolation_at_particle_locations(si.classes['fields'][fieldName], self.n_buffer, output, active, step_dt_fraction=self.step_dt_fraction)

        self.code_timer.stop('interp_named_field_at_particle_locations')

    def interp_named_field_at_given_locations_and_time(self, fieldName, x, time= None, n_cell=None, output=None):
        # interp reader fieldName at specfied locations,  not particle locations
        # output can optionally be redirected to another particle property name different from  reader's fieldName
        # particle_prop_name
        self.code_timer.start('interp_at_given_locations_and_time')
        si = self.shared_info

        output = si.classes['interpolator'].eval_field_interpolation_at_given_locations(si.classes['fields'][fieldName], x, time, output=output, n_cell=n_cell)

        self.code_timer.stop('interp_at_given_locations_and_time')

        return output


    def get_current_reader_time_buffer_index(self): return self.n_buffer

