import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.tracks_writer._base_tracks_writer import  _BaseWriter
from oceantracker.util import  output_util
from oceantracker.util import numpy_util
from oceantracker.shared_info import shared_info as si

class RectangularTracksWriter(_BaseWriter):
    '''
    Writes particle tracks with particle properties written with dims (time, particle,..)
    Is very slow writing, better to use post run conversion!!
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
        nc.create_dimension(si.dim_names.time, None)
        nc.create_dimension(si.dim_names.vector2D, 2)
        nc.create_dimension(si.dim_names.vector3D, 3)
        nc.create_dimension(si.dim_names.particle, None)

        nc.create_variable('alive_particles', si.dim_names.time, dtype=np.int32,
                           chunksizes=[params['particle_chunk']],
                           description='Number of particles written each time step')

        vi = info['variables_to_write']
        for name, i in si.class_roles.time_varying_info.items():
            if not i.params['write']: continue
            nc.create_variable(name, si.dim_names.time, units=i.params['units'], dtype=i.params['dtype'],
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
                dim.append(nc.create_dimension(f'part_prop_{name}_dim3', i.params['prop_dim3']))
                chunking.append(i.params['prop_dim3'])

            nc.create_variable(name, dim, units=i.params['units'], dtype=i.params['dtype'],
                               chunksizes=chunking,
                               description=i.params['description'],
                               compression_level=si.settings.NCDF_compression_level)

        if si.settings.write_dry_cell_flag:
            grid = si.core_class_roles.field_group_manager.reader.grid
            nc.create_dimension(si.dim_names.triangle, grid['triangles'].shape[0])
            nc.create_variable('dry_cell_index', [si.dim_names.time, si.dim_names.triangle], dtype=np.uint8,
                               chunksizes=[params['time_chunk'],grid['triangles'].shape[0]],
                               description= 'Time series of grid dry index 0-255, > 128 is dry', compression_level=si.settings.NCDF_compression_level, )
            pass

    def pre_time_step_write_book_keeping(self):
        info = self.info
        nc = self.nc
        nWrite = info['time_steps_written_to_current_file']

        self.part_to_write = self._select_part_to_write()

        nc.file_handle.variables['alive_particles'][nWrite] = self.part_to_write.shape[0]
        info['time_particle_steps_written'] += self.part_to_write.shape[0]

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
        IDs= part_prop['ID'].get_values(self.part_to_write)
        offsets = IDs - info['first_ID_in_file']

        for name in info['variables_to_write']['time_varying_part_prop']:
            offset_range, b = self._get_part_prop_buffer( part_prop[name].data,self.part_to_write, IDs, info['first_ID_in_file'])
            nc.file_handle.variables[name][nt, offset_range[0]:offset_range[1], ...] = b
           #nc.file_handle.variables[name][nt, offsets, ...] = part_prop[name].data[self.part_to_write, ...]

        if si.settings.write_dry_cell_flag:
            # wont run if nested grids
            grid = si.core_class_roles.field_group_manager.reader.grid
            nc.file_handle.variables['dry_cell_index'][info['time_steps_written_to_current_file'], :] = grid['dry_cell_index'].reshape(1, -1)

        self.post_time_step_write_book_keeping()

        info['time_steps_written_to_current_file'] += 1  # time steps in current file
        self.info['total_time_steps_written'] += 1  # time steps written since the start

    def _get_part_prop_buffer(self, data, part_to_write,IDs, ID_file0):
        # write one time step
        # fill a buffer with full set of values, including those dead/not written
        IDrange= np.asarray([IDs[0],IDs[-1]+1])
        s= list(data.shape)
        s[0] = IDrange[1] - IDrange[0]
        b =np.full(s, numpy_util.smallest_value(data.dtype),dtype=data.dtype)

        b[IDs-IDs[0],...] = data[part_to_write,...]
        offset_range= IDrange - ID_file0
        return offset_range, b




