import numpy as np

import oceantracker.particle_statistics.gridded_statistics as gridded_statistics
from numba import njit
from oceantracker.util.parameter_checking import  ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.parameter_base_class import   ParameterBaseClass
from oceantracker.common_info_default_param_dict_templates import default_polygon_dict_params
class _CorePolygonMethods(ParameterBaseClass):

    def __init__(self):
        super().__init__()
        # set up info/attributes
        self.add_default_params({'polygon_list': PLC([], [dict], default_value= default_polygon_dict_params,
                                                     can_be_empty_list=False, is_required=True)
                                 })

        self.remove_default_params(['grid_center','release_group_centered_grids', 'grid_span' ])

        self.file_tag = 'polygon_stats'

    def initialize(self, **kwargs):

        # do standard stats initialize
        super().initialize()# set up using regular grid for  stats
        self.info['type'] = 'polygon'

    def set_up_spatial_bins(self,nc ):
        si= self.shared_info
        particles = si.classes['particle_group_manager']

        # make a particle property to hold which polygon particles are in, but need instanceID to make it unique beteen different polygon stats instances
        particles.create_particle_property('user',dict(name= 'inside_polygonID_'+ str(self.info['instanceID'] ),
                                               class_name= 'oceantracker.particle_properties.inside_polygons.InsidePolygonsNonOverlapping2D',
                                               polygon_list=self.params['polygon_list'],
                                                write=False))
        nc.add_a_Dimension('polygon', len(self.params['polygon_list']))

class PolygonStats2D_timeBased(_CorePolygonMethods, gridded_statistics.GriddedStats2D_timeBased):
    # class to hold counts of particles inside 2D polygons squares

    def __init__(self):
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag': PVC('stats_polygon_time',str)})


    def check_requirements(self):
        msg_list = self.check_class_required_fields_prop_etc(required_props_list=['x'])
        return msg_list

    def set_up_binned_variables(self,nc):
        si = self.shared_info
        if not self.params['write']: return
        
        dim_names = ('time', 'releaseGroups', 'polygon')
        dim_sizes  = ( None, len(si.classes['particle_release_groups']), nc.get_dim_size('polygon') )

        nc.add_a_Dimension('releaseGroups', dim_sizes[1])
        nc.create_a_variable('count', dim_names,
                             {'notes': 'counts of particles in each polygon at given times, for each release group'}, np.int64)
        nc.create_a_variable('count_all_particles', ['time', 'releaseGroups'],
                             {'notes': 'counts of particles whether in a polygon or not'}, np.int64)
        # set up space for requested particle properties
        # working count space, row are (y,x)
        self.count_time_slice = np.full(dim_sizes[1:], 0, np.int64)

        # counts in each age bin, whether inside polygon or not
        self.count_all_particles_time_slice =  np.full((len(si.classes['particle_release_groups']),) , 0, np.int64)

        for p_name in self.params['particle_property_list']:
            if p_name in si.classes['particle_properties']:
                self.sum_binned_part_prop[p_name] = np.full(dim_sizes[1:], 0.)  # zero for  summing
                nc.create_a_variable( 'sum_' + p_name, dim_names, {'notes': 'sum of particle property inside polygon  ' + p_name}, np.float64)
            else:
                si.case_log.write_msg('Part Prop "' + p_name + '" not a particle property, ignored and no stats calculated')

    def update(self,**kwargs):
        si= self.shared_info
        part_prop = si.classes['particle_properties']
        g = self.grid

        # update time stats  recorded
        time = kwargs['time']
        self.record_time_stats_last_recorded(time)

        # set up pointers to particle properties
        p_groupID = part_prop['IDrelease_group'].dataInBufferPtr()
        p_x       = part_prop['x'].dataInBufferPtr()
        p_inside_polygons = part_prop['inside_polygonID_'+ str(self.info['instanceID'])].dataInBufferPtr()

        sel = self.select_particles_to_count(self.get_particle_index_buffer())

        # do counts
        self.do_counts_and_summing_numba(p_inside_polygons, p_groupID, p_x, self.count_time_slice, self.count_all_particles_time_slice, self.prop_list, self.sum_prop_list, sel)

        self.write_time_varying_stats(self.nWrites,time)
        self.nWrites += 1

    def info_to_write_at_end(self):pass  # nothing extra to write

    @staticmethod
    @njit
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

