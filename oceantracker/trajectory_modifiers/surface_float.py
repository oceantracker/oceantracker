import numpy as np
from numba import njit
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange
from oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier

from oceantracker.shared_info import shared_info as si

class SurfaceFloat(_BaseTrajectoryModifier):
    '''
    Keeps particles at z= the free surface/tide height
    '''
    def update(self,n_time_step, time_sec, active):
         
        part_prop= si.class_roles.particle_properties
        self._move_to_free_surface(part_prop['x'].data, part_prop['tide'].data, active)

    @staticmethod
    @njitOTparallel
    def _move_to_free_surface(x, tide, active):
        for nn in prange(active.size):
            n = active[nn]
            x[n, 2] = tide[n]


