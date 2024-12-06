import numpy as np
from oceantracker.util.polygon_util import InsidePolygon
from oceantracker.util import   cord_transforms
from oceantracker.release_groups.point_release import PointRelease
from oceantracker.shared_info import shared_info as si

class PolygonRelease(PointRelease):
    '''
    Release particles at random locations within given polygon.
    Points chosen are always inside the domain, also inside wet cells unless setting allow_release_in_dry_cells is True.
    '''

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params(si.default_polygon_dict_params)


        # below are not needed for polygons
        self.remove_default_params(['release_radius'])


    def initial_setup(self):
        # sort out list  polygon from points
        info = self.info
        params= self.params
        ml = si.msg_logger
        if params['points'].shape[0] < 3:
            ml.msg('"points" parameter have at least 3 points, given ' + str(params['points']), fatal_error=True, caller=self)

        # ensure points are  meters
        if si.settings.use_geographic_coords:
            params['points'] = cord_transforms.fix_any_spanning180east(params['points'], msg_logger=si.msg_logger, caller=self,
                                                       crumbs=f'Point release#{params["name"]}')
        info['release_type'] = 'polygon'
        info['bounding_box_ll_ul'] = np.stack((np.nanmin(params['points'][:,:2], axis=0),
                                               np.nanmax(params['points'][:,:2], axis=0)))

        self.polygon = InsidePolygon(verticies = params['points'], geographic_coords=si.settings.use_geographic_coords)
        info['polygon_area'] = self.polygon.get_area()
        ll, ur = info['bounding_box_ll_ul']
        info['bounding_box_area'] = abs((ur[0] - ll[0]) * (ur[1] - ll[1]))

        if info['polygon_area']  < 10:
            ml.msg('Polygon release, area of polygon is < 10 sq meters , area =' + str(info['polygon_area']),
                   hint='Is hydro model grid in meters and polygon coords given in (lon, lat)  degrees, convert polygons to hydro models meters coords? ',
                   warning=True)

        info['number_released'] = 0
        info['pulseID'] = 0


    def get_release_location_candidates(self):
        info = self.info
        ll, ur = info['bounding_box_ll_ul']
        # find number required to have one guess get all required points
        # by scaling by fraction of bounding box polygon takes up
        n_candidates = int(np.ceil(self.params['pulse_size']*info['bounding_box_area']/ info['polygon_area'] ))

        xi = np.random.uniform(low=ll[0], high=ur[0], size=n_candidates)
        yi = np.random.uniform(low=ll[1], high=ur[1], size=n_candidates)
        xy_candidates = np.stack((xi, yi), axis=1)

        # select those inside polygon and domain
        sel = self.polygon.inside_indices(xy_candidates)
        x = xy_candidates[sel, :]
        return x

    def get_number_required(self):
        return self.params['pulse_size']



