from oceantracker.particle_concentrations._base_user_triangle_properties import _BaseTriangleProperties
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from numba import njit
import numpy as np

class  ParticleConcentrations2D(_BaseTriangleProperties):
    def __init__(self):
        super().__init__()
        # set up info/attributes
        self.add_default_params( dict(
        initial_particle_load = PVC(1.0, float, doc_str='initial load of particles on release', units='non-dimensional'),
        load_decay_time_scale = PVC(24 * 3600, float, doc_str='time scale of exponential decay of particle load', units='sec')
        ))

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_grid_var_list=['triangle_area', 'x'],
                                                            required_props_list=['total_water_depth'])
    def set_up_data_buffers(self):
        si = self.shared_info
        grid = si.classes['reader'].grid
        # set up data buffer
        s = (grid['triangles'].shape[0],)

        self.particle_count = np.full(s, 0, dtype=np.int32)
        self.particle_concentration = np.full(s, 0.)
        self.load_concentration = np.full(s, 0.)
        self.data_buffers={} # for other particle prop to get concentrations of

    def set_up_output_file(self):
        super().set_up_output_file()
        # add 2D variables
        nc= self.nc
        nc.create_a_variable('particle_count',['time_dim','triangle_dim'], self.particle_count.dtype, description='count of particles in each triangle at given time')
        nc.create_a_variable('particle_concentration', ['time_dim', 'triangle_dim'], self.particle_concentration.dtype, description='concentration of particles in each triangle at given time in particles per meter cubed')
        nc.create_a_variable('load_concentration', ['time_dim', 'triangle_dim'], self.load_concentration.dtype, description='concentration of  particle load decaying with age in each triangle at given time')

    def write(self, time_sec):
        si = self.shared_info


        self.nc.file_handle['time'][self.time_steps_written] = time_sec
        self.nc.file_handle['particle_count'][self.time_steps_written,...] = self.particle_count[:]
        self.nc.file_handle['particle_concentration'][self.time_steps_written, ...] = self.particle_concentration[:]
        self.nc.file_handle['load_concentration'][self.time_steps_written, ...] = self.load_concentration[:]
        self.time_steps_written += 1

    def update(self, time_sec):
        params= self.params
        si=self.shared_info
        grid = si.classes['reader'].grid
        part_prop =si.classes['particle_properties']

        if not params['update_values_every_time_step'] and abs(time_sec - self.info['time_last_stats_recorded']) < params['update_interval']: return


        sel = self.select_particles_to_count()
        self.calcuate_concentration2D(part_prop['n_cell'].data,
                                      part_prop['total_water_depth'].data,
                                      part_prop['age'].data,
                                      grid['triangle_area'],
                                      self.particle_count,
                                      self.particle_concentration,
                                      self.load_concentration,
                                      params['initial_particle_load'], params['load_decay_time_scale'],

                                      sel)
        if abs(time_sec - self.info['time_last_stats_recorded']) >= params['update_interval']:
            self.write(time_sec)
            self.info['time_last_stats_recorded'] = time_sec

    @staticmethod
    @njit()
    def calcuate_concentration2D(n_cell, total_water_depth, age, triangle_area,particle_count, particle_concentration,
                                 load_concentration, initial_particle_load,load_decay_time_scale,
                                 sel_to_count):
        particle_count[:] = 0
        particle_concentration[:] = 0.
        load_concentration[:] = 0
        for n in sel_to_count:
            c = n_cell[n]
            particle_count[c] += 1
            vol = triangle_area[c] * total_water_depth[n]

            if vol > 1.:  # only calculate  if at least 1 cubic meter
                particle_concentration[c] += 1.0 / vol
                # age decaying load
                load_concentration[c] += initial_particle_load*np.exp( -age[n] / load_decay_time_scale) / vol


