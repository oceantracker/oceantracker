from oceantracker.release_groups.polygon_release import PolygonRelease
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
import numpy as np

class PolygonReleaseWaterDepthRange(PolygonRelease):
    def __init__(self):
        super().__init__()
        self.add_default_params({'water_depth_min' : PVC (-1.0e37,float),
                                 'water_depth_max' : PVC(1.0e37,float)})

    def filter_release_points(self, x, n_cell):

        si = self.shared_info
        fgm= si.classes['field_group_manager']
        water_depth = fgm.interp_named_field_at_given_locations_and_time('water_depth', x, time_sec=None, n_cell=n_cell)

        sel = np.logical_and(water_depth >= self.params['water_depth_min'],  water_depth <= self.params['water_depth_max'])

        return x[sel,:], n_cell[sel]
