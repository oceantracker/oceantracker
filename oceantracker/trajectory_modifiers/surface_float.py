import numpy as np
from numba import njit
from oceantracker.util.numba_util import njitOT
from oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier

#  keeps particles at the free surface/tide height

class SurfaceFloat(_BaseTrajectoryModifier):

    def update(self, time_sec, active):
        si = self.shared_info
        part_prop= si.classes['particle_properties']
        self.move_to_free_surface(part_prop['x'], part_prop['tide'], active)

@njitOT
def move_to_free_surface(self, x, tide, active):
    for n in active:
        x[n, 2] = tide[n]


