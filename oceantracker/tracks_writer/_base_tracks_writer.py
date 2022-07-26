import numpy as np
from os import  path
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.parameter_base_class import  ParameterBaseClass
from oceantracker.util.basic_util import nopass
from oceantracker.util.time_util import seconds_to_short_date
from oceantracker.util.ncdf_util import NetCDFhandler
from datetime import datetime
from oceantracker.util.message_and_error_logging import GracefulExitError, FatalError


# class to write with, outline methods needed
# a non-writer, as all methods are None

class _BaseWriter(ParameterBaseClass):
    # particle property  write modes,   used to set when to write  properties to output, as well as if to calculate at all



    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params({
                                'role_output_file_tag': PVC('tracks', str),
                                 'output_step_count': PVC(1,int,min=1, doc_str='Write track data every output_step_count steps of the model'),
                                 'turn_on_write_particle_properties_list': PLC([], [str],doc_str= 'Change default write param of particle properties to write to tracks file, ie  tweak write flags individually'),
                                 'turn_off_write_particle_properties_list': PLC(['water_velocity', 'particle_velocity','velocity_modifier'], [str],
                                                            doc_str='Change default write param of particle properties to not write to tracks file, ie  tweak write flags individually'),
                                 'time_steps_per_per_file': PVC(None, int,min=1, doc_str='Split track output into files with given number of time steps'),
                                 'write_dry_cell_index': PVC(True, bool,
                                              doc_str = 'Write dry cell flag to track output file for all cells, which can be used to show dry cells on plots'),
                                 })
        self.info.update({'output_file': []})
        self.total_time_steps_written = 0
        self.n_files_written = 0

        self.file_build_info={'dimensions' : {}, 'attributes': {}, 'variables': {}}
        self.add_dimension('vector2D', 2)
        self.add_dimension('vector3D', 3)
        self.nc = None

    def initialize(self):
        si= self.shared_info
        grid = si.classes['reader'].grid
        if self.params['write_dry_cell_index']:
            self.add_dimension('triangle', grid['triangles'].shape[0])
            self.add_dimension('triplets', 3)
            self.add_new_variable('dry_cell_index', ['time','triangle'], attributes_dict={'description': 'Time series of grid dry index 0-255'},
                                  dtype=np.uint8, chunking=[self.params['NCDF_time_chunk'],grid['triangles'].shape[0]])


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
        fn =si.output_file_base + '_' + self.params['role_output_file_tag']

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

            # check chunk size under 4GB
            if item['chunks'] is not None:
                c = np.asarray(item['chunks'],dtype=np.int64) # avoids float 32 over flow
                b = np.prod(c)*np.full((0,),0 ).astype(item['dtype']).itemsize # btypes in a chunk
                if float(b) >= 4.0e9 :
                    si.case_log.write_msg('Netcdf chunk size for variable "' + name+ '" exceeds 4GB, chunks=' + str(c), exception=GracefulExitError,
                       hint='Reduce tracks_writer param NCDF_time_chunk (will be slower), if many dead particles then use compact mode and manually set case_param particle_buffer_size to hold number alive at the same time',)

            try:
                nc.create_a_variable(name,item['dim_list'], chunksizes=item['chunks'], dtype=item['dtype'], attributes=item['attributes'])
            except:
                A=1

    def pre_time_step_write_book_keeping(self): pass



    def create_variable_to_write(self,name,first_dim_name,dim_len,**kwargs): pass


    def write_all_non_time_varing_part_properties(self, new_particleIDs):
    # to work in compact mode must write particle non-time varying  particle properties when released
    #  eg ID etc, releaseGroupID  etc
        si= self.shared_info
        writer = si.classes['tracks_writer']
        if si.write_tracks and new_particleIDs.shape[0] > 0:
            for name, prop in si.classes['particle_properties'].items():
                # parameters are not time varying, so done at ends in retangular writes, or on culling particles
                if not prop.params['time_varying'] and prop.params['write']:
                    writer.write_non_time_varying_particle_prop(name, prop.data, new_particleIDs)


    def write_all_time_varying_prop_and_data(self):
        # write particle data at current time step, if none the a forced write

        self.code_timer.start('write_output')
        si= self.shared_info
        grid = si.classes['reader'].grid

        # write time vary info , eg "time"
        self.pre_time_step_write_book_keeping()

        # write group data
        for name,d in si.classes['time_varying_info'].items():
            if d.params['write']:
                self.write_time_varying_info(name, d)

        for name,d in si.classes['particle_properties'].items():
            if d.params['write'] and d.params['time_varying']:
                self.write_time_varying_particle_prop(name, d.data)

        if self.params['write_dry_cell_index']:
            self.nc.file_handle.variables['dry_cell_index'][self.time_steps_written_to_current_file, : ] = grid['dry_cell_index'].reshape(1,-1)

        self.time_steps_written_to_current_file +=1 # time steps in current file
        self.total_time_steps_written  += 1 # time steps written since the start

        self.code_timer.stop('write_output')

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


