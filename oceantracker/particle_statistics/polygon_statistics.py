import numpy as np
import oceantracker.particle_statistics.gridded_statistics2D as gridded_statistics2D
from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.numba_util import njitOT, prange, njitOTparallel
from oceantracker.util.output_util import  add_polygon_list_to_group_netcdf
from oceantracker.particle_statistics._base_stats_variants import _BaseTimeStats, _BaseAgeStats, _BasePolygonStats
from oceantracker.shared_info import shared_info as si
from oceantracker.particle_statistics.util import stats_util
from oceantracker.particle_statistics.util.stats_util import _get_age_bin

class PolygonStats2D_timeBased(_BaseTimeStats,_BasePolygonStats,_BaseParticleLocationStats):
    '''
    Time series of counts particles inside  given 2D polygons
    The particles counted can be subsetted by status, water depth etc, default is all alive particles not outside open boundaries.
    Alive particles have  stationary, no_bottom, stranded or moving status
    Output in netcdf file split into release groups has at least
        -counts of particles in the requested subset
        -counts of all alive particles inside the domain, whether in the subset or not
    '''

    def __init__(self):
        super().__init__()
        # set up info/attributes
        self.add_default_params({
        'output_file_base': PVC('stats_polygon_time',str)})
        self._add_polygon_params()

    def initial_setup(self):
        # set up regular grid for  stats
        super().initial_setup()
        info = self.info
        self._create_polygon_variables_part_prop()

        dm = si.dim_names
        info['count_dims']= {dm.time: None,
                       dm.release_group:len(si.class_roles.release_groups),
                       dm.polygons:  len(self.params['polygon_list']),
                       }

        self.create_count_variables(info['count_dims'],'time')
        self.set_up_part_prop_lists()

    def update(self, n_time_step, time_sec, alive):
        '''Do particle counts'''
        super().update(n_time_step, time_sec, alive)

        self._write_common_time_varying_stats(time_sec)
        self.nWrites += 1


    def open_output_file(self,file_name):
        nc = super().open_output_file(file_name)
        self._create_time_file_variables(nc)
        add_polygon_list_to_group_netcdf(nc,self.params['polygon_list'])

        # time polygon count variables to append over time
        self._create_common_time_varying_stats(nc)
        return nc


    def do_counts(self,n_time_step, time_sec, sel, alive):

        part_prop = si.class_roles.particle_properties
        g = self.grid

        # update time stats  recorded
        # set up pointers to particle properties
        release_groupID = part_prop['IDrelease_group'].used_buffer()
        p_x       = part_prop['x'].used_buffer()

        stats_grid = self.grid
        self.count_all_currently_alive(alive)

        # manual update which polygon particles are inside
        inside_poly_prop = part_prop[self.info['inside_polygon_particle_prop']]
        inside_poly_prop.update(n_time_step,time_sec,sel)

        # do counts
        self._do_counts_and_summing_numba(inside_poly_prop.used_buffer(),
                                          release_groupID, p_x, self.counts_inside_time_slice,
                                          self.prop_data_list, self.sum_prop_data_list, sel)
    @staticmethod
    @njitOT
    def _do_counts_and_summing_numba(inside_polygons, group_ID, x, count,
                                     prop_list, sum_prop_list, sel):

        # zero out counts in the count time slices
        count[:] = 0
        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in sel:
            n_group= group_ID[n]
            n_poly = inside_polygons[n]

            if n_poly == -1 : continue # in no polygon so no count

            count[group_ID[n], n_poly] += 1
            # sum particle properties
            for m in range(len(prop_list)):
                sum_prop_list[m][n_group, n_poly] += prop_list[m][n]

class PolygonStats2D_ageBased(_BaseAgeStats,_BasePolygonStats, _BaseParticleLocationStats):
    '''
    Counts particles inside  given polygons as a histogram  binned by particle age, useful in tracking ages class of larvae.
    The particles counted can be subsetted by status, water depth etc, default is all alive particles not outside open boundaries.
    Alive particles have  stationary, no_bottom, stranded or moving status
     Output in netcdf file split into release groups and age bins for the entire run ( or user given start to end times)  has at least
        - counts of particles in the requested subset
        - counts of all alive particles inside the domain, whether in the subset or not
        - counts of all released particles inside the domain, whether in the subset or not
    '''
    def __init__(self):
        super().__init__()
        self.add_default_params(output_file_base= PVC('stats_polygon_age',str))
        self._add_age_params()
        self._add_polygon_params()

    def initial_setup(self):
        # set up regular grid for  stats
        super().initial_setup()
        info = self.info
        self._create_polygon_variables_part_prop()
        self._create_age_variables()
        dm = si.dim_names
        info['count_dims']= {dm.age: self.grid['age_bins'].size,
                       dm.release_group:len(si.class_roles.release_groups),
                       dm.polygons:  len(self.params['polygon_list'])}

        self.create_count_variables(info['count_dims'],'age')

        self.set_up_part_prop_lists()

    def do_counts(self,n_time_step, time_sec, sel, alive):

        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid
        # set up pointers to particle properties, only point to those in buffer as no need to look at those beyond buffer
        release_groupID   = part_prop['IDrelease_group'].used_buffer()
        p_x         = part_prop['x'].used_buffer()
        p_age       = part_prop['age'].used_buffer()

        self.count_all_alive_by_age(n_time_step,time_sec, alive)

        # manual update which polygon particles are inside
        inside_poly_prop = part_prop[self.info['inside_polygon_particle_prop']]
        inside_poly_prop.update(n_time_step, time_sec, sel)

        # loop over statistics polygons
        self._do_counts_and_summing_numba(inside_poly_prop.used_buffer(),
                                          release_groupID, p_x, self.counts_inside_age_bins,
                                          self.prop_data_list, self.sum_prop_data_list,
                                          sel, stats_grid['age_bin_edges'], p_age)


    @staticmethod
    @njitOT
    def _do_counts_and_summing_numba(inside_polygons, group_ID, x, count,
                                     prop_list, sum_prop_list,
                                     sel, age_bin_edges, age):

        # (no zeroing as accumulated over  whole run)

        for n in sel:

            na = stats_util._get_age_bin(age[n], age_bin_edges)
            if 0 <= na < (age_bin_edges.shape[0] - 1):
                # only count those in age bins
                ng= group_ID[n]
                n_poly = inside_polygons[n]
                if n_poly == -1: continue # in no polygon so no count

                count[na, ng, n_poly] += 1

                # sum particle properties
                for m in range(len(prop_list)):
                    sum_prop_list[m][na, ng, n_poly] += prop_list[m][n]



