import numpy as np
from oceantracker.util.polygon_util import InsidePolygon
from oceantracker.release_groups.point_release import PointRelease
from oceantracker.common_info_default_param_dict_templates import default_polygon_dict_params

class PolygonRelease(PointRelease):
    # random polygon release in 2D or 3D

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params(default_polygon_dict_params)

        self.class_doc('Release particles at random locations within given polygon. Points chosen are always inside the domain, also inside wet cells unless  allow_release_in_dry_cells is True.')

        # below are not needed for polygons
        self.remove_default_params(['release_radius'])


    def initial_setup(self):
        # sort out list  polygon from points
        info = self.info
        si= self.shared_info
        params= self.params
        ml = si.msg_logger
        if params['points'].shape[0] < 3:
            ml.msg('"points" parameter have at least 3 points, given ' + str(params['points']), fatal_error=True, caller=self)

        # ensure points are  meters
        if si.hydro_model_cords_in_lat_long:
            params['points_lon_lat'] = params['points'].copy()
            params['points'] = si.transform_lon_lat_to_meters(params['points_lon_lat'],
                                        in_lat_lon_order=self.params['coords_allowed_in_lat_lon_order'],
                                       crumbs=f'Polygon release {self.IDstr()}')
        info['release_type'] = 'polygon'

        self.polygon = InsidePolygon(verticies = params['points'])

        info['polygon_area'] = self.polygon.get_area()
        b = self.polygon.polygon_bounds
        info['bounding_box_area'] = (b[1]-b[0]) * (b[3]-b[2])

        if info['polygon_area']  < 1:
            ml.msg('Polygon release, area of polygon is practically zero , cant release particles from polygon as shape badly formed, area =' + str(info['polygon_area']), fatal_error=True)

        info['number_released'] = 0
        info['pulseID'] = 0


    def get_release_location_candidates(self):
        si = self.shared_info
        info = self.info
        bounds = self.polygon.polygon_bounds

        # find number required to have one guess get all required points
        # by scaling by fraction of bounding box polygon takes up
        n_candidates = int(np.ceil(self.params['pulse_size']*info['bounding_box_area']/ info['polygon_area'] ))

        xi = np.random.uniform(low=bounds[0], high=bounds[1], size=n_candidates)
        yi = np.random.uniform(low=bounds[2], high=bounds[3], size=n_candidates)
        xy_candidates = np.stack((xi, yi), axis=1)

        # select those inside polygon and domain
        sel = self.polygon.inside_indices(xy_candidates)

        x = xy_candidates[sel, :]

        return x

    def get_number_required(self):
        return self.params['pulse_size']



