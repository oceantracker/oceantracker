from oceantracker.particle_concentrations._base_user_triangle_properties import BaseTriangleProperties
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from numba import njit
import numpy as np

class  ParticleConcentrations2D(BaseTriangleProperties):
    def __init__(self):
        super().__init__()
        # set up info/attributes


    def check_requirements(self):
        msg_list =self.check_class_required_fields_properties_grid_vars_and_3D(required_grid_vars=['triangle_area','x'],
                                                                               required_fields=['total_water_depth'])
        return msg_list

    def set_up_data_buffers(self):
        si = self.shared_info
        # set up data buffer
        s = (si.grid['triangles'].shape[0],)

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
        sel = self.select_particles_to_count()
        self.calcuate_concentration2D(n_buffer, si.classes['particle_properties']['n_cell'].data,
                                      si.classes['fields']['total_water_depth'].data,
                                      si.grid['triangles'],
                                      si.grid['triangle_area'],
                                       self.particle_count,
                                        self.particle_concentration,  sel)
        self.write(n_buffer, time)
        self.record_time_stats_last_recorded(time)

    @staticmethod
    @njit()
    def calcuate_concentration2D(n_buffer, n_cell, total_water_depth, triangles, triangle_area,particle_count, particle_concentration, sel_to_count):
        particle_count[:] = 0
        particle_concentration[:] = 0.
        for n in sel_to_count:
            c = n_cell[n]
            tri = triangles[c, :]
            # get triangle height fom mean of nodal/field values
            twd= total_water_depth[n_buffer, :, 0, 0]
            triangle_total_water_depth = np.nanmean(twd[tri])
            vol = triangle_area[c] * triangle_total_water_depth
            if vol > .1:  # only calculate  if at least .1 cubic meter
                particle_count[c] += 1
                particle_concentration[c] += 1.0 / vol


