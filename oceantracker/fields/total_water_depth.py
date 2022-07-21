from oceantracker.fields._base_field import UserFieldBase
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from oceantracker.util.parameter_checking import append_message
from numba import njit
import numpy as np

class TotalWaterDepth(UserFieldBase):
    def __int__(self):
        super().__init__()
        self.add_default_params({'name': PVC('total_water_depth', str),
                                 'is_time_varying': PVC(True,bool)})
        a=1

    def check_requirements(self):
        si = self.shared_info
        msg_list=[]
        #msg_list = self.check_class_required_fields_properties_grid_vars_and_3D()
        if si.grid['zlevel'] is None and ('tides' not in si.classes['fields'] and  'water_depth' not in si.classes['fields']) :
            msg_list = append_message(msg_list,' zlevel, or tide and water depth required for total water depth, ', crumbs='TotalWaterDepth')
        return msg_list

    def update(self,buffer_index):
        si = self.shared_info
        if si.grid['zlevel'] is None:
            # from tide
           self.get_time_dependent_total_water_depth_from_tide_and_water_depth(buffer_index,
                    si.classes['fields']['tide'].data,
                    si.classes['fields']['water_depth'].data,
                    self.data)
        else:
            self.get_time_dependent_total_water_depth_from_zlevel(buffer_index, si.grid['zlevel'],
                                                            si.grid['bottom_cell_index'],  self.data)
    @staticmethod
    @njit()
    def get_time_dependent_total_water_depth_from_zlevel(buffer_index, zlevel, bottom_cell_index, out):
        # get total time dependent water depth as 4D field  from top and bottom cell of LSC grid zlevels
        for nt in buffer_index:
            for n in np.arange(zlevel.shape[1]):
                out[nt, n] = zlevel[nt, n, -1] - zlevel[nt, n, bottom_cell_index[n]]

    @staticmethod
    @njit()
    def get_time_dependent_total_water_depth_from_tide_and_water_depth(buffer_index, tide, water_depth, out):
        # get total time dependent water depth as 4D field  from top and bottom cell of LSC grid zlevels
        for nt in buffer_index:
            for n in np.arange(tide.shape[1]):
                out[nt, n, 0, 0] = tide[nt, n, 0, 0] + water_depth[0, n, 0, 0]