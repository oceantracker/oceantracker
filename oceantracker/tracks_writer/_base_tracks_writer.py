import numpy as np
from os import  path
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.parameter_base_class import  ParameterBaseClass
from oceantracker.util.basic_util import nopass
from oceantracker.util.time_util import seconds_to_short_date
from oceantracker.util.ncdf_util import NetCDFhandler
from datetime import datetime

# class to write with, outline methods needed
# a non-writer, as all methods are None

class _BaseWriter(ParameterBaseClass):
    # particle property  write modes,   used to set when to write  properties to output, as well as if to calculate at all



    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params({
                                'case_output_file_tag': PVC('tracks', str),
                                 'output_step_count': PVC(1,int,min=1),
                                 'turn_on_write_particle_properties_list': PLC([], [str],doc_str= 'Change default write param of particle properties to write to tracks file, ie  tweak write flags individually'),
                                 'turn_off_write_particle_properties_list': PLC(['water_velocity', 'particle_velocity'], [str],
                                                            doc_str='Change default write param of particle properties to not write to tracks file, ie  tweak write flags individually'),
                                 'time_steps_per_per_file': PVC(None, int,min=1, doc_str='Split track output into files with given number of time steps'),
                                 })
        self.info.update({'output_file': []})
        self.total_time_steps_written = 0
        self.n_files_written = 0

        self.file_build_info={'dimensions' : {}, 'attributes': {}, 'variables': {}}
        self.add_dimension('vector2D', 2)
        self.add_dimension('vector3D', 3)
        self.nc = None

    def add_dimension(self, name, size):
        self.file_build_info['dimensions' ][name] ={'size': size}

    def add_global_attribute(self, name, value):
        self.file_build_info['attributes' ][name] = value

    def add_new_variable(self,name, dim_list, attributes_dict=None, dtype=None, vector_dim=None, chunking=None):

        if dtype is bool: dtype = np.int8
        if dtype is None: dtype=np.float64

        if vector_dim is not None and vector_dim > 1:
            vn = ['vector2D','vector3D']
            dim_list.append(vn[vector_dim-2])
            chunking.append(vector_dim)


        var={'dim_list': dim_list,
             'attributes': attributes_dict if attributes_dict is not None else {},
             'chunks' : chunking,
            'dtype' : np.int8  if dtype is bool else dtype}


        self.file_build_info['variables'][name] = var

    def open_file_if_needed(self):
        si = self.shared_info
        fn =si.output_file_base + '_' + self.params['case_output_file_tag']

        if self.total_time_steps_written == 0:
            if self.params['time_steps_per_per_file'] is not None: # first of the split files
                fn += '_%03.0f' % (self.total_time_steps_written+1)
                self.n_files_written += 1
            self._open_file(fn)

        elif self.params['time_steps_per_per_file'] is not None and self.total_time_steps_written %  self.params['time_steps_per_per_file'] == 0:
            # split make a new file
            self.close()
            self.n_files_written += 1
            self._open_file(fn + '_%03.0f' % self.n_files_written)


    def _open_file(self,file_name):
        self.time_steps_written_to_current_file = 0
        si = self.shared_info

        self.info['output_file'].append(file_name + '.nc')

        si.case_log.write_progress_marker('opening tracks output to : ' + self.info['output_file'][-1])
        self.add_global_attribute('file_created', datetime.now().isoformat())

        self.nc = NetCDFhandler(path.join(si.run_output_dir, self.info['output_file'][-1]), 'w')
        nc = self.nc

        for name, item in self.file_build_info['dimensions'].items():
            nc.add_a_Dimension(name,item['size'])

        for name, item in self.file_build_info['variables'].items():
            nc.create_a_variable(name,item['dim_list'], chunksizes=item['chunks'], dtype=item['dtype'], attributes=item['attributes'])


    def initialize(self,**kwargs): pass

    def pre_time_step_write_book_keeping(self): pass



    def create_variable_to_write(self,name,first_dim_name,dim_len,**kwargs): pass

    def close(self):
        si= self.shared_info
        if si.write_tracks:
            nc = self.nc
            # write properties only written at end
            self.add_global_attribute('total_num_particles_released', si.classes['particle_group_manager'].particles_released)
            self.add_global_attribute('time_steps_written', self.time_steps_written_to_current_file)

            # add all global attributes
            for name, item in self.file_build_info['attributes'].items():
                nc.write_global_attribute(name,item)

            nc.close()


