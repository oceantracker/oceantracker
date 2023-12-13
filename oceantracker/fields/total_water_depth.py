from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from numba import njit
import numpy as np
from oceantracker.fields._base_field import CustomFieldBase
class TotalWaterDepth(CustomFieldBase):
    def __init__(self):
        super().__init__()
        self.add_default_params({'time_varying': PVC(True,bool),
                                 'is_vector': PVC(False, bool),
                                 'write_interp_particle_prop_to_tracks_file' :  PVC(False, bool),
                                 'is3D': PVC(False,bool)})

    def check_requirements(self):
        si = self.shared_info
        self.check_class_required_fields_prop_etc(required_fields_list=['tide'])

    def update(self,active):
        si = self.shared_info
        fields= si.classes['fields']
        grid = si.classes['reader'].grid

        self.get_time_dependent_total_water_depth_from_tide_and_water_depth(
                fields['tide'].data,
                fields['water_depth'].data.ravel(),
                si.minimum_total_water_depth,
                self.data)

    @staticmethod
    @njit()
    def get_time_dependent_total_water_depth_from_tide_and_water_depth(tide, water_depth,
                                                                       min_total_water_depth, total_water_depth):
        # get total time dependent water depth as 4D field  from top and bottom cell of LSC grid zlevels
        for nt in range(tide.shape[0]):
            for node in range(tide.shape[1]):
                d = tide[nt, node,0,0] + water_depth[node]
                if  d < min_total_water_depth:
                    d= min_total_water_depth
                total_water_depth[nt, node, 0, 0] = d