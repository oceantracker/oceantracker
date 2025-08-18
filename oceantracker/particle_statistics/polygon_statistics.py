import numpy as np
import oceantracker.particle_statistics.gridded_statistics2D as gridded_statistics2D
from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC, ParameterListChecker as PLC,merge_params_with_defaults
from oceantracker.util.parameter_base_class import   ParameterBaseClass
from oceantracker.util.numba_util import njitOT, prange, njitOTparallel
from oceantracker.util.output_util import  add_polygon_list_to_group_netcdf

from oceantracker.shared_info import shared_info as si
from oceantracker.particle_statistics.util import stats_util

class PolygonStats2D_timeBased(_BaseParticleLocationStats):
    # class to hold counts of particles inside 2D polygons squares

    def __init__(self):
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag': PVC('stats_polygon_time',str)})
        self.add_polygon_params()

    def initial_setup(self):
        # set up regular grid for  stats
        super().initial_setup()
        info = self.info
        self.create_polygon_variables_part_prop()
        self.create_time_variables()

        dm = si.dim_names
        info['count_dims']= {dm.time: None,
                       dm.release_group:len(si.class_roles.release_groups),
                       dm.polygons:  len(self.params['polygon_list']),
                       }

        self.create_count_variables(info['count_dims'],'time')
        self.set_up_part_prop_lists()



    def open_output_file(self,file_name):
        nc = super().open_output_file(file_name)
        self.nWrites = 0
        self.add_time_variables_to_file(nc)
        add_polygon_list_to_group_netcdf(nc,self.params['polygon_list'])

        # time polygon count variables to append over time
        dims = self.info['count_dims']
        dim_names = [key for key in dims]
        nc.create_variable('count', dim_names, np.int64, compression_level=si.settings.NCDF_compression_level,
                           description='counts of particles in each polygon at given times, for each release group')
        nc.create_variable('count_all_alive_particles', dim_names[:2],
                           compression_level=si.settings.NCDF_compression_level,
                           dtype=np.int64, description='counts of all particles whether selected or not')

        for p in self.params['particle_property_list']:
            nc.create_variable('sum_' + p,list(dims.keys()), np.float64, description='sum of particle property inside bin')
        return nc

    def do_counts(self,n_time_step, time_sec, sel, alive):

        part_prop = si.class_roles.particle_properties
        g = self.grid

        # update time stats  recorded

        # set up pointers to particle properties
        release_groupID = part_prop['IDrelease_group'].used_buffer()
        p_x       = part_prop['x'].used_buffer()

        stats_grid = self.grid
        stats_util._count_all_alive_time(part_prop['status'].used_buffer(), part_prop['IDrelease_group'].data,
                                         self.count_all_alive_particles, alive)
        # manual update which polygon particles are inside
        inside_poly_prop = part_prop[self.info['inside_polygon_particle_prop']]
        inside_poly_prop.update(n_time_step,time_sec,sel)

        # do counts
        self._do_counts_and_summing_numba(inside_poly_prop.used_buffer(),
                                         release_groupID, p_x, self.count_time_slice,
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

class PolygonStats2D_ageBased(_BaseParticleLocationStats):

    def __init__(self):
        super().__init__()
        self.add_default_params({'role_output_file_tag': PVC('stats_polygon_age',str)})
        self.add_age_params()
        self.add_polygon_params()

    def initial_setup(self):
        # set up regular grid for  stats
        super().initial_setup()
        info = self.info
        self.create_polygon_variables_part_prop()
        self.create_age_variables()
        dm = si.dim_names
        info['count_dims']= {dm.age: self.grid['age_bins'].size,
                       dm.release_group:len(si.class_roles.release_groups),
                       dm.polygons:  len(self.params['polygon_list'])}

        self.create_count_variables(info['count_dims'],'age')

        self.set_up_part_prop_lists()


    def _create_file_binned_variables(self, nc):

        # set up space for requested particle properties
        dims= (self.grid['age_bins'].shape[0], len(si.class_roles.release_groups), len(self.params['polygon_list']))
        # working count space, row are (y,x)
        self.count_age_bins = np.full(dims, 0, np.int64)
        # counts in each age bin, whether inside polygon or not
        self.count_all_particles = np.full(dims[:-1] , 0, np.int64)
        self.count_all_alive_particles = np.full(dims[:-1], 0, np.int64)

        for p_name in self.params['particle_property_list']:
            if p_name in si.class_roles.particle_properties:
                self.sum_binned_part_prop[p_name] = np.full(dims, 0.)  # zero for  summing
            else:
                si.msg_logger.msg('Part Prop "' + p_name + '" not a particle property, ignored and no stats calculated', warning=True)

    def do_counts(self,n_time_step, time_sec, sel, alive):

        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid

        # set up pointers to particle properties, only point to those in buffer as no need to look at those beyond buffer
        release_groupID   = part_prop['IDrelease_group'].used_buffer()
        p_x         = part_prop['x'].used_buffer()
        p_age       = part_prop['age'].used_buffer()

        stats_util._count_all_alive_age_bins(part_prop['status'].data,
                                             part_prop['IDrelease_group'].data,
                                             part_prop['age'].data, stats_grid['age_bin_edges'],
                                             self.count_all_alive_particles, alive)

        # manual update which polygon particles are inside
        inside_poly_prop = part_prop[self.info['inside_polygon_particle_prop']]
        inside_poly_prop.update(n_time_step, time_sec, sel)

        # loop over statistics polygons
        self._do_counts_and_summing_numba(inside_poly_prop.used_buffer(),
                                release_groupID, p_x, self.count_age_bins,
                                self.prop_data_list, self.sum_prop_data_list,
                                sel, stats_grid['age_bin_edges'], p_age)
    def write_time_varying_stats(self, time_sec):
        pass # no writing on the fly in aged based states
    def info_to_write_on_file_close(self):
        # write variables whole
        nc = self.nc
        stats_grid = self.grid
        dim_names = [key for key in self.info['count_dims']]
        nc.write_variable('count', self.count_age_bins, dim_names,
                          description='counts of particles in grid at given ages, for each release group')

        nc.write_variable('count_all_alive_particles', self.count_all_alive_particles, dim_names[:2],
                          description='counts of  all alive particles, not just those selected to be counted')

        nc.write_variable('age_bins', stats_grid['age_bins'], ['age_bin_dim'], description='center of age bin, ie age axis in seconds')
        nc.write_variable('age_bin_edges', stats_grid['age_bin_edges'], ['num_age_bin_edges'], description='edges of age bins in seconds')

        # particle property sums
        for key, item in self.sum_binned_part_prop.items():
            # need to write final sums of properties  after all age counts done across all times
            nc.write_variable('sum_' + key, item[:], dim_names, description='sum of particle property inside bin  ' + key)

    @staticmethod
    @njitOT
    def _do_counts_and_summing_numba(inside_polygons, group_ID, x, count,
                                     prop_list, sum_prop_list,
                                     sel, age_bin_edges, age):

        # (no zeroing as accumulated over  whole run)
        da = age_bin_edges[1] - age_bin_edges[0]

        for n in sel:

            na = int(np.floor((age[n] - age_bin_edges[0]) / da))
            if 0 <= na < (age_bin_edges.shape[0] - 1):
                # only count those in age bins
                ng= group_ID[n]
                n_poly = inside_polygons[n]
                if n_poly == -1: continue # in no polygon so no count

                count[na, ng, n_poly] += 1

                # sum particle properties
                for m in range(len(prop_list)):
                    sum_prop_list[m][na, ng, n_poly] += prop_list[m][n]



