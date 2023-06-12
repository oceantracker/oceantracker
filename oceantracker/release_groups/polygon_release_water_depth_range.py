from oceantracker.release_groups.polygon_release import PolygonRelease
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
import numpy as np

class PolygonReleaseWaterDepthRange(PolygonRelease):
    def __init__(self):
        super().__init__()
        self.add_default_params({'min_water_depth' : PVC (-1.0e37,float), 'max_water_depth' : PVC(1.0e37,float)})

    def filter_release_points(self, x, n_cell):

        si = self.shared_info
        fields= si.classes['field_group_manager']
        water_depth = fields.interp_named_field_at_given_locations_and_time('water_depth', x, time=None, n_cell=n_cell)

        sel = np.logical_and(water_depth >= self.params['min_water_depth'],  water_depth <= self.params['max_water_depth'])

        return x[sel,:], n_cell[sel]
