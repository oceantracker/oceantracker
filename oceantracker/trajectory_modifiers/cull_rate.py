from oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.shared_info import shared_info as si
from oceantracker.util.numba_util import  njitOT

class CullRate(_BaseTrajectoryModifier):
    '''
    Decays particle numbers by killing random selection of particles based at each time step give averagerate per second decay_rate.
    Probability of single particle decay given by  (1-exp(-time_step*decay_rate), for small time steps prob. is approx. time_step*decay_rate
    '''
    def __init__(self):
        super().__init__()
        self.add_default_params( decay_rate= PVC( 1.*3600*24, float, doc_str=' Particle decays at this average rate',
                                                          units='particles per sec'))

    def initial_setup(self, **kwargs):
        self.info['prob_culling'] = 1. - np.exp(-self.params['decay_rate'] * si.settings.time_step)
    def update(self, n_time_step, time_sec, active):
        # update decay prop each time step
        part_prop = si.class_roles.particle_properties

        self._do_cull(part_prop['status'].data, self.info['prob_culling'],si.particle_status_flags.dead, active)

    @staticmethod
    @njitOT
    def _do_cull(status, prob_culling, status_dead, active):
        for n in active:
            if status[n] >= 0 and (np.random.rand() <= prob_culling):
                status[n]= status_dead

