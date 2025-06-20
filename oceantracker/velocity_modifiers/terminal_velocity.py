from  oceantracker.velocity_modifiers._base_velocity_modifer import _VelocityModiferBase
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from numba import njit
from oceantracker.util.numba_util import njitOT

from oceantracker.shared_info import shared_info as si

class TerminalVelocity(_VelocityModiferBase):
    # add terminal velocity to particle velocity  < 0 is downwards ie sinking

    def __init__(self,):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params(value= PVC(0.,float, doc_str='Terminal velocity positive upwards, ie fall velocities are < 0 '),
                                 mean= PVC(0., float, obsolete=True, doc_str='use "value" parameter'),
                                 variance= PVC(None, float, min=0., doc_str='variance of normal distribution of terminal velocity, used to give each particles its own terminal velocity from random normal distribution'),
                                 )

    def add_required_classes_and_settings(self):
        info = self.info

        if self.params['variance'] is not None:
            # set up individual particle terminal velocties
            si.add_class('particle_properties', class_name='ParticleParameterFromNormalDistribution',
                         name='terminal_velocity',
                         value=self.params['value'], variance=self.params['variance'])


    def check_requirements(self):
        self.check_class_required_fields_prop_etc(requires3D=True,
                                required_props_list=['velocity_modifier'])

    def initial_setup(self):

        super().initial_setup()
         
        pgm= si.core_class_roles.particle_group_manager


    def update(self,n_time_step, time_sec, active):
        # modify vertical velocity, if backwards, make negative
         
        part_prop = si.class_roles.particle_properties
        velocity_modifier = part_prop['velocity_modifier']

        if self.params['variance'] is None:
            # constant fall vel
            self._add_constant_vertical_vel(velocity_modifier.data, self.params['value'] * si.run_info.model_direction, active)
        else:
            self._add_individual_vertical_vel(velocity_modifier.data, part_prop['terminal_velocity'].data,  si.run_info.model_direction, active)

    @staticmethod
    @njitOT
    def _add_constant_vertical_vel(v, w, sel):
        for n in sel:
            v[n, 2] += w

    @staticmethod
    @njitOT
    def _add_individual_vertical_vel(v, w, model_dir, sel):
        for n in sel:
            v[n, 2] += w[n]*model_dir

