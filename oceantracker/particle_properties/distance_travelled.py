import numpy as np
from oceantracker.particle_properties._base_particle_properties import CustomParticleProperty
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.particle_properties.util import particle_operations_util
from oceantracker.shared_info import shared_info as si
from oceantracker.util.numba_util import njitOT

class DistanceTravelled(CustomParticleProperty):

    def __init__(self):
        super().__init__()
        self.add_default_params( initial_value= PVC(0., float, doc_str='start with zero distance traveled'),
                                 name=PVC('distance_travelled', str,doc_str='Internal name of property') )

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['x', 'x_last_good'])


    def initial_setup(self, **kwargs):
        super().initial_setup()
        # shortcuts

    def initial_value_at_birth(self, active):
        # initial age is zero
        self.set_values(0., active)

    def update(self,n_time_step,time_sec, active):
        # get total distance traveled
        part_prop = si.class_roles.particle_properties

        if si.settings.use_geographic_coords:
            self.distance_from_lon_lat( part_prop['x_last_good'].data,
                                        part_prop['x'].data,
                                        part_prop['degrees_per_meter'].data,
                                        self.data, active)
        else:
            self.distance_from_meters( part_prop['x_last_good'].data,
                                       part_prop['x'].data,
                                       self.data, active)
        pass

    @staticmethod
    @njitOT
    def distance_from_meters(x1, x2, distance, active):
        for n in active:
            s=0.
            for m in range(2):
                s += (x2[n,m] - x1[n,m])**2
            distance[n] += np.sqrt(s)

    @staticmethod
    @njitOT
    def distance_from_lon_lat(x1, x2, degrees_per_meter,distance, active):
        for n in active:
            s = 0.
            for m in range(2):
                s += ((x2[n, m] - x1[n, m])/degrees_per_meter[n,m]) ** 2
            distance[n] += np.sqrt(s)





