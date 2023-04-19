from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from oceantracker.field_group_manager.util import  field_group_manager_util
import numpy as np
from oceantracker.util import time_util



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

        self.n_buffer = np.zeros((2, ), dtype=np.int32)

    def initialize(self):
        si=self.shared_info


    def setup_interp_time_step(self, time_sec, xq, active):
        # set up stuff needed by all fields before any 2D interpolation
        # eg query point and nt the current global time step, from which we are making nt+1
        si =self.shared_info
        reader = si.classes['reader']

        # ger buffer index from this time and next
        nb = np.zeros((2, ), dtype=np.int32)

        nt_hindcast_step = reader.time_to_hydro_model_index(time_sec)
        nb[0] = reader.hydro_model_index_to_buffer_offset(nt_hindcast_step)
        nb[1] = reader.hydro_model_index_to_buffer_offset(nt_hindcast_step + si.model_direction) # buffer is forward in timenext index could be wrapped in ring buffer
        self.info['current_hydro_model_step'] = nt_hindcast_step
        self.info['current_buffer_index'] = nb

        grid_time_buffers = reader.grid_time_buffers

        self.code_timer.start('setup_interp_time_step')
        self.n_buffer = nb  # buffer offset just before given time ,

        time_hindcast =   grid_time_buffers['time'][nb[0]]

        self.step_dt_fraction = abs(time_sec -time_hindcast) / reader.info['hydro_model_time_step']
        #if self.step_dt_fraction  < 0  or self.step_dt_fraction > 1.1:
        #    print('feilds',self.step_dt_fraction,nt_hindcast_step, nb, 'timesec',time_util.seconds_to_datetime64(time_sec),    'hindcast time',time_util.seconds_to_datetime64(time_hindcast),'buffer times',              grid_time_buffers['date'][nb],time_sec -time_hindcast,self.step_dt_fraction)
        # update 0-255 dry cell index
        field_group_manager_util.update_dry_cell_index(nb, self.step_dt_fraction, grid_time_buffers['is_dry_cell'],   grid_time_buffers['dry_cell_index'])

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

    def create_field(self, field_type, field_params, crumbs=''):
        si = self.shared_info
        i = si.create_class_instance_as_interator('fields', field_type, field_params, crumbs=crumbs + ' adding  a field ')
        i.info['field_type'] = field_type
        i.initialize()
        return i



