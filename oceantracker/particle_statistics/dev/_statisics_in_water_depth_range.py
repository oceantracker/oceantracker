# does gridded and polygon statistics for particles in a depth range
import numpy as np

import oceantracker.particle_statistics.gridded_statistics as gridded_statistics
import oceantracker.particle_statistics.polygon_statistics as polygon_statistics
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from numba import njit

class WaterDepthRangeStats(ParameterBaseClass):
    # methods to add depth range selection merge into basic stats via inheritance
    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({'min_depth': PVC(-1.0e09, float), 'max_water_depth': PVC(1.0e09, float)})

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['water_depth'])


    def select_particles_to_count(self, out):
        # count particles in less than given water depth with status large enough
        part_prop= self.shared_info.classes['particle_properties']


        sel= self.select_depth_range_status(part_prop['status'].used_buffer(),   part_prop['water_depth'].used_buffer(), self.params['min_depth'], self.params['max_water_depth'], out)
        return sel

    @staticmethod
    @njit
    def select_depth_range_status(status, depth,min_depth,max_depth, out):
        nfound = 0
        for n in range(status.shape[0]):
           if  min_depth < depth[n] < max_depth:
                out[nfound] = n
                nfound += 1

        return out[:nfound]


class GriddedStats2D_timeBasedDepthRange(WaterDepthRangeStats, gridded_statistics.GriddedStats2D_timeBased):
    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag' : PVC('stats_gridded_time_depth_range', str)})

class GriddedStats2D_ageBasedDepthRange(WaterDepthRangeStats, gridded_statistics.GriddedStats2D_agedBased):
    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag' : PVC('stats_gridded_age_depth_range', str)})

class PolygonStats2D_timeBasedDepthRange(WaterDepthRangeStats, polygon_statistics.PolygonStats2D_timeBased):
    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag' : PVC('stats_polygon_time_depth_range',str)})

class PolygonStats2D_ageBasedDepthRange(WaterDepthRangeStats, polygon_statistics.PolygonStats2D_ageBased):
    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag' : PVC('stats_polygon_age_depth_range', str)})