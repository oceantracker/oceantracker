import numpy as np
from oceantracker.particle_properties._base_properties import ParticleProperty
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.particle_properties.util import particle_operations_util


class DistanceTravelled(ParticleProperty):

    def __init__(self):
        super().__init__()
        self.add_default_params({'initial_value': PVC(0., float)})

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['x', 'x_last_good'])


    def initial_setup(self, **kwargs):
        super().initial_setup()
        # shortcuts

    def initial_value_at_birth(self, active):
        # initial age is zero
        self.set_values(0., active)

    def update(self, active):
        # get total distance traveled
        part_prop = self.shared_info.classes['particle_properties']
        # faster in numba?
        dx = part_prop['x'].get_values(active) - part_prop['x_last_good'].get_values(active)
        ds = np.sqrt(np.power(dx[:, 0], 2), np.power(dx[:, 1], 2)).reshape((-1,))

        particle_operations_util.add_values_to(self.data, ds, active)

