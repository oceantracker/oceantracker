import numpy as np
from numba import njit
from oceantracker.util.numba_util import njitOT
from oceantracker.trajectory_modifiers._base_trajectory_modifers import BaseTrajectoryModifier

from oceantracker.shared_info import SharedInfo as si

class SurfaceFloat(BaseTrajectoryModifier):
    '''
    Keeps particles at z= the free surface/tide height
    '''
    def update(self,n_time_step, time_sec, active):
         
        part_prop= si.roles.particle_properties
        self._move_to_free_surface(part_prop['x'].data, part_prop['tide'].data, active)

    @staticmethod
    @njitOT
    def _move_to_free_surface(x, tide, active):
        for n in active:
            x[n, 2] = tide[n]


