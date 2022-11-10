import numpy as np
from oceantracker.particle_properties._base_properties import ParticleProperty
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC

class DistanceTravelled(ParticleProperty):

    def __init__(self):
        super().__init__()
        self.add_default_params({'name': PVC('distance_travelled', str), 'initial_value': PVC(0., float)})

    def check_requirements(self):
        msg_list = self.check_class_required_fields_list_properties_grid_vars_and_3D(required_props_list=['x', 'x_last_good'])
        return msg_list

    def initialize(self,**kwargs):
        super().initialize()
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
        self.add_values_to(ds, active)

