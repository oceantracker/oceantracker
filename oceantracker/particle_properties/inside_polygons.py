from oceantracker.particle_properties._base_particle_properties import ManuallyUpdatedParticleProperty
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.util.polygon_util import set_up_list_of_polygon_instances

from oceantracker.shared_info import shared_info as si

class InsidePolygonsNonOverlapping2D(ManuallyUpdatedParticleProperty):
    '''
    particle property giving ID of 2D polygon which particle is inside. -1 if in no polygon
    assumes non-overlapping polygons, ie does not check if polygons overlap.
    If they are overlapping particles are "inside" the last polygon that was checked in which they are contained
    '''
    def __init__(self):
        super().__init__()
        self.add_default_params({'initial_value': PVC(-1, int),
                                 'dtype':PVC('int32',str)})

        self.add_default_params({'polygon_list':[]})

    def initial_setup(self, **kwargs):
        super().initial_setup()
        # set up polygons instances

        self.polygons, msg = set_up_list_of_polygon_instances(self.params['polygon_list'], geographic_coords=si.settings.use_geographic_coords)

    def update(self,n_time_step, time_sec, active):
        # find polygon each particle is inside
        part_prop = si.class_roles.particle_properties
        # make all inside no polyg
        self.set_values(-1, active)

        for n, poly in enumerate(self.polygons):
            # assumes non-overlapping polygons, ie so only inside one at a time, the first polygon it is inside
            inside = poly.inside_indices(part_prop['x'].used_buffer(), active=active, out=self.get_partID_buffer('B1'))
            self.set_values(n, inside)

