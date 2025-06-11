import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.tracks_writer._base_tracks_writer import  _BaseWriter
from oceantracker.util import  output_util


from oceantracker.shared_info import shared_info as si

class CompactTracksWriter(_BaseWriter):
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaultsults

        self.add_default_params({
                    'NCDF_time_chunk': PVC(None,int, obsolete=True, doc_str=' Use main setting with same name'),
                    'NCDF_particle_chunk': PVC(None, int, obsolete=True, doc_str=' Use main setting with same name'),
                    #'convert': PVC(False, bool, doc_str='convert compact tracks file to rectangular for at end of the run'),
                    #'retain_compact_files': PVC(False, bool,  doc_str='keep  compact tracks files after conversion to rectangular format'),
                    'role_output_file_tag': PVC('tracks_compact', str, expert=True),
                                 })
        self.nc = None

    def initial_setup(self):
        super().initial_setup()
        self.info['time_particle_steps_written'] = 0

    def setup_file_vars(self, nc):
        info= self.info

        nc.add_dimension(si.dim_names.time, None)
        nc.add_dimension(si.dim_names.vector2D, 2)
        nc.add_dimension(si.dim_names.vector3D, 3)
        nc.add_dimension(si.dim_names.particle, None)
        nc.add_dimension('time_particle_dim', None)
        nc.add_dimension('range_pair_dim', 2)


        nc.create_a_variable('particles_written_per_time_step',si.dim_names.time,dtype=np.int32,
                             description='Number of particles written each time step')
        nc.create_a_variable('particle_ID', 'time_particle_dim', dtype=np.int32,compression_level=si.settings.NCDF_compression_level,
                             description='ID number of of particle recorded ')
        nc.create_a_variable('write_step_index', 'time_particle_dim', dtype=np.int32,compression_level=si.settings.NCDF_compression_level,
                             description='Time/write step of particle recorded ')
        # variable to give index ranges of time steps within output
        nc.create_a_variable('time_step_range', ['time_dim','range_pair_dim'],dtype=np.int32,
                              description='range in time_particle_dim for each time step, could be used to unpack')

        vi = info['variables_to_write']
        for name, i in si.class_roles.time_varying_info.items():
            if not i.params['write']: continue
            nc.create_a_variable(name,si.dim_names.time,units=i.params['units'],dtype=i.params['dtype'],
                                  description=i.params['description'])
            vi['time_varying_info'].append(name)

        for name, i in si.class_roles.particle_properties.items():
            if not i.params['write']: continue
            dim =[]
            if i.params['time_varying']:
                dim.append('time_particle_dim')
                vi['time_varying_part_prop'].append(name)
                comp = si.settings.NCDF_compression_level
            else:
                dim.append('particle_dim')
                vi['non_time_varying_part_prop'].append(name)
                comp = 0

            if i.params['vector_dim'] == 2: dim.append(si.dim_names.vector2D)
            if i.params['vector_dim'] == 3: dim.append(si.dim_names.vector3D)
            if i.params['prop_dim3'] > 1: dim.append(nc.add_dimension(f'part_prop_{name}_dim3', i.params['prop_dim3']))

            nc.create_a_variable(name, dim, units=i.params['units'],dtype=i.params['dtype'],
                                  description=i.params['description'],compression_level=comp)

        if si.settings['write_dry_cell_flag']:
            grid = si.core_class_roles.field_group_manager.reader.grid
            nc.add_dimension(si.dim_names.triangle, grid['triangles'].shape[0])
            nc.create_a_variable('dry_cell_index', [si.dim_names.time,si.dim_names.triangle],dtype=np.uint8,
                                  description= 'Time series of grid dry index 0-255, > 128 is dry',compression_level=si.settings.NCDF_compression_level,)
            pass
    def pre_time_step_write_book_keeping(self):
        # write indexing variables
        #todo change to write particle shared_params when culling ?
        info = self.info
        nc = self.nc
        nWrite = info['time_steps_written_to_current_file']
        self.sel_alive = si.class_roles.particle_properties['status'].compare_all_to_a_value('gt', si.particle_status_flags.dead, out= self.get_partID_buffer('B1'))

        n_file = self.nc.var_shape('particle_ID')[0]

        self.file_index = [n_file, n_file + self.sel_alive.shape[0]]
        fi = self.file_index
        # record range if time step in time_particle dim
        nc.file_handle.variables['time_step_range'][nWrite,:] = np.asarray(fi)
        nc.file_handle.variables['particles_written_per_time_step'][nWrite] =  self.sel_alive.shape[0]

        nc.file_handle.variables['particle_ID'][fi[0]:fi[1], ...] = si.class_roles.particle_properties['ID'].get_values(self.sel_alive)

        nc.file_handle.variables['write_step_index'][fi[0]:fi[1], ...] = info['total_time_steps_written'] * np.ones((self.sel_alive.shape[0],), dtype=np.int32)

        self.info['time_particle_steps_written'] += self.sel_alive.shape[0]
    def write_all_non_time_varing_part_properties(self, new_particleIDs):
        # to work in compact mode must write particle non-time varying  particle properties when released
        #  eg ID etc, releaseGroupID  etc

        info = self.info
        nc = self.nc
        n_in_file = self.nc.var_shape('ID')[0]
        n_write = range(n_in_file, n_in_file + new_particleIDs.size)

        part_prop = si.class_roles.particle_properties
        if new_particleIDs.size > 0:
            for name in info['variables_to_write']['non_time_varying_part_prop']:
                nc.file_handle.variables[name][n_write, ...] = part_prop[name].data[new_particleIDs, ...]

    def write_all_time_varying_prop_and_data(self):
        # write particle data at current time step, if none then a forced write
        # write time vary info , eg "time"
        self.start_update_timer()
        info = self.info
        part_prop = si.class_roles.particle_properties
        time_varying_info = si.class_roles.time_varying_info
        self.pre_time_step_write_book_keeping()
        nc = self.nc

        # write time varying data, eg time  data
        for name in info['variables_to_write']['time_varying_info']:
            nc.file_handle.variables[name][info['time_steps_written_to_current_file'], ...] = time_varying_info[name].data[:]

        for name in info['variables_to_write']['time_varying_part_prop']:
            nc.file_handle.variables[name][self.file_index[0]:self.file_index[1], ...] = part_prop[name].data[self.sel_alive, ...]

        if si.settings['write_dry_cell_flag']:
            # wont run if nested grids
            grid = si.core_class_roles.field_group_manager.reader.grid
            nc.file_handle.variables['dry_cell_index'][info['time_steps_written_to_current_file'], :] = grid['dry_cell_index'].reshape(1, -1)

        self.post_time_step_write_book_keeping()

        info['time_steps_written_to_current_file'] += 1  # time steps in current file
        self.info['total_time_steps_written'] += 1  # time steps written since the start
        self.stop_update_timer()

    def _close_file(self):
        nc = self.nc
        nc.write_global_attribute('total_num_particles_released', si.core_class_roles.particle_group_manager.info['particles_released'])
        nc.write_global_attribute('time_steps_written', self.info['time_steps_written_to_current_file'])

        # write status values to  file attribues
        output_util.add_particle_status_values_to_netcdf(nc)

        super()._close_file()




