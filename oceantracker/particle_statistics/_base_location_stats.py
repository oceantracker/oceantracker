import numpy as np
from oceantracker.util import basic_util
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util.parameter_base_class import ParameterBaseClass
from os import  path
from oceantracker.util.parameter_checking import  ParamDictValueChecker as PVC
from oceantracker.common_info_default_param_dict_templates import particle_info

class _BaseParticleLocationStats(ParameterBaseClass):

    def __init__(self):
        # set up info/attributes
        super().__init__()

        self.add_default_params({ 'calculation_interval':       PVC(24*60*60.,float),
                                  'role_output_file_tag' :           PVC('stats_base',str),
                                  'count_status_greater_than':   PVC('dead', str, possible_values=particle_info['status_flags'].keys()),
                                  'count_status_equal_to':       PVC(None, str, possible_values=particle_info['status_flags'].keys()),
                                  'write':                      PVC(True,bool)
                                  })
        self.sum_binned_part_prop = {}
        self.info['output_file'] = None


    def initialize(self):
        si =self.shared_info
       # used to create boolean of those to count
        self.info['time_last_stats_recorded'] = si.time_of_nominal_first_occurrence

    def set_up_spatial_bins(self): basic_util.nopass()

    def open_output_file(self):
        si=self.shared_info
        if self.params['write']:
            self.info['output_file'] = si.output_file_base + '_' + self.params['role_output_file_tag'] + '_%03.0f' % (self.instanceID + 1) + '.nc'
            self.nc = NetCDFhandler(path.join(si.run_output_dir, self.info['output_file']), 'w')
        else:
            self.nc = None
        self.nWrites = 0

    def select_particles_to_count(self, out):
        # select  those> 0 or equal given value to count in stats
        si = self.shared_info
        part_prop = self.shared_info.classes['particle_properties']

        if self.params['count_status_equal_to'] is None:
            sel = part_prop['status'].compare_all_to_a_value('gt', si.particle_status_flags[self.params['count_status_greater_than']], out=out)
        else:
            sel = part_prop['status'].compare_all_to_a_value('eq', si.particle_status_flags[self.params['count_status_equal_to']], out=out)

        return sel

    def record_time_stats_last_recorded(self, t):   self .info['time_last_stats_recorded'] = t

    def update(self): basic_util.nopass()


    def info_to_write_at_end(self) : pass

    def close(self):
        si= self.shared_info
        nc = self.nc
        # write total released in each release group
        num_released=[]
        for pg in si.class_list_interators['particle_release_groups']['all'].values():
            num_released.append(pg.info['number_released'])

        if self.params['write']:
            self.info_to_write_at_end()
            nc.write_a_new_variable('number_released_each_release_group', np.asarray(num_released,dtype=np.int32), ['releaseGroups'], {'Notes': 'Total number released in each release group'})
            nc.write_global_attribute('total_num_particles_released', si.classes['particle_group_manager'].particles_released)
            nc.close()
        nc = None  # parallel pool cant pickle nc