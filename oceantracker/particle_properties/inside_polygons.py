from oceantracker.particle_properties._base_particle_properties import ManuallyUpdatedParticleProperty
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.util.polygon_util import set_up_list_of_polygon_instances, find_overlapping_polygons, InsideWhichPolygon

from oceantracker.shared_info import shared_info as si

class InsidePolygonsNonOverlapping2D(ManuallyUpdatedParticleProperty):
    '''
    particle property giving ID of 2D polygon which particle is inside. -1 if in no polygon
    polygons must not overlap, a fatal error is raised at setup if they overlap more than a small tolerance,
    particles in any remaining tiny overlap are "inside" the first polygon in polygon_list containing them
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
        self.inside_which_polygon = InsideWhichPolygon(self.polygons)

        names = [p.get('name') if p.get('name') is not None else n for n, p in enumerate(self.params['polygon_list'])]
        overlaps = find_overlapping_polygons(self.polygons, names)
        if len(overlaps) > 0:
            si.msg_logger.msg(f'Overlapping polygons in polygon_list: {", ".join(overlaps)}',
                              hint='Polygons used for polygon statistics or polygon entry/exit events must not overlap, as particles in an overlap would only be counted in the last of these polygons in polygon_list',
                              caller=self, fatal_error=True)

    def update(self,n_time_step, time_sec, active):
        # find polygon each particle is inside, -1 if in none,
        # assumes non-overlapping polygons, ie so only inside one at a time
        part_prop = si.class_roles.particle_properties
        self.inside_which_polygon.find(part_prop['x'].used_buffer(), active, self.data)

