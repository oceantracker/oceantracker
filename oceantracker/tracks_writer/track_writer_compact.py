import numpy as np
from os import  path
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.tracks_writer._base_tracks_writer import  _BaseWriter
from oceantracker.tracks_writer.dev_convert_compact_tracks import convert_to_rectangular

import oceantracker.common_info_default_param_dict_templates as common_info
class CompactTracksWriter(_BaseWriter):
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaultsults

        self.add_default_params({'NCDF_time_chunk': PVC(24, int, min=1, doc_str=' number of time steps per time chunk in the netcdf file'),
                                 'NCDF_particle_chunk': PVC(100_000, int, min=1000, doc_str=' number of particles per time chunk in the netcdf file'),
                                 #'convert': PVC(False, bool, doc_str='convert compact tracks file to rectangular for at end of the run'),
                                 'retain_compact_files': PVC(False, bool,
                                                             doc_str='keep  compact tracks files after conversion to rectangular format'),
                                 'role_output_file_tag': PVC('tracks_compact', str),
                                 'write_dry_cell_index' : PVC(True,bool, obsolete='Use top level setting write_dry_cell_flag, instead')
                                 })
        self.nc = None

    def initial_setup(self):
        super().initial_setup()
        si = self.shared_info
        self.add_dimension('particle_dim', None)
        self.add_dimension('time_particle_dim', None)
        self.add_dimension('range_pair_dim', 2)

        self.create_variable_to_write('particles_written_per_time_step',True, False, dtype=np.int32)
        self.create_variable_to_write('particle_ID', True, True, dtype=np.int32)
        self.create_variable_to_write('write_step_index', True, True, dtype=np.int32)

        # variable to give index ranges of time steps within output
        self.add_new_variable('time_step_range', ['time_dim','range_pair_dim'],
                              description='range in time_particle_dim for each time step',
                               dtype=np.int32)

        self.info['time_particle_steps_written'] = 0

    def create_part_prop_to_write(self,name, instance):
        #todo write wrapper for below for particle properties to be easier to use
        pass

    def create_variable_to_write(self,name,is_time_varying, is_part_prop, vector_dim=None,
                                 description=None, attributes=None, dtype=None, fill_value=None):
        # creates a variable to write with given shape, normally shape[0]= None as unlimited
        si=self.shared_info
        dimList=[]
        if is_time_varying and not is_part_prop: dimList.append('time_dim')
        if is_time_varying and is_part_prop:dimList.append('time_particle_dim')
        if not is_time_varying and is_part_prop: dimList.append('particle_dim')

        # work out chunk dimensions from dimlist
        chunks = []
        for dim in dimList:
            if dim not in self.info['file_builder']['dimensions']:
                raise ValueError('Tracks file setup error: variable dimensions must be defined before variables are defined, variable  =' + name + ' , dim=', dim)

            if dim == 'time_dim':
                chunks.append(self.params['NCDF_time_chunk'])
            elif dim == 'time_particle_dim':
                chunks.append(self.params['NCDF_time_chunk']*self.params['NCDF_particle_chunk'])
            elif dim == 'particle_dim':
                chunks.append(self.params['NCDF_particle_chunk'])
            else:
                chunks.append(self.info['file_builder']['dimensions'][dim]['size'])



        self.add_new_variable(name, dimList, description=description,fill_value=fill_value,
                              attributes=attributes, dtype=dtype, vector_dim=vector_dim, chunking=chunks)

    def pre_time_step_write_book_keeping(self):
        # write indexing variables
        #todo change to write particle shared_params when culling ?
        nc = self.nc
        si = self.shared_info
        nWrite = self.time_steps_written_to_current_file
        self.sel_alive = si.classes['particle_properties']['status'].compare_all_to_a_value('gt', si.particle_status_flags['dead'], out= self.get_partID_buffer('B1'))

        n_file = self.info['time_particle_steps_written']
        self.file_index = [n_file, n_file + self.sel_alive.shape[0]]

        # record range if time step in time_particle dim
        nc.file_handle.variables['time_step_range'][nWrite,:] = np.asarray( self.file_index)
        nc.file_handle.variables['particles_written_per_time_step'][nWrite] =  self.sel_alive.shape[0]

        nc.file_handle.variables['particle_ID'][self.file_index[0]:self.file_index[1], ...] = si.classes['particle_properties']['ID'].get_values(self.sel_alive)

        nc.file_handle.variables['write_step_index'][self.file_index[0]:self.file_index[1], ...] = nWrite * np.ones((self.sel_alive.shape[0],), dtype=np.int32)

        self.info['time_particle_steps_written'] += self.sel_alive.shape[0]

    def write_time_varying_info(self,name,d):
        self.nc.file_handle.variables[name][self.time_steps_written_to_current_file, ...] = d.data[:]

    def write_non_time_varying_particle_prop(self, prop_name, data, released):
        # this writes prop like release ID as particles are release, so it works with both rectangular and compact writers
        si = self.shared_info
        IDs= si.classes['particle_properties']['ID'].get_values(released)
        d= data[released, ...]
        self.nc.file_handle.variables[prop_name][IDs, ...]  = d

    def write_time_varying_particle_prop(self, prop_name, data):
        # only write those particles which are alive
        self.nc.file_handle.variables[prop_name][self.file_index[0]:self.file_index[1], ...] = data[self.sel_alive, ...]

    def close(self):
        si = self.shared_info
        if si.settings['write_tracks']:
            self.add_global_attribute('total_num_particles_released', si.classes['particle_group_manager'].info['particles_released'])
            self.add_global_attribute('time_steps_written', self.time_steps_written_to_current_file)

            # write status values to file
            for key, val in common_info.particle_info['status_flags'].items():
                self.add_global_attribute('status_'+ key, int(val))

            super().close()
            '''
            if self.params['convert']:
                # convert output files to rectangular format
                for fn in self.info['output_file']:
                    convert_to_rectangular(path.join(si.run_output_dir, fn),
                                           time_chunk=self.params['NCDF_time_chunk'])
                pass
            '''



