from os import path

from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC
from oceantracker.util.parameter_checking import ParameterCoordsChecker as PCC, ParameterTimeChecker as PTC
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.particle_statistics.util import stats_util
class _BaseAgeStats(ParameterBaseClass):

    def _add_age_params(self):
        self.add_default_params({
                 'min_age_to_bin': PVC(0., float, min=0., doc_str='Min. particle age to count',
                                       units='sec'),
                 'max_age_to_bin': PVC(None, float, min=1., doc_str='Max. particle age to count',
                                       units='sec', is_required=True),
                 'age_bin_size': PVC(None, float, min=1,
                                     doc_str='Size of bins to count ages into',
                                     units='sec', is_required=True),
                                 })

    def save_state(self, si, state_dir):

        fn = path.join(state_dir,f'stats_state_{self.params["name"]}.nc')
        nc = NetCDFhandler(fn,mode='w')
        self.info_to_write_on_file_close(nc)
        nc.close()
        return fn

    def restart(self, state_info):
        file_name = state_info['stats_files'][self.params['name']]
        nc = NetCDFhandler(file_name, mode='r')

        self.count_age_bins = nc.read_variable('counts_inside')
        self.count_all_alive_particles = nc.read_variable('count_all_alive_particles')

        # copy in summed properties, to preserve references in sum_prop_data_list that is used inside numba
        for name, s in self.sum_binned_part_prop.items():
            self.sum_binned_part_prop[name][:] = nc.read_variable(f'sum_{name}')

        nc.close()
        pass
    pass