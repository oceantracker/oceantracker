from oceantracker.particle_properties._base_particle_properties import CustomParticleProperty
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.shared_info import shared_info as si
from oceantracker.util.numba_util import njitOT

class WaterSpeed(CustomParticleProperty):
    '''
    Calculates the horizontal speed of water, particle speed may differ due to velocity modifiers, e.g. terminal velocity and random walk
    '''
    def __init__(self):
        super().__init__()
        self.add_default_params(  name = PVC('water_speed', str,doc_str='name used within code and in output', units='m/s'),
                                  )

    def update(self,n_time_step, time_sec,active):
        # update speed
        self._calc_speed(si.class_roles.particle_properties['water_velocity'].data, self.data, active)

    @staticmethod
    @njitOT
    def _calc_speed(v, speed, active):
        for n in active:
            speed[n] = np.sqrt(v[n,0]**2 + v[n,1]**2)

