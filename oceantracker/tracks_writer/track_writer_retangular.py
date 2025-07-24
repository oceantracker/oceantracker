import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.tracks_writer._base_tracks_writer import  _BaseWriter
from oceantracker.util import  output_util


from oceantracker.shared_info import shared_info as si

class RectangularTracksWriter(_BaseWriter):
    '''
    Writes particle tracks with particle properties written with dims (time, particle,..)
    '''
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaultsults

        self.add_default_params(
            particle_chunk =  PVC(None, int, min=1,  expert=True,
                          doc_str='Netcdf chunk size of particle dim,  default is as estimated from forecasted max. particles alive'),
            time_chunk=PVC(1, int, min=1, expert=True, doc_str='Netcdf chunk size of time dim'),
            role_output_file_tag=PVC('tracks_rectangular', str, expert=True),
                )
        self.nc = None


    def initial_setup(self):
        super().initial_setup()
        info=self.info
        info['time_particle_steps_written'] = 0


        params = self.params
        if params['particle_chunk'] is None:
            params['particle_chunk'] = int(si.run_info.forecasted_max_number_alive/10)

        self.dim_sizes = dict()
    def setup_file_vars(self, nc):
        info= self.info
        params = self.params
        nc.add_dimension(si.dim_names.time, None)
        nc.add_dimension(si.dim_names.vector2D, 2)
        nc.add_dimension(si.dim_names.vector3D, 3)
        nc.add_dimension(si.dim_names.particle, None)

        nc.create_a_variable('alive_particles',si.dim_names.time,dtype=np.int32,
                             chunksizes=[params['particle_chunk']],
                             description='Number of particles written each time step')

        vi = info['variables_to_write']
        for name, i in si.class_roles.time_varying_info.items():
            if not i.params['write']: continue
            nc.create_a_variable(name,si.dim_names.time,units=i.params['units'],dtype=i.params['dtype'],
                                  chunksizes= [params['time_chunk']],
                                  description=i.params['description'])
            vi['time_varying_info'].append(name)

        for name, i in si.class_roles.particle_properties.items():
            if not i.params['write']: continue
            dim =[]
            if i.params['time_varying']:
                dim += [si.dim_names.time,si.dim_names.particle]
                vi['time_varying_part_prop'].append(name)
                chunking = [params['time_chunk'],params['particle_chunk']]
            else:
                dim.append('particle_dim')
                vi['non_time_varying_part_prop'].append(name)
                chunking = [params['time_chunk']]

            if i.params['vector_dim'] == 2:
                dim.append(si.dim_names.vector2D)
                chunking.append(2)
            elif i.params['vector_dim'] == 3:
                dim.append(si.dim_names.vector3D)
                chunking.append(3)
            if i.params['prop_dim3'] > 1:
                dim.append(nc.add_dimension(f'part_prop_{name}_dim3', i.params['prop_dim3']))
                chunking.append(i.params['prop_dim3'])

            nc.create_a_variable(name, dim, units=i.params['units'],dtype=i.params['dtype'],
                    chunksizes=chunking,
                    description=i.params['description'],
                    compression_level=si.settings.NCDF_compression_level)

        if si.settings['write_dry_cell_flag']:
            grid = si.core_class_roles.field_group_manager.reader.grid
            nc.add_dimension(si.dim_names.triangle, grid['triangles'].shape[0])
            nc.create_a_variable('dry_cell_index', [si.dim_names.time,si.dim_names.triangle],dtype=np.uint8,
                    chunksizes=[params['time_chunk'],grid['triangles'].shape[0]],
                    description= 'Time series of grid dry index 0-255, > 128 is dry',compression_level=si.settings.NCDF_compression_level,)
            pass

    def pre_time_step_write_book_keeping(self):
        info = self.info
        nc = self.nc
        nWrite = info['time_steps_written_to_current_file']

        self.sel_alive = self._select_part_to_write()

        # record range if time step in time_particle dim
        nc.file_handle.variables['alive_particles'][nWrite] = self.sel_alive.shape[0]
        info['time_particle_steps_written'] += self.sel_alive.shape[0]

    def write_all_non_time_varing_part_properties(self, new_particle_indices):
        # write info about partciles when relaase, eg IDs in file
        info = self.info
        nc = self.nc
        part_prop = si.class_roles.particle_properties
        IDs = part_prop['ID'].get_values(new_particle_indices)
        ID0 = info['first_ID_in_file']
        if new_particle_indices.size > 0:
            for name in info['variables_to_write']['non_time_varying_part_prop']:
                nc.file_handle.variables[name][IDs - ID0, ...] = part_prop[name].data[new_particle_indices, ...]

    def write_all_time_varying_prop_and_data(self):
        # write particle data at current time step, if none then a forced write
        # write time vary info , eg "time"
        info = self.info
        part_prop = si.class_roles.particle_properties
        time_varying_info = si.class_roles.time_varying_info
        self.pre_time_step_write_book_keeping()
        nc = self.nc
        nt = info['time_steps_written_to_current_file']

        # write time varying data, eg time  data
        for name in info['variables_to_write']['time_varying_info']:
            nc.file_handle.variables[name][nt, ...] = time_varying_info[name].data[:]
        IDs= part_prop['ID'].get_values(self.sel_alive)
        offsets = IDs - info['first_ID_in_file']

        for name in info['variables_to_write']['time_varying_part_prop']:
           nc.file_handle.variables[name][nt, offsets, ...] = part_prop[name].data[self.sel_alive, ...]

        if si.settings['write_dry_cell_flag']:
            # wont run if nested grids
            grid = si.core_class_roles.field_group_manager.reader.grid
            nc.file_handle.variables['dry_cell_index'][info['time_steps_written_to_current_file'], :] = grid['dry_cell_index'].reshape(1, -1)

        self.post_time_step_write_book_keeping()

        info['time_steps_written_to_current_file'] += 1  # time steps in current file
        self.info['total_time_steps_written'] += 1  # time steps written since the start

    def _open_file(self, file_name):
        super()._open_file(file_name)



