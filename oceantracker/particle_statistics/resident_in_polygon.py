from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC, ParameterCoordsChecker as PCC, merge_params_with_defaults
from copy import  deepcopy
from oceantracker.particle_statistics.util import stats_util
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange

from oceantracker.shared_info import shared_info as si

import numpy as np
from numba import njit
#todo much clearner to  have user define polygon list for residence time per polygon like stats polygon!

class ResidentInPolygon(_BaseParticleLocationStats):
    '''
    Caculate residence times within a single given polygon for each release group'
    based on

    Lucas, L. V., & Deleersnijder, E. (2020). Timescale Methods for Simplifying, Understanding and Modeling Biophysical and Water Quality Processes in Coastal Aquatic Ecosystems: A Review. Water 2020, Vol. 12, Page 2717, 12(10), 2717. https://doi.org/10.3390/W12102717
    '''
    def __init__(self):
        # set up info/attributes
        super().__init__()

        self.add_default_params(points = PCC(None,doc_str='Points for 2D polygon to calc residence times, as N by 2 list or numpy array'))

        # todo are prop values useful, add?
        self.remove_default_params(['particle_property_list'])

    def add_required_classes_and_settings(self):
        # add polygon entry exit times class to use in residency calcs
        info = self.info
        params = self.params
        info['polygon_entry_exit_times_prop_name'] = f'{params["name"]}_polygon_entry_exit_times'

        si.add_class('particle_properties', class_name='PolygonEntryExitTimes',
                     name=info['polygon_entry_exit_times_prop_name'], write=False,
                     points=params['points'])

    def initial_setup(self, **kwargs):

        info  = self.info
        params = self.params
        # do standard stats initialize
        super().initial_setup()

        dm = si.dim_names
        info['count_dims']= {
                        dm.time: None,
                        dm.release_group:len(si.class_roles.release_groups)}

        # create count, residence time buffers
        dim_sizes =(info['count_dims'][dm.release_group],)
        self.count_time_slice = np.full(dim_sizes, 0, np.int64)
        self.count_all_alive_particles = np.full(dim_sizes, 0, np.int64)


    def open_output_file(self,file_name):
        self.nWrites = 0
        nc = super().open_output_file(file_name)
        self.add_time_variables_to_file(nc)

        # time grid count variables
        dims = self.info['count_dims']
        dim_names = [key for key in dims]
        nc.create_variable('count_all_alive_particles', dim_names[:2], np.int64,
                           compression_level=si.settings.NCDF_compression_level,
                           description='counts of all alive particles everywhere')
        nc.create_variable('count', dims.keys(), np.int64, compression_level=si.settings.NCDF_compression_level,
                           description='counts of particles in spatial bins at given times, for each release group')
        return nc

    def do_counts(self,n_time_step, time_sec, sel, alive):

        part_prop = si.class_roles.particle_properties

        stats_util._count_all_alive_time(part_prop['status'].data,
                                         part_prop['IDrelease_group'].data,
                                         self.count_all_alive_particles, alive)
        # manual update of eresidence times
        self._do_counts_and_summing_numba(
                        part_prop[self.info['polygon_entry_exit_times_prop_name']].data,
                        part_prop['IDrelease_group'].data,
                        self.count_time_slice,
                        sel)


    def info_to_write_on_file_close(self,nc):
        pass

    @staticmethod
    @njitOT
    def _do_counts_and_summing_numba(polygon_entry_exit_times,
                        IDrelease_group,
                        counts,
                        sel):
        # count those of each pulse inside release polygon
        counts[:] = 0

        for n in sel:
            ng = IDrelease_group[n]
            counts[ng] += 1



