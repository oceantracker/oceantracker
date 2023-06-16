from  oceantracker.velocity_modifiers._base_velocity_modifer import VelocityModiferBase
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from numba import njit

class TerminalVelocity(VelocityModiferBase):
    # add terminal velocity to particle velocity  < 0 is downwards ie sinking

    def __init__(self,):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'mean': PVC(0.,float, doc_str='Terminal velocity positive upwards, ie fall velocities ate negative'),
                                 'variance': PVC(None, float, min=0., doc_str='variance of normal distribution of terminal velocity, used to give each particles its own terminal velocity from random normal distribution'),
                                 'requires_3D': PVC(True, bool)
                                 })

        # only possible in in 3D so tweak flag

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(requires3D=True, required_props_list=['velocity_modifier'])


    def initial_setup(self):
        super().initial_setup()
        si = self.shared_info
        particle= si.classes['particle_group_manager']

        si.msg_logger.msg('When using a terminal velocity, ensure time step is small enough that vertical displacement is a small fraction of the water depth, ie vertical Courant number < 1',warning=True)

        if self.params['variance'] is not None:
           # set up individual particle terminal velocties
           particle.create_particle_property('terminal_velocity','user',dict(
                                                          class_name='oceantracker.particle_properties.particle_parameter_from_normal_distribution.ParticleParameterFromNormalDistribution',
                                             mean=self.params['mean'], variance=self.params['variance']))

    def update(self, time_sec, active):
        # modify vertical velocity, if backwards, make negative
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        velocity_modifier = part_prop['velocity_modifier']

        if self.params['variance'] is None:
            # constant fall vel
            self._add_constant_vertical_vel(velocity_modifier.data, self.params['mean'] * si.model_direction, active)
        else:
            self._add_individual_vertical_vel(velocity_modifier.data, part_prop['terminal_velocity'].data,  si.model_direction, active)

    @staticmethod
    @njit
    def _add_constant_vertical_vel(v, w, sel):
        for n in sel:
            v[n, 2] += w

    @staticmethod
    @njit
    def _add_individual_vertical_vel(v, w, model_dir, sel):
        for n in sel:
            v[n, 2] += w[n]*model_dir

