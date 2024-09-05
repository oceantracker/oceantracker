from oceantracker.particle_properties._base_particle_properties import CustomParticleProperty
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.polygon_util import set_up_list_of_polygon_instances, InsidePolygon

from oceantracker.shared_info import shared_info as si

class InsidePolygonsNonOverlapping2D(CustomParticleProperty):
    '''
    particle property giving ID of 2D polygon which particle is inside. -1 if in no polygon
    assumes non-overlapping polygons, ie so only inside one at a time, ie the first it is found inside,
    does not check if polygons overlap
    '''
    def __init__(self):
        super().__init__()
        self.add_default_params({'initial_value': PVC(-1, int),
                                 'dtype':PVC('int32',str)})

        self.add_default_params({'polygon_list':[]})

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['x'])

    def initial_setup(self, **kwargs):
        super().initial_setup()
        # set up polygons instances

        self.polygons, msg = set_up_list_of_polygon_instances(self.params['polygon_list'])

    def update(self,n_time_step, time_sec, active):
        # find polygon each particle is inside
        part_prop = si.class_roles.particle_properties

        # make all inside no polyg
        self.set_values(-1, active)

        # loop over polygons
        # faster if those already found to be inside previously polygon are eliminated
        to_search = active # for first polygon search all those IDs which are active

        for n, poly in enumerate(self.polygons):
            # assumes non-overlapping polygons, ie so only inside one at a time, the first polygon it is inside
            inside, out_side = poly.inside_indices(part_prop['x'].used_buffer(), active=to_search, out=self.get_partID_buffer('B1'),
                                                   also_return_indices_outside=True, out_outside=self.get_partID_subset_buffer('B1'))
            self.set_values(n, inside)
            to_search = out_side # on next polygon only search those not in precceding polygons

