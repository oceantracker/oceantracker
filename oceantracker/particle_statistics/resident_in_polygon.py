from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC, ParameterCoordsChecker as PCC, merge_params_with_defaults
from copy import  deepcopy
from oceantracker.release_groups.polygon_release import PolygonRelease
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
        self.remove_default_params(['particle_property_list'])

    def add_required_classes_and_settings(self):
        # add polygon entry exit times class to use in residency calcs
        info = self.info
        params = self.params
        info['PolygonEntryExitTimes_prop_name'] = f'{params["name"]}_PolygonEntryExitTimes'

        si.add_class('particle_properties', class_name='PolygonEntryExitTimes',
                     name=info['PolygonEntryExitTimes_prop_name'], write=False,
                     points=params['points'])

    def initial_setup(self, **kwargs):

        ml = si.msg_logger
        params = self.params
        # do standard stats initialize
        super().initial_setup()  # set up using regular grid for  stats


        self._create_file_variables(self.nc)

        self.set_up_part_prop_lists()


    def _create_file_variables_old(self, nc):

        if not self.params['write']: return

        dim_names = ('time_dim', 'pulse_dim')
        num_pulses= self.schedulers['count_scheduler'].info['number_scheduled_times']
        nc.create_dimension('pulse_dim', dim_size=num_pulses)
        nc.create_variable('count', dim_names, np.int64, description='counts of particles in each pulse of release group inside release polygon at given times')

        # set up space for requested particle properties
        # working count space
        self.count_time_slice = np.full((num_pulses,), 0, np.int64)
        self.count_all_particles_time_slice = np.full_like(self.count_time_slice, 0, np.int64)

        for p_name in self.params['particle_property_list']:
            if p_name in si.class_roles.particle_properties:
                self.sum_binned_part_prop[p_name] = np.full(num_pulses, 0.)  # zero for  summing
                nc.create_variable('sum_' + p_name, dim_names, np.float64, description='sum of particle property inside polygon  ' + p_name)
            else:
                si.msg_logger.msg('Part Prop "' + p_name + '" not a particle property, ignored and no stats calculated', warning= True)

    def create_grid_variables(self, nc): pass

    def do_counts(self,n_time_step, time_sec, sel):

        part_prop = si.class_roles.particle_properties
        rg  = self.release_group_to_count

        # manual update which polygon particles are inside
        inside_poly_prop = part_prop[self.info['inside_polygon_particle_prop']]
        inside_poly_prop.update(n_time_step, time_sec, sel)

        # do counts
        self._do_counts_and_summing_numba(inside_poly_prop.data,
                                         part_prop['IDrelease_group'].data,
                                         part_prop['IDpulse'].data,
                                         self.info['release_group_ID_to_count'],
                                         self.info['z_range'],
                                         part_prop['x'].data,
                                         self.count_time_slice, self.count_all_particles_time_slice,
                                         self.prop_data_list, self.sum_prop_data_list, sel)


    def info_to_write_on_file_close(self):
        nc = self.nc
        nc.write_variable('release_times', self.schedulers['count_scheduler'].scheduled_times, ['pulse_dim'], dtype=np.float64, attributes={'times_pulses_released': ' times in seconds since 1970'})

    @staticmethod
    @njitOT
    def _do_counts_and_summing_numba(in_polgon,
                                     release_group_ID, pulse_ID, required_release_group, zrange, x, count,
                                     count_all_particles, prop_list, sum_prop_list, sel):
        # count those of each pulse inside release polygon

        # zero out counts in the count time slices
        count[:] = 0
        count_all_particles[:] = 0
        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in sel:
            if  release_group_ID[n] == required_release_group:
                pulse= pulse_ID[n]

                # count all particles not whether in volume or not
                count_all_particles[pulse] += 1  # all particles count whether in a polygon or not , whether in required depth range or not

                if x.shape[1] == 3 and not (zrange[0] <= x[n, 2] <= zrange[1]): continue

                if in_polgon[n] >= 0: # only one polygon

                    count[pulse] += 1
                    # sum particle properties
                    for m in range(len(prop_list)):
                        sum_prop_list[m][pulse] += prop_list[m][n]