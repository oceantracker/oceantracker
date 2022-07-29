import numpy as np
from oceantracker.tracks_writer.track_writer_retangular import RectangularTrackWriter

class FlatTrackWriter(RectangularTrackWriter):

    def initialize(self):

        si = self.shared_info
        self.add_dimension('time', None)
        self.add_dimension('particle', None)
        self.add_dimension('time_particle', None)

        self.create_variable_to_write('particles_written_per_time_step',True, False, dtype=np.int32)
        self.create_variable_to_write('particle_ID', True, True, dtype=np.int32)
        self.create_variable_to_write('write_step_index', True, True, dtype=np.int32)
        self.info['time_particle_steps_written'] = 0

    def create_variable_to_write(self,name,is_time_varying, is_part_prop, vector_dim=None, attributes_dict=None, dtype=None):
        # creates a variable to write with given shape, normally shape[0]= None as unlimited
        si=self.shared_info

        dimList=[]
        if is_time_varying and not is_part_prop: dimList.append('time')
        if is_time_varying and is_part_prop:dimList.append('time_particle')
        if not is_time_varying and is_part_prop: dimList.append('particle')

        # work out chunk dimensions from dimlist
        chunks = []
        for dim in dimList:
            if dim not in self.file_build_info['dimensions']:
                raise ValueError('Tracks file setup error: variable dimensions must be defined before variables are defined, variable  =' + name + ' , dim=', dim)

            if dim == 'time':
                chunks.append(self.params['NCDF_time_chunk'])
            elif dim == 'time_particle':
                chunks.append(self.params['NCDF_time_chunk']*si.particle_buffer_size)
            elif dim == 'particle':
                chunks.append(si.particle_buffer_size)
            else:
                chunks.append(self.file_build_info['dimensions'][dim]['size'])

        self.add_new_variable(name, dimList, attributes_dict=attributes_dict, dtype=dtype, vector_dim=vector_dim, chunking=chunks)

    def pre_time_step_write_book_keeping(self):
        # write indexing variables
        #todo change to write particle shared_params when culling ?
        nc = self.nc
        si = self.shared_info
        nWrite = self.time_steps_written_to_current_file
        self.sel_alive = si.classes['particle_properties']['status'].compare_all_to_a_value('gt', si.particle_status_flags['dead'], out= self.get_particle_index_buffer())

        n_file = self.info['time_particle_steps_written']
        self.file_index = [n_file, n_file + self.sel_alive.shape[0]]

        nc.file_handle.variables['particles_written_per_time_step'][nWrite] =  self.sel_alive.shape[0]

        nc.file_handle.variables['particle_ID'][self.file_index[0]:self.file_index[1], ...] = si.classes['particle_properties']['ID'].get_values(self.sel_alive)

        nc.file_handle.variables['write_step_index'][self.file_index[0]:self.file_index[1], ...] = nWrite * np.ones((self.sel_alive.shape[0],), dtype=np.int32)

        self.info['time_particle_steps_written'] += self.sel_alive.shape[0]

    def write_non_time_varying_particle_prop(self, prop_name, data, released):
        # this write prop like release ID as particles are release, so it works with both rectangular and compact writers
        si = self.shared_info
        IDs= si.classes['particle_properties']['ID'].get_values(released)
        d= data[released, ...]
        self.nc.file_handle.variables[prop_name][IDs, ...]  = d

    def write_time_varying_particle_prop(self, prop_name, data):
        # only write those particles which are alive
        self.nc.file_handle.variables[prop_name][self.file_index[0]:self.file_index[1], ...] = data[self.sel_alive, ...]

    def close(self):
        self.add_global_attribute('total_num_particles_released', self.shared_info.classes['particle_group_manager'].particles_released)
        self.add_global_attribute('time_steps_written', self.time_steps_written_to_current_file)
        super().close()



