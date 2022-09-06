import numpy as np
from oceantracker.util.polygon_util import InsidePolygon
from oceantracker.particle_release_groups.point_release import PointRelease
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, GracefulExitError
from oceantracker.common_info_default_param_dict_templates import default_polygon_dict_params


class PolygonRelease(PointRelease):
    # random polygon release in 2D or 3D

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params(default_polygon_dict_params)
        self.class_doc(description='Release particles at random locations within given polygon. Points chosen are always inside the domain, also inside wet cells unless  allow_release_in_dry_cells is True.')

        # below are not needed for polygons
        self.remove_default_params(['release_radius'])


    def initialize(self):
        # sort out list  polygon from points
        info = self.info
        si= self.shared_info
        points = np.array(self.params['points']).astype(np.float64)

        if points.shape[0] < 3:
            si.case_log.write_msg('For polygon release group  "points" parameter have at least 3 points, given ' + str(points), exception = GracefulExitError)

        self.polygon = InsidePolygon(verticies = points[:,:2])

        info['points'] =  self.polygon.points

        area = self.polygon.get_area()

        if area < 1:
            si.case_log.write_msg('Release group = ' + str(self.info['release_groupID'])
                           + ', a Polygon release, area of polygon is practically zero , cant release particles from polygon as shape badly formed, area =' + str(area), exception = GracefulExitError)

        info['number_released'] = 0
        info['pulse_count'] = 0


    def estimated_total_number_released(self):
        info = self.info
        if info['release_schedule_times'] is None:
            return 0
        else:
            npart = self.params['pulse_size'] * info['release_schedule_times'].shape[0]
            npart = int(npart + max(10, .03 * npart))  # add 3% more
            return npart

    def get_release_location_candidates(self):
        si = self.shared_info
        bounds = self.polygon.polygon_bounds
        xi = np.random.uniform(low=bounds[0], high=bounds[1], size=self.params['pulse_size'])
        yi = np.random.uniform(low=bounds[2], high=bounds[3], size=self.params['pulse_size'])
        xy_candidates = np.stack((xi, yi), axis=1)

        # select those inside polygon and domain
        sel = self.polygon.inside_indices(xy_candidates)
        x = xy_candidates[sel, :]

        if si.hindcast_is3D:
            x  = np.hstack((x, np.zeros((x.shape[0], 1)) ))
            if len(self.params['z_range']) > 0:
                x[:, 2] = np.random.uniform(self.params['z_range'][0], self.params['z_range'][1])

        return x

    def get_number_required(self):
        return self.params['pulse_size']



