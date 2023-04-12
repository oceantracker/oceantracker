from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats
from oceantracker.util.parameter_checking import  ParamDictValueChecker as PVC, ParameterListChecker as PLC


from oceantracker.particle_release_groups.polygon_release import PolygonRelease
from oceantracker.util.polygon_util import InsidePolygon, inside_ray_tracing_single_point
import numpy as np
from numba import njit

class ResidentInPolygon(_BaseParticleLocationStats):
    def __init__(self):
        # set up info/attributes
        super().__init__()

        self.add_default_params({'name_of_polygon_release_group':  PVC(None, str,is_required=True,
                                     doc_str='"name" parameter of polygon release group to count paticles for residence time , (release group "name"  must be set by user). Particles inside this release groups polygon are conted to be used to calculate its residence time'),
                                 'role_output_file_tag': PVC('residence', str),
                                 'z_range': PLC([], [float, int], min_length=2, doc_str='z range = [zmin, zmax] count particles in this z range in 3D'),
                                 })

    def initialize(self, **kwargs):
        si= self.shared_info
        params = self.params
        # do standard stats initialize
        super().initialize()  # set up using regular grid for  stats

        # find associated release group
        if params['name_of_polygon_release_group']  not in si.classes['particle_release_groups']:
            #todo add crumb trail to error
            si.msg_logger.msg(params['class_name'].split('.')[-1] + ' no polygon release group of name ' + params['name_of_polygon_release_group'] +
                                   ' user must name release group for residence time counts ' + ', available release group names are ' + str(list(si.classes['particle_release_groups'].keys())), fatal_error=True)

        rg = si.classes['particle_release_groups'][params['name_of_polygon_release_group']]
        if not isinstance(rg, PolygonRelease) :
            si.msg_logger.msg(params['class_name'].split('.')[-1] + ' Named  release group "' + params['name_of_polygon_release_group'] +
                                  '" is not a subclass of  PolygonRelease class, residence time must be associated with a polygon release ', fatal_error=True)

        self.release_group_to_count = rg
        self.info['release_group_name'] = rg.params['name']
        self.info['release_group_ID_to_count'] = rg.info['instanceID']


        self.polygon = InsidePolygon(self.release_group_to_count.params['points'])

        # tag file with release group number
        #params['role_output_file_tag'] += '_RG%3.0f ' % params['count_release_group']
        self.open_output_file()

        self.set_up_time_bins(self.nc)
        self.set_up_binned_variables(self.nc)
        self.set_up_part_prop_lists()

        #todo move to base location stats, so all can use depth range
        if len(self.params['z_range'])==0:
            self.params['z_range'] = [-1.0e30, 1.0e30]

        self.params['z_range']= np.asarray(self.params['z_range'])

    def check_requirements(self):
        si= self.shared_info
        params = self.params
        self.check_class_required_fields_prop_etc()


    def set_up_binned_variables(self, nc):
        si = self.shared_info
        if not self.params['write']: return

        dim_names = ('time_dim', 'pulse_dim')
        num_pulses= len(self.release_group_to_count.info['release_info']['release_schedule_times'])
        nc.add_dimension('pulse_dim', dim_size=num_pulses)
        nc.create_a_variable('count', dim_names,
                             {'notes': 'counts of particles in each pulse of release group inside release polygon at given times'},
                             np.int64)
        nc.create_a_variable('count_all_particles', ['time_dim', 'pulse_dim'],
                             {'notes': 'counts of particles in each, whether inside polygon or not at given times'}, np.int64)
        # set up space for requested particle properties
        # working count space
        self.count_time_slice = np.full((num_pulses,), 0, np.int64)
        self.count_all_particles_time_slice = np.full_like(self.count_time_slice, 0, np.int64)

        for p_name in self.params['particle_property_list']:
            if p_name in si.classes['particle_properties']:
                self.sum_binned_part_prop[p_name] = np.full(num_pulses, 0.)  # zero for  summing
                nc.create_a_variable('sum_' + p_name, dim_names,
                                     {'notes': 'sum of particle property inside polygon  ' + p_name}, np.float64)
            else:
                si.msg_logger.msg('Part Prop "' + p_name + '" not a particle property, ignored and no stats calculated', warning= True)

    def set_up_spatial_bins(self,nc ): pass

    def update(self,**kwargs):
        if not self.is_time_to_count(): return
        si= self.shared_info
        part_prop = si.classes['particle_properties']
        rg  = self.release_group_to_count
        poly= self.polygon



        # update time stats  recorded
        time = kwargs['time']
        self.record_time_stats_last_recorded(time)

        # any overloaded selection of particles given in child classes
        sel = self.select_particles_to_count(self.get_particle_index_buffer())

        # do counts
        self.do_counts_and_summing_numba(poly.line_bounds, poly.slope_inv, poly.polygon_bounds,
                                    part_prop['IDrelease_group'].data,
                                    part_prop['IDpulse'].data,
                                    self.info['release_group_ID_to_count'],
                                    self.params['z_range'],
                                    part_prop['x'].data,
                                    self.count_time_slice, self.count_all_particles_time_slice,
                                    self.prop_list, self.sum_prop_list, sel)

        self.write_time_varying_stats(self.nWrites,time)
        self.nWrites += 1

    def info_to_write_at_end(self):
        nc = self.nc
        nc.write_a_new_variable('release_schedule_times', self.release_group_to_count.info['release_info']['release_schedule_times'],['pulse_dim'], dtype=np.float64,attributesDict={'times_pulses_released': ' times in seconds since 1970'})


    @staticmethod
    @njit
    def do_counts_and_summing_numba(lb, slope_inv, bounds,
                                    release_group_ID, pulse_ID, required_release_group,zrange, x, count,
                                    count_all_particles, prop_list, sum_prop_list, active):
        # count those of each pulse inside release polygon

        # zero out counts in the count time slices
        count[:] = 0
        count_all_particles[:] = 0
        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in active:
            if  release_group_ID[n] == required_release_group:
                pulse= pulse_ID[n]

                # count all particles not whether in volume or not
                count_all_particles[pulse] += 1  # all particles count whether in a polygon or not , whether in required depth range or not

                if x.shape[1] == 3 and not (zrange[0] <= x[n, 2] <= zrange[1]): continue

                if inside_ray_tracing_single_point(x[n,:], lb, slope_inv, bounds):

                    count[pulse] += 1
                    # sum particle properties
                    for m in range(len(prop_list)):
                        sum_prop_list[m][pulse] += prop_list[m][n]