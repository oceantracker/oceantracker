import  oceantracker.util.basic_util as basic_util
from oceantracker.tracks_writer._base_tracks_writer import BaseWriter
from oceantracker.util.ncdf_util import NetCDFhandler
from datetime import datetime
import numpy as np

from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC

from os import path


class  RectangularTrackWriter(BaseWriter):
    # write particle properties from a property dictionary into rectangular arrays, (time ,  nparticles,:,:)
    # time is unlimited dimension
    #todo set time chunk to fraction of total time steps with minimum?
    #todo issue  steing up time chunks is slow!!
    default_method = basic_util.nopass

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaultsults

        self.add_default_params({ 'NCDF_time_chunk': PVC(24, int, min =1)})
        self.nc = None

    def add_a_Dimension(self,name,size): self.nc.add_a_Dimension(name,size)

    def initialize(self):
        si = self.shared_info
        self.open_file()
        nc= self.nc

        # add dim if not there
        nc.add_a_Dimension('time', None)
        nc.add_a_Dimension('particle', si.particle_buffer_size)
        nc.write_global_attribute('ocean_tracker_file_fmt', 1)

    def open_file(self):
        si = self.shared_info
        self.info['output_file'] = si.output_file_base + '_' + self.params['case_output_file_tag'] + '.nc'

        si.case_log.write_progress_marker('opening tracks output to : ' + self.info['output_file'])

        self.nc = NetCDFhandler(path.join(si.run_output_dir, self.info['output_file']), 'w')
        nc = self.nc
        nc.write_global_attribute('created', str(datetime.now().isoformat()))
        nc.add_a_Dimension('vector2D', 2)
        nc.add_a_Dimension('vector3D', 3)
        self.time_steps_written = 0

    def create_variable_to_write(self,name,is_time_varying=True,is_part_prop = True, vector_dim=None, attributes=None, dtype=None):
        # creates a variable to write with given shape, normally shape[0]= None as unlimited
        nc = self.nc
        if dtype is bool: dtype = np.int8

        dimList=[]
        chunks = []
        if is_time_varying:dimList.append('time')
        if is_part_prop: dimList.append('particle')

        if vector_dim is not None and vector_dim > 1:
            vn = ['vector2D','vector3D']
            dimList.append(vn[vector_dim-2])

        # work out chunk dimensions from names
        chunks=[]
        for n in dimList: chunks.append(nc.get_dim_size(n))

        if chunks[0]==0: chunks[0] = self.params['NCDF_time_chunk'] # for unlimited time dim

        nc.create_a_variable(name, dimList, attributes, dtype,chunksizes= chunks)

    def post_time_step_write_book_keeping(self):
        self.time_steps_written+=1

    def write_time_varying_info(self,name,d):
        self.nc.file_handle.variables[name][self.time_steps_written, ...] = d.data[:]

    def write_time_varying_particle_prop(self, name, data):
        num_in_buffer = self.shared_info.classes['particle_group_manager'].particles_in_buffer
        self.nc.file_handle.variables[name][self.time_steps_written, :num_in_buffer, ...] = data[:num_in_buffer, ...]

    def write_non_time_varying_particle_prop(self, prop_name, data, sel_particles):
        # this write porop like ID as particles are created, so it works with both rectangular and compact writers
        self.nc.file_handle.variables[prop_name][sel_particles, ...] = data[sel_particles, ...]



    def close(self):
        if self.nc is not None:
            nc=self.nc
            # write properties only written at end
            nc.write_global_attribute('total_num_particles_released', self.shared_info.classes['particle_group_manager'].particles_released)
            nc.write_global_attribute('time_steps_written', self.time_steps_written)
            nc.close()


