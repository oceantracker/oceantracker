import  oceantracker.util.basic_util as basic_util
from oceantracker.tracks_writer._base_tracks_writer import _BaseWriter
from oceantracker.util.ncdf_util import NetCDFhandler
from datetime import datetime
import numpy as np

from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC

from os import path


class  RectangularTrackWriter(_BaseWriter):
    # write particle properties from a property dictionary into rectangular arrays, (time ,  particles,:,:)
    # time is unlimited dimension
    #todo set time chunk to fraction of total time steps with minimum?
    #todo issue  setting up time chunks is too slow!!
    default_method = basic_util.nopass

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaultsults

        self.add_default_params({ 'NCDF_time_chunk': PVC(24, int, min =1)})
        self.nc = None


    def initialize(self):
        super().initialize()

        si = self.shared_info
        self.add_dimension('time',None)
        self.add_dimension('particle', si.particle_buffer_size)


    def create_variable_to_write(self,name,is_time_varying=True,is_part_prop = True, vector_dim=None, attributes_dict=None, dtype=None):
        # creates a variable to write with given shape, normally shape[0]= None as unlimited
        dimList=[]
        if is_time_varying:dimList.append('time')
        if is_part_prop: dimList.append('particle')

        # work out chunk dimensions from dimlist
        chunks =[]
        for n in dimList:
            if n not in self.file_build_info['dimensions' ]:
                raise ValueError('Tracks file setup error: variable dimensions must be defined before variables are defined, variable  =' + name + ' , dim=', n)
            dimsize = self.file_build_info['dimensions' ][n]['size']
            chunks.append( self.params['NCDF_time_chunk'] if dimsize is None else dimsize)

        self.add_new_variable(name, dimList, attributes_dict=attributes_dict, dtype=dtype, vector_dim=vector_dim, chunking=chunks)



    def write_time_varying_info(self,name,d):
        self.nc.file_handle.variables[name][self.time_steps_written_to_current_file, ...] = d.data[:]

    def write_time_varying_particle_prop(self, name, data):
        num_in_buffer = self.shared_info.classes['particle_group_manager'].particles_in_buffer
        self.nc.file_handle.variables[name][self.time_steps_written_to_current_file, :num_in_buffer, ...] = data[:num_in_buffer, ...]

    def write_non_time_varying_particle_prop(self, prop_name, data, sel_particles):
        # this write porop like ID as particles are created, so it works with both rectangular and compact writers
        self.nc.file_handle.variables[prop_name][sel_particles, ...] = data[sel_particles, ...]




