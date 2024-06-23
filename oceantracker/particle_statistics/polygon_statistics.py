import numpy as np
import oceantracker.particle_statistics.gridded_statistics as gridded_statistics
from numba import njit
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC, ParameterListChecker as PLC,merge_params_with_defaults
from oceantracker.util.parameter_base_class import   ParameterBaseClass
from oceantracker.util.numba_util import njitOT
from oceantracker.util.output_util import  add_polygon_list_to_group_netcdf
from oceantracker.shared_info import SharedInfo as si

class _CorePolygonMethods(ParameterBaseClass):

    def __init__(self):
        super().__init__()
        # set up info/attributes
        self.add_default_params({'polygon_list': [],
                                 'use_release_group_polygons': PVC(False, bool,doc_str = 'Omit polygon_list param and use all polygon release polygons as statistics/counting polygons, useful for building release group polygon to polygon connectivity matrix.'),
                                 })

        self.remove_default_params(['grid_center','release_group_centered_grids', 'grid_span' ])
        self.file_tag = 'polygon_stats'

    def initial_setup(self, **kwargs):

        ml = si.msg_logger
        params = self.params

        # pre fill  polygon list from release groups if requested
        if params['use_release_group_polygons']:
            params['polygon_list']=[]
            for name, i in si.roles.release_groups.items():
                if i.info['release_type'] == 'polygon':
                    params['polygon_list'].append({'name': name, 'points':i.params['points']})

            if len(params['polygon_list']) == 0:
                ml.msg('There are no polygon releases to use as statistic polygons',
                                  hint='must have at least one polygon release defined to use the use_release_group_polygons parameter, or use statistics polygon_list parameter',
                                   fatal_error=True, exit_now=True, caller=self)
        else:
            # use give polygon list
            for p in params['polygon_list']:
                p = merge_params_with_defaults(p,  si.default_polygon_dict_params,
                                si.msg_logger, crumbs='polygon_statistics_merging polygon list')
                if si.hydro_model_cords_in_lat_long:
                    p['points_lon_lat'] = p['points'].copy()
                    p['points'] = si._transform_lon_lat_to_meters(p['points_lon_lat'], in_lat_lon_order=params['coords_in_lat_lon_order'])

        if len(params['polygon_list'])==0:
            ml.msg('Must have polygon_list parameter  with at least one polygon dictionary', caller=self,
                        fatal_error=True, exit_now=True,hint= 'eg. polygon_list =[ {"points": [[2.,3.],....]} ]')

        # do standard stats initialize
        super().initial_setup()  # set up using regular grid for  stats
        self.info['type'] = 'polygon'


    def set_up_spatial_bins(self,nc ):

        pgm = si.core_roles.particle_group_manager

        # make a particle property to hold which polygon particles are in, but need instanceID to make it unique beteen different polygon stats instances
        self.info['inside_polygon_particle_prop'] = f'inside_polygon_for_onfly_stats_ {self.info["instanceID"]:03d}'
        pgm.add_particle_property(self.info['inside_polygon_particle_prop'],'manual_update',dict(
                                               class_name= 'oceantracker.particle_properties.inside_polygons.InsidePolygonsNonOverlapping2D',
                                               polygon_list=self.params['polygon_list'],
                                                write=False))
        nc.add_dimension('polygon_dim', len(self.params['polygon_list']))

        add_polygon_list_to_group_netcdf(nc,self.params['polygon_list'])

class PolygonStats2D_timeBased(_CorePolygonMethods, gridded_statistics.GriddedStats2D_timeBased):
    # class to hold counts of particles inside 2D polygons squares

    def __init__(self):
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag': PVC('stats_polygon_time',str)})


    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['x'])

    def set_up_binned_variables(self,nc):

        if not self.params['write']: return
        
        dim_names = ('time_dim', 'release_group_dim', 'polygon_dim')
        dim_sizes  = ( None, len(si.roles.release_groups), nc.dim_size('polygon_dim') )

        nc.add_dimension('release_group_dim', dim_sizes[1])
        nc.create_a_variable('count', dim_names, np.int64, description='counts of particles in each polygon at given times, for each release group')
        nc.create_a_variable('count_all_particles', ['time_dim', 'release_group_dim'], np.int64, description='counts of particles whether in a polygon or not')
        # set up space for requested particle properties
        # working count space, row are (y,x)
        self.count_time_slice = np.full(dim_sizes[1:], 0, np.int64)

        # counts in each age bin, whether inside polygon or not
        self.count_all_particles_time_slice =  np.full((len(si.roles.release_groups),) , 0, np.int64)

        for p_name in self.params['particle_property_list']:
            if p_name in si.roles.particle_properties:
                self.sum_binned_part_prop[p_name] = np.full(dim_sizes[1:], 0.)  # zero for  summing
                nc.create_a_variable( 'sum_' + p_name, dim_names, np.float64,  description='sum of particle property inside polygon  ' + p_name)
            else:
                si.msg_logger.msg('Part Prop "' + p_name + '" not a particle property, ignored and no stats calculated')



    def do_counts(self,n_time_step, time_sec, sel):

        part_prop = si.roles.particle_properties
        g = self.grid

        # update time stats  recorded

        # set up pointers to particle properties
        p_groupID = part_prop['IDrelease_group'].used_buffer()
        p_x       = part_prop['x'].used_buffer()

        # manual update which polygon particles are inside
        inside_poly_prop = part_prop[self.info['inside_polygon_particle_prop']]
        inside_poly_prop.update(n_time_step,time_sec,sel)

        # do counts
        self.do_counts_and_summing_numba(inside_poly_prop.used_buffer(),
                                         p_groupID, p_x, self.count_time_slice, self.count_all_particles_time_slice, self.prop_data_list, self.sum_prop_data_list, sel)


    def info_to_write_at_end(self):pass  # nothing extra to write

    @staticmethod
    @njitOT
    def do_counts_and_summing_numba(inside_polygons, group_ID, x, count, count_all_particles, prop_list, sum_prop_list, active):

        # zero out counts in the count time slices
        count[:] = 0
        count_all_particles[:] = 0
        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in active:
            n_group= group_ID[n]
            count_all_particles[n_group] += 1  # all particles counter whether in a polygon or not
            n_poly = inside_polygons[n]

            if n_poly == -1 : continue # in no polygon so no count

            count[group_ID[n], n_poly] += 1
            # sum particle properties
            for m in range(len(prop_list)):
                sum_prop_list[m][n_group, n_poly] += prop_list[m][n]

