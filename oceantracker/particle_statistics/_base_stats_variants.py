from os import path

from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC
from oceantracker.util.parameter_checking import ParameterCoordsChecker as PCC, ParameterTimeChecker as PTC
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.particle_statistics.util import stats_util
import numpy  as np
from oceantracker.shared_info import shared_info as si


class _BaseTimeStats(ParameterBaseClass):

    def _add_time_params(self):
        self.add_default_params( )

    def _create_common_time_varying_stats(self,nc):
        params = self.params
        dims = self.info['count_dims']
        dim_names =  stats_util.get_dim_names(dims)
        nc.create_variable('count_all_alive_particles', dim_names[:2], np.int64,
                           compression_level=si.settings.NCDF_compression_level,
                           description='counts of all alive particles everywhere')
        nc.create_variable('counts_inside', dims.keys(), np.int64, compression_level=si.settings.NCDF_compression_level,
                           description='counts of particles in spatial bins at given times, for each release group')
        if 'particle_property_list' in params:
            for p in params['particle_property_list']:
                nc.create_variable('sum_' + p,list(dims.keys()), np.float64, description='sum of particle property inside bin')

    def _write_common_time_varying_stats(self, time_sec):
        # write nth step in file
        n_write = self.nWrites
        fh = self.nc.file_handle
        fh['time'][n_write] = time_sec

        release_groups = si.class_roles.release_groups

        # write number released
        num_released = np.zeros((len(release_groups),), dtype=np.int32)
        for nrg, rg in enumerate(release_groups.values()):
            num_released[nrg] = rg.info['number_released']

        fh['num_released'][n_write, :] = num_released # for each release group so far
        fh['num_released_total'][n_write] = num_released.sum() # total all release groups so far

        fh['counts_inside'][n_write, ...] = self.counts_inside_time_slice[:, ...]
        fh['count_all_alive_particles'][n_write, ...] = self.count_all_alive_particles[:, ...]

        for key, item in self.sum_binned_part_prop.items():
            self.nc.file_handle['sum_' + key][n_write, ...] = item[:]  # write sums  working in original view


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

    def _create_age_variables(self):
        # this set up age bins, not time
        params = self.params
        ml = si.msg_logger
        stats_grid = self.grid

        # check age limits to bin particle ages into,  equal bins in given range
        params['max_age_to_bin'] = min(params['max_age_to_bin'], si.run_info.duration)
        params['max_age_to_bin'] = max(params['age_bin_size'], params['max_age_to_bin']) # at least one bin

        if params['min_age_to_bin'] >=  params['max_age_to_bin']: params['min_age_to_bin'] = 0
        age_range = params['max_age_to_bin']- params['min_age_to_bin']
        if params['age_bin_size'] > age_range:  params['age_bin_size'] = age_range

        # set up age bin edges
        dage= params['age_bin_size']
        stats_grid['age_bin_edges'] = float(si.run_info.model_direction) * np.arange(params['min_age_to_bin'], params['max_age_to_bin']+dage, dage)

        if stats_grid['age_bin_edges'].shape[0] ==0:
            ml.msg('Particle Stats, aged based: no age bins, check parms min_age_to_bin < max_age_to_bin, if backtracking these should be negative',
                     caller=self, error=True)

        stats_grid['age_bins'] = 0.5 * (stats_grid['age_bin_edges'][1:] + stats_grid['age_bin_edges'][:-1])  # ages at middle of bins

    def save_state(self, si, state_dir):

        fn = path.join(state_dir,f'stats_state_{self.params["name"]}.nc')
        nc = NetCDFhandler(fn,mode='w')
        self.info_to_write_on_file_close(nc)
        nc.close()
        return fn

    def restart(self, state_info):
        file_name = state_info['stats_files'][self.params['name']]
        nc = NetCDFhandler(file_name, mode='r')

        self.counts_inside_age_bins = nc.read_variable('counts_inside')
        self.count_all_alive_particles = nc.read_variable('count_all_alive_particles')

        # copy in summed properties, to preserve references in sum_prop_data_list that is used inside numba
        for name, s in self.sum_binned_part_prop.items():
            self.sum_binned_part_prop[name][:] = nc.read_variable(f'sum_{name}')

        nc.close()
        pass
    pass


class _BaseGrid2DStats(ParameterBaseClass):

    def _add_2D_grid_params(self):
        self.add_default_params({

            'grid_size': PLC([100, 99], int, fixed_len=2, min=1, max=10 ** 5,
                             doc_str='number of (rows, columns) in grid, where rows is y size, cols x size, values should be odd, so will be rounded up to next '),
            'release_group_centered_grids': PVC(False, bool,
                                                doc_str='Center grid on the release groups  mean horizontal location or center of release polygon. '),
            'grid_center': PCC(None, single_cord=True, is3D=False,
                               doc_str='center of the statistics grid as (x,y), must be given if not using  release_group_centered_grids',
                               units='meters'),
            'grid_span': PLC(None, float, doc_str='(width-x, height-y)  of the statistics grid',
                             units='meters (dx,dy) or degrees (dlon, dlat) if geographic',
                             is_required=True),
            'role_output_file_tag': PVC('stats_gridded_time_2D', str),
        })
        self.info['type'] = 'gridded'