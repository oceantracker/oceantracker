from oceantracker.particle_properties._base_particle_properties import ParticleProperty
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.shared_info import SharedInfo as si
from oceantracker.util.numba_util import njitOT

class Speed(ParticleProperty):
    '''
    Calculates the horizontal speed of water or particles.
    '''
    def __init__(self):
        super().__init__()
        self.add_default_params(variable= PVC('water_velocity', str,possible_values=['water_velocity', 'particle_velocity'],
                                          doc_str='Which speed to calculate'),
                                #name = PVC('total_water_depth', str,doc_str='name used within code and in output'),
                                )

    def update(self,n_time_step, time_sec,active):
        # update speed
        vel_prop = si.roles['particle_properties'][self.params['variable']]
        self._calc_speed(vel_prop.data, self.data, active)

    @staticmethod
    @njitOT
    def _calc_speed(v, speed, active):
        for n in active:
            speed[n] = np.sqrt(v[n,0]**2 + v[n,1]**2)

