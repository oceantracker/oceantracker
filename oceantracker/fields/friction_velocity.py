from oceantracker.fields._base_field import CustomFieldBase
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.util.numba_util import njitOT
from numba import njit
import numpy as np
from oceantracker.shared_info import shared_info as si



class FrictionVelocity(CustomFieldBase):
    ''''''
    def __init__(self):
        super().__init__()
        self.add_default_params(name=PVC('friction_velocity', str,
                                doc_str='Name to refer to this field internally within code'),
                                 time_varying=PVC(True,bool),
                                 is3D=PVC(False,bool),
                                 requires3D=PVC(True,bool),
                                 is_vector=PVC(False,bool),
                                 )

    def add_required_classes_and_settings(self, settings, reader_builder, msg_logger):
        info = self.info
        hi = reader_builder['hindcast_info']

        if settings['use_bottom_stress']:
            si.add_reader_field('bottom_stress',dict(write_interp_particle_prop_to_tracks_file=False))
            info['mode'] = 4
        else:
            # use near bottom velocity
            vgt = si.vertical_grid_types

            match  hi['vert_grid_type']:
                    case  vgt.Sigma : info['mode'] = 1
                    case  vgt.Slayer: info['mode'] = 2
                    case  vgt.LSC: info['mode'] = 2
                    case vgt.Zfixed: info['mode'] = 3
        pass

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(requires3D=True)



    def update(self, fields,grid,buffer_index):
        info = self.info
        if info['mode'] == 1:
            # sigma model
            self.calc_friction_velocity_Sigma_grid(buffer_index,
                                                   grid['sigma'],
                                                   fields['tide'].data, fields['water_depth'].data,
                                                   fields['water_velocity'].data,
                                                   si.settings.z0, self.data)
        elif info['mode'] == 2:
            # native vertical grid
            self.calc_friction_velocity_from_Slayer_or_LSC_grid(buffer_index, grid['zlevel'],
                                                                grid['bottom_cell_index'],
                                                                si.settings.z0, fields['water_velocity'].data,
                                                                self.data)
        elif info['mode'] == 3:
            self.calc_friction_velocity_fixed_zlevels_grid(buffer_index, grid['z'],
                                            grid['water_depth'],
                                            grid['bottom_cell_index'],
                                            si.settings.z0, fields['water_velocity'].data,
                                            self.data)
        elif info['mode'] == 4:
            self.calc_friction_velocity_from_bottom_stress(buffer_index, fields['bottom_stress'].data,
                                                           si.settings['water_density'], self.data)

    @staticmethod
    @njitOT
    def calc_friction_velocity_from_Slayer_or_LSC_grid(buffer_index, zlevel, bottom_cell_index, z0, water_velocity, out):
        # get friction velocity from bottom cell, if velocity is zero at base of bottom cell
        # based on log layer  u= u_* log(z/z0)/kappa
        for nt in buffer_index:
            for n in np.arange(zlevel.shape[1]): # loop over nodes
                nz1=bottom_cell_index[n]+1
                dz =  zlevel[nt, n, nz1] - zlevel[nt, n, bottom_cell_index[n]] # size of bottom cell

                if dz >  0.2:
                    speed = np.sqrt(water_velocity[nt, n, nz1, 0]**2 + water_velocity[nt, n, nz1, 1]**2)
                    out[nt, n, 0, 0] = 0.4*speed/np.log((dz+z0)/z0)
                else:
                    out[nt, n, 0, 0] = 0.

    @staticmethod
    @njitOT
    def calc_friction_velocity_Sigma_grid(buffer_index, sigma, tide, water_depth,
                                          water_velocity, z0, out):
        # get friction velocity from bottom cell, if velocity is zero at base of bottom cell
        # based on log layer  u= u_* log(z/z0)/kappa
        for nt in buffer_index:
            for n in np.arange(out.shape[1]):  # loop over nodes
                # size of bottom cell from its fraction of the water depth
                twd = abs(tide[nt,n, 0, 0] + water_depth[0, n, 0, 0])
                if twd < 0.1: twd = 0.1
                dz = (sigma[1] - sigma[0]) * twd
                speed = np.sqrt(water_velocity[nt, n, 1, 0] ** 2 + water_velocity[nt, n, 1, 1] ** 2)
                out[nt, n, 0, 0] = 0.4 * speed / np.log((dz + z0) / z0)



    @staticmethod
    @njitOT
    def calc_friction_velocity_fixed_zlevels_grid(buffer_index, z, water_depth,
                                                  bottom_cell_index, z0,
                                                  water_velocity, out):

        # get friction velocity from bottom cell, if velocity is zero at base of bottom cell
        # based on log layer  u= u_* log(z/z0)/kappa

        for nt in buffer_index:
            for n in np.arange(water_velocity.shape[1]): # loop over nodes
                nz1 = bottom_cell_index[n]+1
                dz =  z[nz1] + water_depth[n] # size of bottom cell

                if dz >  0.2:
                    speed = np.sqrt(water_velocity[nt, n, nz1, 0]**2 + water_velocity[nt, n, nz1, 1]**2)
                    out[nt, n, 0, 0] = 0.4*speed/np.log((dz+z0)/z0)
                else:
                    out[nt, n, 0, 0] = 0.

    @staticmethod
    @njitOT
    def calc_friction_velocity_from_bottom_stress(buffer_index, bottom_stress, water_density,  out):
        # get friction velocity from bottom cell, if velocity is zero at base of bottom cell
        # based on log layer  u= u_* log(z/z0)/kappa
        for nt in buffer_index:
            for n in np.arange(out.shape[1]):  # loop over nodes

                stress_mag = np.sqrt(bottom_stress[nt, n, 0, 0] ** 2 + bottom_stress[nt, n, 0, 1] ** 2)
                out[nt, n, 0, 0] = np.sqrt(stress_mag/water_density)