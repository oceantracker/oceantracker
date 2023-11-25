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
    # todo distingish between hydro model reader fields and auxilary fields, eg waves from another reader
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.n_buffer = np.zeros((2, ), dtype=np.int32)

    def initial_setup(self):

        self._setup_primary_hydro_reader()

    def final_setup(self):
        si = self.shared_info
        si.classes['reader'].final_setup()



    def update(self, time_sec):
        # check if all interpolators have the time steps they need
        si  = self.shared_info
        t0 = perf_counter()
        reader = si.classes['reader']
        if not reader.are_time_steps_in_buffer(time_sec):
                reader.fill_time_buffer(time_sec)  # get next steps into buffer if not in buffer
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

    def _setup_primary_hydro_reader(self):
        si = self.shared_info


        reader = si.add_core_class('reader', si.working_params['core_roles']['reader'],   crumbs=f'field Group Manager>setup_hydro_fields> reader class  ', initialise=False)
        reader.initial_setup()
        nc = reader.open_first_file()

        grid,  si.is3D_run   = reader.set_up_grid(nc)
        reader.setup_water_velocity(nc,grid)
        reader.grid = grid
        si.msg_logger.msg(f'Hydro files are "{"3D" if si.is3D_run else "2D"}"', note=True)

        interp = si.add_core_class('interpolator', si.working_params['core_roles']['interpolator'],  crumbs=f'field Group Manager>setup_hydro_fields> interpolator class  ')

        # setup compulsory fields, plus others required

        reader.params['load_fields'] = list(set(['tide','water_depth', 'water_velocity'] + reader.params['load_fields'] ))

        for name in  reader.params['load_fields'] :

            field_params = reader.get_field_params(nc, name)
            field_params['class_name']='oceantracker.fields._base_field.ReaderField'
            i = si.create_class_dict_instance(name, 'fields', 'reader_field', field_params, crumbs= f' creating reader feild  field setup > "{name}"')
            i.initial_setup()

            i.reader = reader
            i.interpolator = interp

            # read data if not time varying
            if not i.is_time_varying() :
                i.data[0, ...] = reader.assemble_field_components(nc, name)

        nc.close()

        # add core total water depth property
        i = self.add_custom_field('total_water_depth',
                dict( class_name= 'oceantracker.fields.total_water_depth.TotalWaterDepth',
                      time_varying=True,write_interp_particle_prop_to_tracks_file =False),
                                           crumbs='initializing core TotalWaterDepth class ')

        i.reader = reader
        i.interpolator = interp
    def add_custom_field(self, name,  params, crumbs=''):
        # classname must be given
        si = self.shared_info


        if 'class_name' not in params:
            si.msg_logger.msg('field_group_manager> add_custom_field parameters must contain  "class_name"')
        i = si.create_class_dict_instance(name, 'fields', 'custom_field', params, crumbs=crumbs+ f' custom field setup > "{name}"', initialise=True)
        i.known_field_types = self.known_field_types

        return i
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
