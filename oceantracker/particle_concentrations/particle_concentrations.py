from oceantracker.particle_concentrations._base_user_triangle_properties import _BaseTriangleProperties
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from numba import njit
import numpy as np

class  ParticleConcentrations2D(_BaseTriangleProperties):
    def __init__(self):
        super().__init__()
        # set up info/attributes


    def check_requirements(self):
        msg_list =self.check_class_required_fields_properties_grid_vars_and_3D(required_grid_vars=['triangle_area','x'],
                                                                               required_props=['total_water_depth'])
        return msg_list

    def set_up_data_buffers(self):
        si = self.shared_info
        grid = si.classes['reader'].grid
        # set up data buffer
        s = (grid['triangles'].shape[0],)

        self.particle_count = np.full(s, 0, dtype=np.int32)
        self.particle_concentration = np.full(s, 0.)
        self.data_buffers={} # for other particle prop to get concentrations of

    def set_up_output_file(self):
        super().set_up_output_file()
        # add 2D variables
        nc= self.nc
        nc.create_a_variable('particle_count', ['time','face'], dtype=self.particle_count.dtype)
        nc.create_a_variable('particle_concentration', ['time', 'face'], dtype=self.particle_concentration.dtype)

    def update(self,n_buffer, time):
        si=self.shared_info
        grid = si.classes['reader'].grid

        sel = self.select_particles_to_count()
        self.calcuate_concentration2D(si.classes['particle_properties']['n_cell'].data,
                                      si.classes['particle_properties']['total_water_depth'].data,
                                      grid['triangle_area'],
                                       self.particle_count,
                                        self.particle_concentration,  sel)
        self.write(n_buffer, time)
        self.record_time_stats_last_recorded(time)

    @staticmethod
    @njit()
    def calcuate_concentration2D(n_cell, total_water_depth, triangle_area,particle_count, particle_concentration, sel_to_count):
        particle_count[:] = 0
        particle_concentration[:] = 0.
        for n in sel_to_count:
            c = n_cell[n]
            twd= total_water_depth[n]
            vol = triangle_area[c] * twd
            if vol > .1:  # only calculate  if at least .1 cubic meter
                particle_count[c] += 1
                particle_concentration[c] += 1.0 / vol


