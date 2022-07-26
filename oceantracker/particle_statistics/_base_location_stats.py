import numpy as np
from oceantracker.util import basic_util
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util.parameter_base_class import ParameterBaseClass
from os import  path
from oceantracker.util.parameter_checking import  ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.common_info_default_param_dict_templates import particle_info
from numba.typed import List as NumbaList

class _BaseParticleLocationStats(ParameterBaseClass):

    def __init__(self):
        # set up info/attributes
        super().__init__()

        self.add_default_params({ 'calculation_interval':       PVC(24*60*60.,float),
                                  'role_output_file_tag' :           PVC('stats_base',str),
                                  'file_tag': PVC(None, str),
                                  'write':                      PVC(True,bool),
                                  'count_status_in_range' :  PLC(['frozen', 'moving'], [str], min_length=2, max_length=2,
                                                                 doc_str=' Count only those particles with status which fall in the given range'),
                                  'particle_property_list': PLC([], [str], make_list_unique=True)    })
        self.sum_binned_part_prop = {}
        self.info['output_file'] = None
        self.class_doc(role='Particle statistics, based on spatial particle counts and particle properties in a grid or within polygons. Statistics are \n * separated by release group \n * can be a time series of statistics or put be in particle age bins.')

    def initialize(self):
        si =self.shared_info
       # used to create boolean of those to count
        self.info['time_last_stats_recorded'] = si.time_of_nominal_first_occurrence


    def set_up_spatial_bins(self): basic_util.nopass()

    def open_output_file(self):
        si=self.shared_info
        if self.params['write']:
            self.info['output_file'] = si.output_file_base + '_' + self.params['role_output_file_tag'] + '_%03.0f' % (self.info['instanceID']  + 1)
            self.info['output_file'] += '.nc' if self.params['file_tag'] is None else '_'+ self.params['file_tag'] + '.nc'
            self.nc = NetCDFhandler(path.join(si.run_output_dir, self.info['output_file']), 'w')
        else:
            self.nc = None
        self.nWrites = 0

    def set_up_time_bins(self,nc):
        # stats time variables commute to all 	for progressive writing
        nc.add_a_Dimension('time', None)  # unlimited time
        nc.create_a_variable('time', ['time'], {'notes': 'time in seconds'}, np.double)

        # other output common to all types of stats
        nc.create_a_variable('num_released', ['time'], {'notes': 'total number released'}, np.int64)

    def  set_up_part_prop_lists(self):
        # set up list of part prop and sums to enable averaging of particle properties
        si=self.shared_info
        part_prop = si.classes['particle_properties']
        self.prop_list, self.sum_prop_list = [],[]

        for key, prop in self.sum_binned_part_prop.items():
            if part_prop[key].is_vector():
                self.write_msg('On the fly statistical Binning of vector particle property  "' + key + '" not yet implemented', warning=None)
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
        part_prop = self.shared_info.classes['particle_properties']

        sel = part_prop['status'].find_those_in_range_of_values(
                si.particle_status_flags[self.params['count_status_in_range'][0]],
                si.particle_status_flags[self.params['count_status_in_range'][1]],
                out=out)

        return sel

    def record_time_stats_last_recorded(self, t):   self .info['time_last_stats_recorded'] = t

    def update(self): basic_util.nopass()

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
        for pg in si.class_interators_using_name['particle_release_groups']['all'].values():
            num_released.append(pg.info['number_released'])

        if self.params['write']:
            self.info_to_write_at_end()
            nc.write_a_new_variable('number_released_each_release_group', np.asarray(num_released,dtype=np.int64), ['releaseGroups'], {'Notes': 'Total number released in each release group'})
            nc.write_global_attribute('total_num_particles_released', si.classes['particle_group_manager'].particles_released)
            nc.close()
        nc = None  # parallel pool cant pickle nc