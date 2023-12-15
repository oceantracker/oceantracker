from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.util.parameter_util import make_class_instance_from_params
from oceantracker.field_group_manager.util import  field_group_manager_util
import numpy as np
from oceantracker.util import time_util
from oceantracker.util.profiling_util import function_profiler
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

    def initial_setup(self):
        si= self.shared_info
        self._setup_hydro_reader(si.working_params['core_classes']['reader'])
        reader = self.reader

        # initialize user supplied custom fields calculated from other fields which may depend on reader fields, eg friction velocity from velocity
        for name, params in si.working_params['class_dicts']['fields'].items():
            i = si.create_class_dict_instance(name, 'fields', 'user', params, crumbs='Adding "fields" from user params')
            i.initial_setup()
            # if not time varying can update once at start from other non-time varying fields
            if not i.is_time_varying(): i.update()
        pass


    def final_setup(self):
        si = self.shared_info
        si.classes['reader'].final_setup()


    def update(self, time_sec):
        # check if all interpolators have the time steps they need
        si  = self.shared_info
        t0 = perf_counter()
        reader = self.reader
        if not reader.are_time_steps_in_buffer(time_sec):
                reader.fill_time_buffer(time_sec)  # get next steps into buffer if not in buffer
        si.block_timer('Fill reader buffers',t0)


    def setup_time_step(self, time_sec, xq, active, fix_bad=True):
        # set up stuff needed by all fields before any  interpolation
        # eg query point and nt the current global time step, from which we are making nt+1
        # currently only sets up primary interpolator
        si =self.shared_info
        si.classes['interpolator'].setup_interp_time_step(time_sec, xq, active,fix_bad=fix_bad)

        return active
    def fix_time_step(self, active):
        # fix any bad walks etc.
        # currently only sets up primary interpolator
        si =self.shared_info
        si.classes['interpolator'].fix_bad_cell_search(active)
        return active


    #@function_profiler(__name__)
    def interp_field_at_particle_locations(self, field_name, active, output=None):
        # in place evaluation of field interpolation
        # interp reader field_name inplace to particle locations to same time and memory
        # output can optionally be redirected to another particle property name different from  reader's field_name
        # particle_prop_name

        si = self.shared_info
        if output is None:
            # over write current values
            output = si.classes['particle_properties'][field_name].used_buffer()
        field_instance = self.fields[field_name]

        if field_instance.is3D():
            self.interpolator._interp_field3D(field_name, field_instance, output, active)
        else:
            self.interpolator._interp_field2D(field_name, field_instance, output, active)
            # print('xx interp',field_name, output[:5])

    def interp_named_field_at_given_locations_and_time(self, field_name, x, time= None, n_cell=None,bc_cord=None, output=None):
        # interp reader field_name at specfied locations,  not particle locations
        # output can optionally be redirected to another particle property name different from  reader's field_name
        # particle_prop_name

        si = self.shared_info
        output = self.interpolator.eval_field_interpolation_at_given_locations(field_name, self.fields[field_name], x, time,
                                                                               output=output, n_cell=n_cell)
        return output

    def _setup_hydro_reader(self,reader_params):
        si = self.shared_info

        self.reader = si.add_core_class('reader', reader_params,   crumbs=f'field Group Manager>setup_hydro_fields> reader class  ', initialise=False)

        reader = self.reader
        reader.initial_setup()
        nc = reader.open_first_file()

        grid,  si.is3D_run   = reader.set_up_grid(nc)
        reader.grid = grid
        reader.setup_water_velocity(nc,grid)

        si.msg_logger.msg(f'Hydro files are "{"3D" if si.is3D_run else "2D"}"', note=True)

        self.interpolator = si.add_core_class('interpolator', si.working_params['core_classes']['interpolator'], crumbs=f'field Group Manager>setup_hydro_fields> interpolator class  ')
        #make_class_instance_from_params('interpolator', params, ml, default_classID=name,  crumbs=crumb_base + crumbs)
        # setup compulsory fields, plus others required

        reader.params['load_fields'] = list(set(['tide','water_depth', 'water_velocity'] + reader.params['load_fields'] ))

        for name in  reader.params['load_fields']:
            self.add_reader_field( name, nc)

        self.setup_dispersion(nc)

        if si.is3D_run:
            self.setup_resupension(nc)

        nc.close()


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
            self.add_reader_field( 'A_Z_profile',nc)
            self.add_custom_field( 'A_Z_profile_vertical_gradient',  dict(name_of_field= 'A_Z_profile'),
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
            self.add_reader_field('bottom_stress', nc) # set up reading from file
            self.add_custom_field('friction_velocity', default_classID='field_friction_velocity_from_bottom_stress',
                              crumbs='initializing resuspension class using bottom stress')
            has_bottom_stress = True
            ml.msg('Found bottom stress in hydro-files, using it to calculate friction velocity for particle resuspension', note=True)
        else:
            self.add_custom_field('friction_velocity',default_classID='field_friction_velocity_from_near_sea_bed_velocity',
                                                    crumbs='initializing friction velocity field used by resuspension class with near bottom velocity')
            has_bottom_stress = False
            ml.msg('No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for suspension', note=True)

        self.info['has_bottom_stress'] = has_bottom_stress


    def add_reader_field(self, name, nc):
        si = self.shared_info
        reader= self.reader
        field_params = reader.get_field_params(nc, name)
        field_params['class_name'] = 'oceantracker.fields._base_field.ReaderField'

        i = si.create_class_dict_instance(name, 'fields', 'reader_field', field_params, crumbs=f' creating reader field setup > "{name}"')

        i.initial_setup()

        # it not field map given then add a map based on name, so only works for scalars
        if name not in reader.params['field_variable_map']:
            reader.params['field_variable_map'][name] = name
            si.msg_logger.msg(f'No field map given for variable named "{name}" in reader "load_fields" parameter, assuming hydro-files have variable with this name, which is a scalar variable',
                         hint='if not a scalar, or need to use another name internally, then  then add a map to reader "field_variable_map parameter"', note=True )

        # read data if not time varying
        if not i.is_time_varying():
            i.data[0, ...] = reader.assemble_field_components(nc, name)

        self.fields[name] = i

    def add_custom_field(self, name,  params={}, crumbs='', default_classID=None):
        # classname must be given
        si = self.shared_info

        if 'class_name' not in params:
            si.msg_logger.msg('field_group_manager> add_custom_field parameters must contain  "class_name" parameter')

        #self.fields[name]= make_class_instance_from_params(name, params, si.msg_logger, default_classID=default_classID,       crumbs=crumbs, merge_params=True)
        i = si.create_class_dict_instance(name, 'fields', 'custom_field', params, crumbs=crumbs+ f' custom field setup > "{name}"', initialise=True,default_classID=default_classID)
        self.fields[name] = i
        return i

    def update_dry_cells(self):
        # update 0-255 dry cell index for each interpolator
        si =self.shared_info
        self.interpolator.update_dry_cells()


    def get_hydo_model_time_step(self):
        return self.shared_info.classes['reader'].info['file_info']['hydro_model_time_step']

    def get_hindcast_range(self):
        si = self.shared_info
        reader = self.reader
        r = [reader.info['file_info']['first_time'],reader.info['file_info']['last_time']]
        return np.asarray(r)

    def write_hydro_model_grids(self):
        si = self.shared_info
        self.reader.write_hydro_model_grid()
