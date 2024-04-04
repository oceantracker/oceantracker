import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier
from oceantracker.particle_properties.util import particle_comparisons_util

from oceantracker.shared_info import SharedInfo as si


class CullParticles(_BaseTrajectoryModifier):
    '''
    Prototype for how to  cull particles, this version just culls random particles,
     inherit and change "def select_particles_to_cull(self, time_sec, active):" method to give other behaviors')
    '''

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({ 'cull_interval': PVC( 24*3600, float, min=0),
                                 'cull_status_greater_than':PVC('dead',str,possible_values=si.particle_status_flags.possible_values()),
                                 'cull_status_equal_to': PVC(None,str,possible_values=si.particle_status_flags.possible_values()),
                                 'probability_of_culling' : PVC(0.1, float, min=0,max= 1.)
                                  })

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['x', 'status'])


    def initial_setup(self):

        super().initial_setup()  # set up using regular grid for  stats

        self.time_of_last_cull = si.run_info.time_of_nominal_first_occurrence

    def select_particles_to_cull(self, time_sec, active):
         
        part_prop = si.roles.particle_properties

        if self.params['cull_status_equal_to'] is None:
            #  cull fraction of those active with status high enough
            eligible_to_cull = part_prop['status'].compare_all_to_a_value('gt',si.particle_status_flags[self.params['cull_status_greater_than']], out=self.get_partID_buffer('B1'))
        else:
            eligible_to_cull = part_prop['status'].compare_all_to_a_value('eq', si.particle_status_flags[self.params['cull_status_equal_to']], out=self.get_partID_buffer('B1'))

        culled = particle_comparisons_util.random_selection(eligible_to_cull, self.params['probability_of_culling'], self.get_partID_subset_buffer('B1'))

        return culled

    def update(self,n_time_step, time_sec, active):

        if  abs(time_sec- self.time_of_last_cull ) <= self.params['cull_interval']: return
        self.time_of_last_cull = time_sec


        part_prop =  si.roles.particle_properties

        culled = self.select_particles_to_cull(time_sec, active)
        part_prop['status'].set_values(si.particle_status_flags.dead, culled)

        part_prop['x'].set_values(np.nan, culled)
