from oceantracker.fields._base_field import UserFieldBase
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from numba import njit
import numpy as np
from oceantracker.particle_properties._base_properties import ParticleProperty
class FrictionVelocity(ParticleProperty):

    # friction velocity field from depth averaged  velocity at the nodes

    def __init__(self):
        super().__init__()
        self.add_default_params({'name': PVC('friction_velocity', str), 'initial_value': PVC(0., float)})

    def check_requirements(self):
        msg_list = self.check_class_required_fields_properties_grid_vars_and_3D(
                            required_props=['water_velocity_depth_average', 'total_water_depth'],
                            requires3D=True)
        return msg_list

    def update(self, active):
        si = self.shared_info
        part_prop=si.classes['particle_properties']
        self.friction_velocity_at_nodes_from_depth_average_velocity(active,
                                    part_prop['water_velocity_depth_average'].data,
                                    part_prop['total_water_depth'].data,
                                    si.run_params['z0'], self.data)
        a=1
    @staticmethod
    @njit
    def friction_velocity_at_nodes_from_depth_average_velocity(active,water_velocity_depth_averaged, total_water_depth, z0, out):
        # get friction velocity at nodes from depth_average_velocity
        kappa = 0.4 # von Karmen's kappa
        # wolfram integrate integrate log(x/z0) =  integral_z0^h log(z/z0)/h dz =  log(h/z0) -1+ z0/h
        # gives
        #       u_friction= kappa*h*speed_depthAv./I2(waterDepth);
        #           where I2=@(h) z0./h + log(h/z0)-1;
        for n in active:
            h = total_water_depth[n]
            if h > 2.0*z0 :  # use 2*z0, to avoid possibility if h at precision is > z0, but which gives  I2=0 in calculation below, leading to division by zero error
                I2 =  np.log(h/z0) - 1. + z0/h
                out[n] = kappa * np.sqrt(water_velocity_depth_averaged[n, 0] ** 2 + water_velocity_depth_averaged[n, 1] ** 2) / I2
            else:
                out[n] = np.inf # thin layer so make it stick