class PolygonStats2D_ageBased(_CorePolygonMethods, gridded_statistics.GriddedStats2D_agedBased):

    def __init__(self):
        super().__init__()
        self.add_default_params({'role_output_file_tag': PVC('stats_polygon_age',str)})\


    def check_requirements(self):
        msg_list = self.check_class_required_fields_prop_etc(required_props_list=['age'])
        return msg_list

    def set_up_binned_variables(self,nc):
        si = self.shared_info
        # set up space for requested particle properties
        dims= ( self.grid['age_bins'].shape[0], len(si.classes['particle_release_groups']), len(self.params['polygon_list']))
        # working count space, row are (y,x)
        self.count_age_bins = np.full(dims, 0, np.int64)
        # counts in each age bin, whether inside polygon or not
        self.count_all_particles = np.full(dims[:-1] , 0, np.int64)

        for p_name in self.params['particle_property_list']:
            if p_name in si.classes['particle_properties']:
                self.sum_binned_part_prop[p_name] = np.full(dims, 0.)  # zero for  summing
            else:
                self.write_msg('Part Prop "' + p_name + '" not a particle property, ignored and no stats calculated', warning=True)

    def update(self,**kwargs):

        part_prop = self.shared_info.classes['particle_properties']
        sgrid = self.grid

        # update time stats  recorded
        time = kwargs['time']
        self.record_time_stats_last_recorded(time)

        # set up pointers to particle properties, only point to those in buffer as no need to look at those beyond buffer
        p_groupID   = part_prop['IDrelease_group'].dataInBufferPtr()
        p_x         = part_prop['x'].dataInBufferPtr()
        p_age       = part_prop['age'].dataInBufferPtr()
        p_inside_polygons = part_prop['inside_polygonID_'+ str(self.info['instanceID'] )].dataInBufferPtr()

        # find those which user wants to count eg all alive by default
        sel = self.select_particles_to_count(self.get_particle_index_buffer())

        # loop over statistics polygons
        self.do_counts_and_summing_numba(p_inside_polygons, p_groupID, p_x, self.count_age_bins, self.count_all_particles, self.prop_list, self.sum_prop_list, sel, sgrid['age_bin_edges'], p_age)

    def info_to_write_at_end(self):
        # write variables whole
        nc = self.nc
        sgrid = self.grid

        nc.write_a_new_variable('count', self.count_age_bins, ['age_bins', 'releaseGroups', 'polygon'],
                                {'notes': 'counts of particles in grid at given ages, for each release group'}, np.int64)

        nc.write_a_new_variable('count_all_particles', self.count_all_particles, ['age_bins', 'releaseGroups'], {'notes': 'counts of  particles in all age bands for each release group, whether inside a polygon or not'}, np.int64)

        nc.write_a_new_variable('age_bins'     , sgrid['age_bins']     , ['age_bins']         , {'notes': 'center of age bin, ie age axis in seconds'}, np.float64)
        nc.write_a_new_variable('age_bin_edges', sgrid['age_bin_edges'], ['num_age_bin_edges'], {'notes': 'edges of age bins in seconds'}, np.float64)

        # particle property sums
        for key, item in self.sum_binned_part_prop.items():
            # need to write final sums of properties  after all age counts done across all times
            nc.write_a_new_variable('sum_' + key, item[:], ('age_bins', 'releaseGroups', 'polygon'), {'notes': 'sum of particle property inside bin  ' + key}, np.float64)

    @staticmethod
    @njit
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



