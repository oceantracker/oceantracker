from oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from oceantracker.common_info_default_param_dict_templates import particle_info
from oceantracker.particle_properties.util import particle_comparisons_util

# proptype for how to  split particles
class SplitParticles(_BaseTrajectoryModifier):
    # splits all particles at given time interval
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'name': PVC('particle_splitting', str),
                                 'splitting_interval': PVC(3600, float, min = 1),
                                 'split_status_greater_than' : PVC('dead', str, possible_values=particle_info['status_flags'].keys()),
                                 'split_status_equal_to': PVC(None,  str, possible_values=particle_info['status_flags'].keys()),
                                 'probability_of_splitting': PVC(1.0, float, min=0., max=1.)
                                 })
    def initialize(self):

        super().initialize()  # set up using regular grid for  stats
        si= self.shared_info
        self.time_of_last_split = self.shared_info.model_start_time

    def select_particles_to_split(self, buffer_index, time, active):
        # get indices of particles to split
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        if self.params['split_status_equal_to'] is None:
            eligible_to_split = part_prop['status'].compare_all_to_a_value('gt', si.particle_status_flags[self.params['split_status_greater_than']], out=self.get_particle_index_buffer())
        else:
            eligible_to_split = part_prop['status'].compare_all_to_a_value('eq',si.particle_status_flags[self.params['split_status_equal_to']], out=self.get_particle_index_buffer())

        # split those eligible_to_split with given probability
        split = particle_comparisons_util.random_selection(eligible_to_split, self.params['probability_of_splitting'], self.get_particle_subset_buffer())

        return split

    def update(self, buffer_index, time, active):
        si = self.shared_info
        part_prop = si.classes['particle_properties']

        if  abs(time- self.time_of_last_split ) <= self.params['splitting_interval']:  return
        si = self.shared_info
        self.time_of_last_split  = time

        # split given fraction
        split = self.select_particles_to_split(buffer_index, time, active)

        x0           = part_prop['x'].get_values(split)
        user_release_groupID   = part_prop['user_release_groupID'].get_values(split)
        IDrelease_group    = part_prop['IDrelease_group'].get_values(split)
        n_cell_guess = part_prop['n_cell'].get_values(split)
        IDpulse      = part_prop['IDpulse'].get_values(split)

        si.classes['particle_group_manager'].release_a_particle_group_pulse(buffer_index, time, x0, IDrelease_group, IDpulse, user_release_groupID, n_cell_guess)