import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.tracks_writer.depricated._base_tracks_writer_2025_03_17 import  _BaseWriter
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

    def create_variable_to_write(self,name,is_time_varying, is_part_prop, vector_dim=None,
                                 description=None,units=None,
                                 attributes={}, dtype=None, fill_value=None):
        # creates a variable to write with given shape, normally shape[0]= None as unlimited
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
                chunks.append(si.settings.NCDF_time_chunk)
            elif dim == 'time_particle_dim':
                chunks.append(si.settings.NCDF_time_chunk*si.settings.NCDF_particle_chunk)
            elif dim == 'particle_dim':
                chunks.append(si.settings.NCDF_particle_chunk)
            else:
                chunks.append(self.info['file_builder']['dimensions'][dim]['size'])
        if description is not None:attributes.update(description=description)
        if units is not None: attributes.update(units=units)

        self.add_new_variable(name, dimList, description=description,fill_value=fill_value,
                              attributes=attributes, dtype=dtype, vector_dim=vector_dim, chunking=chunks)

    def pre_time_step_write_book_keeping(self):
        # write indexing variables
        #todo change to write particle shared_params when culling ?
        info = self.info
        nc = self.nc
        nWrite = info['time_steps_written_to_current_file']
        self.sel_alive = si.class_roles.particle_properties['status'].compare_all_to_a_value('gt', si.particle_status_flags.dead, out= self.get_partID_buffer('B1'))

        n_file = self.nc.var_shape('particle_ID')[0]

        self.file_index = [n_file, n_file + self.sel_alive.shape[0]]

        # record range if time step in time_particle dim
        nc.file_handle.variables['time_step_range'][nWrite,:] = np.asarray( self.file_index)
        nc.file_handle.variables['particles_written_per_time_step'][nWrite] =  self.sel_alive.shape[0]

        nc.file_handle.variables['particle_ID'][self.file_index[0]:self.file_index[1], ...] = si.class_roles.particle_properties['ID'].get_values(self.sel_alive)

        nc.file_handle.variables['write_step_index'][self.file_index[0]:self.file_index[1], ...] = info['total_time_steps_written'] * np.ones((self.sel_alive.shape[0],), dtype=np.int32)

        self.info['time_particle_steps_written'] += self.sel_alive.shape[0]


    def write_time_varying_info(self,name,d):
        self.nc.file_handle.variables[name][self.info['time_steps_written_to_current_file'], ...] = d.data[:]

    def write_non_time_varying_particle_prop(self, prop_name, data, released, n_write):
        # this writes prop like release ID as particles are release, so it works with both rectangular and compact writers

        self.nc.file_handle.variables[prop_name][n_write, ...] = data[released, ...]

    def write_time_varying_particle_prop(self, prop_name, data):
        # only write those particles which are alive

        self.nc.file_handle.variables[prop_name][self.file_index[0]:self.file_index[1], ...] = data[self.sel_alive, ...]

    def _close_file(self):

        self.add_global_attribute('total_num_particles_released', si.core_class_roles.particle_group_manager.info['particles_released'])
        self.add_global_attribute('time_steps_written', self.info['time_steps_written_to_current_file'])

        # write status values to  file attribues
        output_util.add_particle_status_values_to_netcdf(self.nc)

        super()._close_file()




