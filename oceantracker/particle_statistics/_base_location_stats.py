import numpy as np
from oceantracker.util import basic_util, output_util
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util.parameter_base_class import ParameterBaseClass
from os import  path
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.common_info_default_param_dict_templates import particle_info
from numba.typed import List as NumbaList
from oceantracker.util import time_util
class _BaseParticleLocationStats(ParameterBaseClass):

    def __init__(self):
        # set up info/attributes
        super().__init__()
        #todo add depth range for count
        self.add_default_params({ 'calculation_interval':       PVC(24*60*60.,float),
                                  'count_start_date': PVC(None, 'iso8601date',doc_str= 'Start particle counting from this date'),
                                  'count_end_date': PVC(None, 'iso8601date', doc_str='Stop particle counting from this date'),
                                  'role_output_file_tag' :           PVC('stats_base',str),
                                  'write':                      PVC(True,bool),
                                  'count_status_in_range' :  PLC(['frozen', 'moving'], [str], min_length=2, max_length=2,
                                                                 doc_str=' Count only those particles with status which fall in the given range'),
                                  'particle_property_list': PLC([], [str], make_list_unique=True)    })
        self.sum_binned_part_prop = {}
        self.info['output_file'] = None
        self.class_doc(role='Particle statistics, based on spatial particle counts and particle properties in a grid or within polygons. Statistics are \n * separated by release group \n * can be a time series of statistics or put be in particle age bins.')

    def initial_setup(self):
        si =self.shared_info
        info = self.info
        params = self.params
       # used to create boolean of those to count
        info['time_last_stats_recorded'] = si.time_of_nominal_first_occurrence


        if params['count_start_date'] is None:
            info['start_time'] = si.solver_info['model_start_time']
        else:
            info['start_time'] = time_util.isostr_to_seconds(params['count_start_date'])

        if params['count_end_date'] is None:
            info['end_time'] = si.solver_info['model_end_time']
        else:
            info['end_time'] = time_util.isostr_to_seconds(params['count_end_date'])

    def set_up_spatial_bins(self): basic_util.nopass()

    def open_output_file(self):
        si=self.shared_info
        if self.params['write']:
            self.info['output_file'] = si.output_file_base + '_' + self.params['role_output_file_tag']
            self.info['output_file'] += '_' + self.info['name'] + '.nc'
            self.nc = NetCDFhandler(path.join(si.run_output_dir, self.info['output_file']), 'w')
        else:
            self.nc = None
        self.nWrites = 0

    def set_up_time_bins(self,nc):
        # stats time variables commute to all 	for progressive writing
        nc.add_dimension('time_dim', None)  # unlimited time
        nc.create_a_variable('time', ['time_dim'],  np.float64, description= 'time in seconds')

        # other output common to all types of stats
        nc.create_a_variable('num_released', ['time_dim'], np.int64, description='total number released')

    def  set_up_part_prop_lists(self):
        # set up list of part prop and sums to enable averaging of particle properties
        si=self.shared_info
        part_prop = si.classes['particle_properties']
        self.prop_list, self.sum_prop_list = [],[]

        for key, prop in self.sum_binned_part_prop.items():
            if part_prop[key].is_vector():
                si.msg_logger.msg('On the fly statistical Binning of vector particle property  "' + key + '" not yet implemented', warning=True)
            else:
                self.prop_list.append(part_prop[key].data) # must used dataptr here
                self.sum_prop_list.append(self.sum_binned_part_prop[key][:])

        # convert to a numba list
        if len(self.prop_list) ==0:
            # must set yp typed empty lists for numba to have right signatures of numba functions
            # make list the right shape and pop to make it empty
            #todo a cleaner way to do this with NumbaList.empty??
            self.prop_list =  NumbaList([np.empty( (1,))])
            self.prop_list.pop(0)
            self.sum_prop_list = NumbaList([np.empty((1,1,1,1))])
            self.sum_prop_list.pop(0)
        else:
            # otherwise use types of arrays
            self.prop_list = NumbaList(self.prop_list)
            self.sum_prop_list = NumbaList(self.sum_prop_list)

    def select_particles_to_count(self, out):
        # select  those> 0 or equal given value to count in stats



        si = self.shared_info
        part_prop = si.classes['particle_properties']

        sel = part_prop['status'].find_those_in_range_of_values(
                si.particle_status_flags[self.params['count_status_in_range'][0]],
                si.particle_status_flags[self.params['count_status_in_range'][1]],
                out=out)
        return sel

    def is_time_to_count(self):
        si = self.shared_info
        params= self.params
        info=self.info

        if params['count_start_date'] is None:
            info['start_time'] = si.solver_info['model_start_time']
        else:
            info['start_time'] = time_util.isostr_to_seconds(params['count_start_date'])

        if params['count_end_date'] is None:
            info['end_time'] = si.solver_info['model_end_time']
        else:
            info['end_time'] = time_util.isostr_to_seconds(params['count_end_date'])

        md= si.model_direction
        out =   info['start_time'] * md <=  si.solver_info['current_model_time'] * md  <= info['end_time'] * md
        return out

    def record_time_stats_last_recorded(self, t):   self .info['time_last_stats_recorded'] = t

    def update(self, time_sec):
        if not self.is_time_to_count(): return

        self.start_update_timer()

        self.record_time_stats_last_recorded(time_sec)

        # any overloaded selection of particles given in child classes
        sel = self.select_particles_to_count(self.get_particle_index_buffer())

        self.do_counts(time_sec,sel)

        self.write_time_varying_stats(self.nWrites, time_sec)
        self.nWrites += 1

        self.stop_update_timer()

    def write_time_varying_stats(self, n, time):
        # write nth step in file
        fh = self.nc.file_handle
        fh['time'][n] = time
        fh['count'][n, ...] = self.count_time_slice[:, ...]
        fh['count_all_particles'][n, ...] = self.count_all_particles_time_slice[:, ...]

        for key, item in self.sum_binned_part_prop.items():
            self.nc.file_handle['sum_' + key][n, ...] = item[:]  # write sums  working in original view

    def info_to_write_at_end(self) : pass

    def close(self):
        si= self.shared_info
        nc = self.nc
        # write total released in each release group
        num_released=[]
        for name, i in si.classes['release_groups'].items():
            num_released.append(i.info['number_released'])

        if self.params['write']:
            self.info_to_write_at_end()
            nc.write_a_new_variable('number_released_each_release_group', np.asarray(num_released,dtype=np.int64), ['release_group_dim'], description='Total number released in each release group')
            nc.write_global_attribute('total_num_particles_released', si.classes['particle_group_manager'].particles_released)

            # add attributes mapping release index to release group name
            output_util.add_release_group_ID_info_to_netCDF(nc, si.classes['release_groups'] )

            nc.close()
        self.nc = None  # parallel pool cant pickle nc