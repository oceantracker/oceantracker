from oceantracker.release_groups.polygon_release import PolygonRelease
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
import numpy as np

class PolygonReleaseWaterDepthRange(PolygonRelease):
    def __init__(self):
        super().__init__()
        self.add_default_params({'water_depth_min' : PVC (-1.0e37,float),
                                 'water_depth_max' : PVC(1.0e37,float)})

    def filter_release_points(self, is_inside, release_part_prop, time_sec= None):

        water_depth =release_part_prop['water_depth']

        sel = np.logical_and(water_depth >= self.params['water_depth_min'],  water_depth <= self.params['water_depth_max'])
        is_inside = np.logical_and(sel, is_inside)
        return is_inside, release_part_prop
