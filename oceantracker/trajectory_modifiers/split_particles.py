import numpy as np

from oceantracker.trajectory_modifiers._base_trajectory_modifers import BaseTrajectoryModifier
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC

from oceantracker.particle_properties.util import particle_comparisons_util
from oceantracker.util.basic_util import IDmapToArray
from oceantracker.shared_info import SharedInfo as si
from oceantracker.util.numba_util import njitOT

# proptype for how to  split particles
class SplitParticles(BaseTrajectoryModifier):
    '''
    Splits  particles in two at  given time interval,
    for given status values and  given particle age range.
    Simulates reproduction, but can produce large numbers fast!
    '''

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params(interval= PVC(24*3600, float,doc_str='time interval between splits',units='sec', min = 60),
                                statuses=PLC(['moving', 'on_bottom', 'stranded_by_tide', 'stationary'], str, min_len=1,
                                             doc_str='list of status names to cull ', possible_values=si.particle_status_flags.possible_values()),
                                min_age=PVC(None, float, doc_str='minumim particle age to start splitting', units='sec'),
                                max_age = PVC(None, float, doc_str='maximum particle age to split', units='sec'),
                probability =PVC(1.0, float,doc_str='probability of splitting at each given interval', min=0., max=1.),

                split_status_greater_than = PVC('dead', str, obsolete='use "statuses" list param'),
                split_status_equal_to = PVC(None, str, obsolete='use "statuses" list param'),
                )
    def initial_setup(self):

        super().initial_setup()  # set up using regular grid for  stats
        params = self.params
        self.add_scheduler('splitter01', interval=params['interval'], caller=self)

        self.statuses_to_split = IDmapToArray(si.particle_status_flags, params['statuses'])

        self.age_bounds= np.asarray([ 0. if params['min_age'] is None else params['min_age'],
                                     si.info.large_float if params['max_age'] is None else params['max_age']
                                     ])
        pass
    def select_particles_to_split(self, time_sec, active):
        # get indices of particles to split

        part_prop = si.roles.particle_properties
        params = self.params

        eligible_to_split = self._splitIDs(part_prop['status'].used_buffer(),  self.statuses_to_split,
                                           part_prop['age'].used_buffer(),  self.age_bounds,
                                          self.get_partID_buffer('B1'))
        # split those eligible_to_split with given probability
        split = particle_comparisons_util.random_selection(eligible_to_split, params['probability'], self.get_partID_subset_buffer('B1'))

        return split

    def update(self,n_time_step, time_sec, active):

        if self.schedulers['splitter01'].do_task(n_time_step):
            part_prop = si.roles.particle_properties
            self.time_of_last_split  = time_sec

            # split given fraction
            split = self.select_particles_to_split(time_sec, active)
            release_data= dict(
                    x = part_prop['x'].get_values(split),
                    user_release_groupID = part_prop['user_release_groupID'].get_values(split),
                    IDrelease_group = part_prop['IDrelease_group'].get_values(split),
                    n_cell = part_prop['n_cell'].get_values(split),
                    IDpulse = part_prop['IDpulse'].get_values(split),
                    bc_cords = part_prop['bc_cords'].get_values(split),
                    hydro_model_gridID = part_prop['hydro_model_gridID'].get_values(split),
                    )
            si.core_roles.particle_group_manager.release_a_particle_group_pulse(release_data, time_sec )

    @staticmethod
    @njitOT
    def _splitIDs(status, statuses,age, age_bounds,out):

        found = 0
        for n in  range(status.shape[0]):
            if age_bounds[0] <= age[n] <= age_bounds[1]: # only split if in age range
                for m in range(len(statuses)):
                    # check if in array of required status IDs
                    if status[n] == statuses[m]:
                        out[found] = n # index matching a
                        found += 1
                        break # is so move on to next
        return out[:found]