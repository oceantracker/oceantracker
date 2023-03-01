from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.basic_util import nopass
from oceantracker.common_info_default_param_dict_templates import particle_info
from oceantracker.util.ncdf_util import NetCDFhandler
from os import path
from datetime import datetime


class _BaseTriangleProperties(ParameterBaseClass):

    def __init__(self):
        super().__init__()
        # set up info/attributes
        self.add_default_params({'class_name' : PVC(None, str,is_required=True),
                                 'particle_properties_to_track': PLC([],[str],  make_list_unique=True),
                                 'write': PVC(True, bool),
                                 'role_output_file_tag': PVC(None, str),
                                 'count_status_equal_to': PVC(None, str, possible_values=particle_info['status_flags'].keys()),
                                 'release_group_to_track': PVC(None, int, min=0),
                                 'only_update_concentrations_on_write': PVC(False, bool),
                                 'output_step_count': PVC(1, int, min=1),
                                 'calculation_interval' : PVC(1, float, min=1) # not 1 to keep file size small
                                 })
    def initialize(self):
        # set up data buffer and output variables
        self.set_up_data_buffers()
        self.set_up_output_file()

    def set_up_data_buffers(self): nopass('')

    def set_up_output_file(self):
        # set up output file
        si = self.shared_info
        grid = si.classes['reader'].grid

        tag = '' if self.params['role_output_file_tag'] is None else '_' + self.params['role_output_file_tag']
        self.info['output_file'] = si.output_file_base + '_concentrations_%03.0f' % (self.info['instanceID']  + 1) + tag + '.nc'

        si.msg_logger.write_progress_marker('opening concentrations output to : ' + self.info['output_file'])

        self.nc = NetCDFhandler(path.join(si.run_output_dir, self.info['output_file']), 'w')
        nc = self.nc
        nc.write_global_attribute('created', str(datetime.now().isoformat()))
        nc.add_dimension('time_dim', None)
        nc.add_dimension('triangle_dim', grid['triangles'].shape[0])

        nc.create_a_variable('time', ['time_dim'])
        self.time_steps_written = 0
        # need to add other variables in children
        self.info['time_last_stats_recorded'] = si.time_of_nominal_first_occurrence

    def select_particles_to_count(self):
        si= self.shared_info
        part_prop =  si.classes['particle_properties']
        return part_prop['status'].compare_all_to_a_value('gteq', si.particle_status_flags['frozen'], out=self.get_particle_index_buffer())

    def write(self, n_buffer, time):
        si = self.shared_info
        if self.params['only_update_concentrations_on_write']: self.update(n_buffer, time)

        if si.write_output_files and self.params['write'] and (self.time_steps_written+1) % self.params['output_step_count'] ==0:
            self.nc.file_handle['time'][self.time_steps_written] = time
            self.nc.file_handle['particle_count'][self.time_steps_written,...] = self.particle_count[:]
            self.nc.file_handle['particle_concentration'][self.time_steps_written, ...] = self.particle_concentration[:]
            self.time_steps_written += 1

    def update(self,n_buffer=None, time=None):nopass
    def check_requirements(self): pass

    def record_time_stats_last_recorded(self, t): self.info['time_last_stats_recorded'] = t

    def close(self):
        if hasattr(self,'nc'): self.nc.close()






