from  oceantracker.velocity_modifiers._base_velocity_modifer import VelocityModiferBase
from oceantracker.particle_properties.util import particle_operations_util
from oceantracker.particle_properties.particle_parameter_from_normal_distribution import  ParticleParameterFromNormalDistribution
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC

class TerminalVelocity(VelocityModiferBase):
    # add terminal velocity to particle velocity  < 0 is downwards ie sinking

    def __init__(self,):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'name': PVC('terminal_velocity',str),'mean': PVC(0.,float),'variance': PVC(None, float, min=0.)})

        # only possible in in 3D so tweak flag

    def check_requirements(self):
        msg_list = self.check_class_required_fields_properties_grid_vars_and_3D(requires3D=True)
        return msg_list

    def initialize(self):
        super().initialize()
        particle= self.shared_info.classes['particle_group_manager']

        si = self.shared_info
        si.case_log.write_warning('When using a terminal velocity, ensure time step is small enough that vertical displacement is a small fraction of the water depth, ie vertical Courant number < 1')

        if self.params['variance'] is not None:
           # set up individual particle terminal velocties
            p = ParticleParameterFromNormalDistribution()
            particle.create_particle_property('user',dict(name='terminal_velocity', instance=p,
                                             mean=self.params['mean'], variance=self.params['variance']))

    def modify_velocity(self,v, t, active):
        # modify vertical velocity, if backwards, make negative
        si = self.shared_info
        if self.params['variance'] is None:
            # constant fall vel
            particle_operations_util.add_value_to(v[:, 2], self.params['mean'] * si.model_direction, active)
        else:
            particle_operations_util.add_to(v[:, 2], si.classes['particle_properties']['terminal_velocity'].data, active, scale = si.model_direction)


