from oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.common_info_default_param_dict_templates import particle_info
from oceantracker.particle_properties.util import particle_comparisons_util


# proptype for how to  split particles
class SplitParticles(_BaseTrajectoryModifier):
    # splits all particles at given time interval
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'splitting_interval': PVC(3600, float, min = 1),
                                 'split_status_greater_than' : PVC('dead', str, possible_values=particle_info['status_flags'].keys()),
                                 'split_status_equal_to': PVC(None,  str, possible_values=particle_info['status_flags'].keys()),
                                 'probability_of_splitting': PVC(1.0, float, min=0., max=1.)
                                 })
    def initial_setup(self):

        super().initial_setup()  # set up using regular grid for  stats
        si= self.shared_info
        self.time_of_last_split = si.run_info['model_start_time']

    def select_particles_to_split(self, time_sec, active):
        # get indices of particles to split
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        if self.params['split_status_equal_to'] is None:
            eligible_to_split = part_prop['status'].compare_all_to_a_value('gt', si.particle_status_flags[self.params['split_status_greater_than']], out=self.get_partID_buffer('B1'))
        else:
            eligible_to_split = part_prop['status'].compare_all_to_a_value('eq',si.particle_status_flags[self.params['split_status_equal_to']], out=self.get_partID_buffer('B1'))

        # split those eligible_to_split with given probability
        split = particle_comparisons_util.random_selection(eligible_to_split, self.params['probability_of_splitting'], self.get_partID_subset_buffer('B1'))

        return split

    def update(self, time_sec, active):
        si = self.shared_info
        part_prop = si.classes['particle_properties']

        if  abs(time_sec - self.time_of_last_split) <= self.params['splitting_interval']:  return
        si = self.shared_info
        self.time_of_last_split  = time_sec

        # split given fraction
        split = self.select_particles_to_split(time_sec, active)

        x0           = part_prop['x'].get_values(split)
        user_release_groupID   = part_prop['user_release_groupID'].get_values(split)
        IDrelease_group    = part_prop['IDrelease_group'].get_values(split)
        n_cell_guess = part_prop['n_cell'].get_values(split)
        IDpulse      = part_prop['IDpulse'].get_values(split)
        hydro_model_gridID = part_prop['hydro_model_gridID'].get_values(split)

        si.classes['particle_group_manager'].release_a_particle_group_pulse(time_sec, x0, IDrelease_group, IDpulse, user_release_groupID, n_cell_guess,hydro_model_gridID)