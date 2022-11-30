from oceantracker.fields._base_field import UserFieldBase
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC

from numba import njit
import numpy as np

class FrictionVelocity(UserFieldBase):
    def __init__(self):
        super().__init__()
        self.add_default_params({'name': PVC('friction_velocity', str),
                                 'is_time_varying': PVC(True,bool),
                                 'num_components': PVC(1, int),
                                 'is3D': PVC(False,bool)})


    def check_requirements(self):
        si = self.shared_info

        msg_list = self.check_class_required_fields_prop_etc(
            required_fields_list=['water_velocity'],
            required_grid_var_list=['zlevel'],
            requires3D=True)
        return msg_list

    def update(self, buffer_index):
        si = self.shared_info
        grid = si.classes['reader'].grid
        self.calc_fiction_velocity(buffer_index, grid['zlevel'], grid['bottom_cell_index'], si.z0, si.classes['fields']['water_velocity'].data , self.data)

    @staticmethod
    @njit()
    def calc_fiction_velocity(buffer_index, zlevel, bottom_cell_index, z0, water_velocity, out):
        # get friction velocity from bottom cell, if velocity is zero at base of bottom cell
        # based on log layer  u= u_* log(z/z0)/kappa
        for nt in buffer_index:
            for n in np.arange(zlevel.shape[1]): # loop over nodes
                nz1=bottom_cell_index[n]+1
                dz =  zlevel[nt, n, nz1] - zlevel[nt, n, bottom_cell_index[n]] # size of bottom cell
                if dz < z0:
                    out[nt, n, 0, 0]= 0.
                else:
                    speed = np.sqrt(water_velocity[nt, n, nz1, 0]**2 + water_velocity[nt, n, nz1, 1]**2)
                    out[nt, n, 0, 0] = 0.4*speed/np.log((dz+z0)/z0)



