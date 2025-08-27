
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util import basic_util
from oceantracker.util.numba_util import njitOT,njitOTparallel,prange
from oceantracker.shared_info import  shared_info as si
class _BaseResuspension(ParameterBaseClass):

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({}) # must be 3D



    # all particles checked to see if they need status changing
    def update(self,n_time_step, time_sec, active): basic_util.nopass('must have update',self)

    def select_particles_to_resupend(self, active):
        # compare to single critical value
        # todo add comparison to  particles critical value from distribution,
        #  add new particle property to hold  individual critical values
        part_prop = si.class_roles.particle_properties

        resupend = self._find_part_to_resuspend(
                                part_prop['status'].used_buffer(),
                                si.particle_status_flags.on_bottom,
                                part_prop['friction_velocity'].data,
                                self.params['critical_friction_velocity'],
                                out=self.get_partID_buffer('B1'))
        return resupend

    @staticmethod
    @njitOT
    def _find_part_to_resuspend(status, on_bottom,friction_velocity, critical_friction_velocity, out):
        found = 0
        for n in range(status.size):
            if status[n] == on_bottom and friction_velocity[n] >= critical_friction_velocity:
                out[found] = n
                found += 1
        return out[:found]