class PolygonStats2D_ageBased(_CorePolygonMethods, gridded_statistics.GriddedStats2D_ageBased):

    def __init__(self):
        super().__init__()
        self.add_default_params({'role_output_file_tag': PVC('stats_polygon_age',str)})\


    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['age'])


    def set_up_binned_variables(self,nc):
         


        # set up space for requested particle properties
        dims= ( self.grid['age_bins'].shape[0], len(si.roles.release_groups), len(self.params['polygon_list']))
        # working count space, row are (y,x)
        self.count_age_bins = np.full(dims, 0, np.int64)
        # counts in each age bin, whether inside polygon or not
        self.count_all_particles = np.full(dims[:-1] , 0, np.int64)

        for p_name in self.params['particle_property_list']:
            if p_name in si.roles.particle_properties:
                self.sum_binned_part_prop[p_name] = np.full(dims, 0.)  # zero for  summing
            else:
                si.msg_logger.msg('Part Prop "' + p_name + '" not a particle property, ignored and no stats calculated', warning=True)

    def do_counts(self,n_time_step, time_sec, sel):

        part_prop = si.roles.particle_properties
        stats_grid = self.grid



        # set up pointers to particle properties, only point to those in buffer as no need to look at those beyond buffer
        p_groupID   = part_prop['IDrelease_group'].used_buffer()
        p_x         = part_prop['x'].used_buffer()
        p_age       = part_prop['age'].used_buffer()

        # manual update which polygon particles are inside
        inside_poly_prop = part_prop[self.info['inside_polygon_particle_prop']]
        inside_poly_prop.update(n_time_step, time_sec, sel)

        # loop over statistics polygons
        self.do_counts_and_summing_numba(inside_poly_prop.used_buffer(), p_groupID, p_x, self.count_age_bins,
                                         self.count_all_particles, self.prop_data_list, self.sum_prop_data_list, sel, stats_grid['age_bin_edges'], p_age)

    def info_to_write_at_end(self):
        # write variables whole
        nc = self.nc
        stats_grid = self.grid

        nc.write_a_new_variable('count', self.count_age_bins, ['age_bin_dim', 'release_group_dim', 'polygon_dim'],
                               description='counts of particles in grid at given ages, for each release group')

        nc.write_a_new_variable('count_all_particles', self.count_all_particles, ['age_bin_dim', 'release_group_dim'],
                                description='counts of  particles in all age bands for each release group, whether inside a polygon or not')

        nc.write_a_new_variable('age_bins'     , stats_grid['age_bins']     , ['age_bin_dim'], description= 'center of age bin, ie age axis in seconds')
        nc.write_a_new_variable('age_bin_edges', stats_grid['age_bin_edges'], ['num_age_bin_edges'], description='edges of age bins in seconds')

        # particle property sums
        for key, item in self.sum_binned_part_prop.items():
            # need to write final sums of properties  after all age counts done across all times
            nc.write_a_new_variable('sum_' + key, item[:], ('age_bin_dim', 'release_group_dim', 'polygon_dim'), description= 'sum of particle property inside bin  ' + key)

    @staticmethod
    @njitOT
    def do_counts_and_summing_numba(inside_polygons, group_ID, x, count, count_all_particles, prop_list, sum_prop_list,
                                     active, age_bin_edges, age):

        # (no zeroing as accumulated over  whole run)
        da = age_bin_edges[1] - age_bin_edges[0]

        for n in active:

            na = int(np.floor((age[n] - age_bin_edges[0]) / da))
            if 0 <= na < (age_bin_edges.shape[0] - 1):
                # only count those in age bins
                ng= group_ID[n]
                count_all_particles[na,ng] += 1

                n_poly = inside_polygons[n]
                if n_poly == -1: continue # in no polygon so no count

                count[na, ng, n_poly] += 1

                # sum particle properties
                for m in range(len(prop_list)):
                    sum_prop_list[m][na, ng, n_poly] += prop_list[m][n]



