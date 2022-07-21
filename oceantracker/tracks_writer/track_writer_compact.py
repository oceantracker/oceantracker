import numpy as np
from oceantracker.tracks_writer.track_writer_retangular import RectangularTrackWriter

class FlatTrackWriter(RectangularTrackWriter):

    def initialize(self):

        self.open_file()

        # set up  variables for output
        nc = self.nc
        # required dimensions
        nc.add_a_Dimension('time_particle',None)
        nc.add_a_Dimension('time', None)
        nc.add_a_Dimension('particle', None)

        self.create_variable_to_write('particles_written_per_time_step',True, False, dtype=np.int32)
        self.create_variable_to_write('particle_ID', True, True, dtype=np.int32)
        self.create_variable_to_write('write_step_index', True, True, dtype=np.int32)
        self.info['time_particle_steps_written']= 0

    def create_variable_to_write(self,name,is_time_varying, is_part_prop, vector_dim=None, attributes=None, dtype=None):
        # creates a variable to write with given shape, normally shape[0]= None as unlimited
        si=self.shared_info
        nc = self.nc
        if dtype is bool: dtype = np.int8

        dimList=[]
        chunks =[]
        if is_time_varying and is_part_prop:
            dimList.append('time_particle')
            chunks.append(self.params['NCDF_time_chunk']*si.particle_buffer_size)
        elif is_part_prop:
            dimList.append('particle')
            chunks .append(int(0.2* si.particle_buffer_size))
        else:
            dimList.append('time') # only time varying
            chunks .append(self.params['NCDF_time_chunk'])


        if vector_dim is not None and vector_dim > 1:
            vn = ['vector2D','vector3D']
            dimList.append(vn[vector_dim-2])
            chunks.append(vector_dim)

        nc.create_a_variable(name, dimList, attributes, dtype,chunksizes= chunks)

    def pre_time_step_write_book_keeping(self, ):
        # write indexing variables
        #todo change to write particle shared_params when culling ?
        nc = self.nc
        si = self.shared_info
        nWrite = self.time_steps_written
        self.sel_alive = si.classes['particle_properties']['status'].compare_all_to_a_value('gt', si.particle_status_flags['dead'], out= self.get_particle_index_buffer())

        n_file = self.info['time_particle_steps_written']
        self.file_index = [n_file, n_file + self.sel_alive.shape[0]]

        nc.file_handle.variables['particles_written_per_time_step'][nWrite] =  self.sel_alive.shape[0]

        nc.file_handle.variables['particle_ID'][self.file_index[0]:self.file_index[1], ...] = si.classes['particle_properties']['ID'].get_values(self.sel_alive)

        nc.file_handle.variables['write_step_index'][self.file_index[0]:self.file_index[1], ...] = nWrite * np.ones((self.sel_alive.shape[0],), dtype=np.int32)

        self.info['time_particle_steps_written'] += self.sel_alive.shape[0]


    def write_non_time_varying_particle_prop(self, prop_name, data, released):
        # this write prop like relase ID as particles are release, so it works with both rectangular and compact writers
        si = self.shared_info
        IDs= si.classes['particle_properties']['ID'].get_values(released)
        self.nc.file_handle.variables[prop_name][IDs, ...] = data[released, ...]

    def write_time_varying_particle_prop(self, prop_name, data):
        # only write those particles which are alive
        self.nc.file_handle.variables[prop_name][self.file_index[0]:self.file_index[1], ...] = data[self.sel_alive, ...]

    def close(self):
        if self.nc is not None:
            nc=self.nc
            # write properties only written at end
            nc.write_global_attribute('ocean_tracker_file_fmt', 2)
            nc.write_global_attribute('total_num_particles_released', self.shared_info.classes['particle_group_manager'].particles_released)
            nc.write_global_attribute('time_steps_written', self.time_steps_written)
            nc.close()



