import numpy as np
from numba import njit
from oceantracker.util.numba_util import njitOT

from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, ParameterCoordsChecker as PCC

from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats

class GriddedStats2D_timeBased(_BaseParticleLocationStats):
    # class to hold counts of particles inside grid squares

    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({
                 'grid_size':           PLC([100, 99],[int], fixed_len=2,
                                            min=1, max=10 ** 6,
                                            doc_str='number of rows and colums in grid'),
                 'release_group_centered_grids': PVC(False, bool),
                 'grid_center':         PCC(None,single_cord=True, is3D=False),
                 'grid_span':           PCC(None, single_cord=True, is3D=False),
                 'role_output_file_tag' :    PVC('stats_gridded_time',str),
                    })
        self.grid = {}

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['x', 'status'])

    def initial_setup(self):
        # set up regular grid for  stats
        si =self.shared_info
        super().initial_setup()
        self.open_output_file()
        nc = self.nc
        if self.params['write']:
              nc.add_dimension('release_group_dim', len(si.classes['release_groups']))

        # get release group IDs to split bt
        self.set_up_spatial_bins(nc)
        self.set_up_time_bins(nc)

        # set up space for sums of requested particle properties
        self.set_up_binned_variables(nc)
        self.info['type'] = 'gridded'
        self.set_up_part_prop_lists()



    def info_to_write_at_end(self):
        nc = self.nc
        stats_grid = self.grid
        nc.write_a_new_variable('x', stats_grid['x'], ['release_groups_dim', 'x_dim'], description='Mid point of grid cell')
        nc.write_a_new_variable('y', stats_grid['y'], ['release_group_dim', 'y_dim'],  description='Mid point of grid cell')

        area = np.diff(stats_grid['y_bin_edges'][0,:]).reshape((-1,1))*np.diff(stats_grid['x_bin_edges'][0,:]).reshape((1,-1))
        nc.write_a_new_variable('grid_cell_area', area, [ 'y_dim','x_dim'],  description='Horizontal area of each cell')

    def set_up_spatial_bins(self,nc):
        si = self.shared_info
        stats_grid= self.grid
        params= self.params
        info = self.info

        # xlims in meters
        xlims= si.classes['field_group_manager'].get_grid_limits()


        # if not given choose grid center/bounds based on extent of the grid

        if params['grid_center'] is None:
            info['grid_center']= np.array([np.mean(xlims[:2]), np.mean(xlims[2:])])
        else:
            if si.hydro_model_cords_in_lat_long:
                info['grid_center_lon_lat'] = params['grid_center'].copy()
                info['grid_center']= si.transform_lon_lat_to_meters( info['grid_center_lon_lat'], in_lat_lon_order=self.params['coords_allowed_in_lat_lon_order'])
            else:
                info['grid_center'] =   params['grid_center']

        # get grid span as (2,) array
        if params['grid_span'] is None:
            info['grid_span'] = np.hstack((np.diff(xlims[:2]), np.diff(xlims[2:])))
        else:
            if si.hydro_model_cords_in_lat_long:
                info['grid_span_lon_lat'] = params['grid_span'].copy()
                info['grid_span'] = si.transform_lon_lat_deltas(info['grid_span_lon_lat'], info['grid_center_lon_lat'], deltas_in_lat_lon_order=self.params['coords_allowed_in_lat_lon_order'])
            else:
                info['grid_span'] = params['grid_span']

        # ensure grid sizes are odd, so grid center is in middle of center cell
        for n in range(len(params['grid_size'])):
            if params['grid_size'][n] %2 != 0: params['grid_size'][n]+=1

        # uncentered bin edges as N by 1 to allow replication
        base_x = np.linspace(-info['grid_span'][0]/2., info['grid_span'][0]/2., params['grid_size'][1]).reshape(-1,1)
        base_y = np.linspace(-info['grid_span'][1]/2., info['grid_span'][1]/2., params['grid_size'][0]).reshape(-1,1)

        # center of grid cells
        ngroups= len(si.classes['release_groups'])

        if params['release_group_centered_grids']:
            # form grids around mean of each release group locations

            stats_grid['x_bin_edges'] = np.full((ngroups,len(base_x)), 0., dtype=np.float64)
            stats_grid['y_bin_edges'] = np.full((ngroups,len(base_y)), 0., dtype=np.float64)

            # loop over release groups to get bin edges
            for ngroup, name  in enumerate(si.classes['release_groups'].keys()):
                x0 = si.classes['release_groups'][name].info['points'] # works for point and polygon releases,
                x_release_group_center= np.nanmean(x0[:,:2], axis=0)
                stats_grid['x_bin_edges'][ngroup, :] = base_x.T + x_release_group_center[0]
                stats_grid['y_bin_edges'][ngroup, :] = base_y.T + x_release_group_center[1]

        else:
            # used same grid with single  given center for all particle release groups
            stats_grid['x_bin_edges'] = np.tile(base_x.T, (ngroups, 1)) + info['grid_center'][0]
            stats_grid['y_bin_edges'] = np.tile(base_y.T, (ngroups, 1)) + info['grid_center'][1]

        #  bin centers for each release group
        stats_grid['x'] = (stats_grid['x_bin_edges'][:, 1:] + stats_grid['x_bin_edges'][:, 0:-1]) / 2.
        stats_grid['y'] = (stats_grid['y_bin_edges'][:, 1:] + stats_grid['y_bin_edges'][:, 0:-1]) / 2.

        # assumes equal spacing
        stats_grid['cell_area'] = np.diff(base_y,axis=0) * np.diff(base_x,axis=0).T

        if self.params['write']:
            nc.add_dimension('x_dim', stats_grid['x'].shape[1])
            nc.add_dimension('y_dim', stats_grid['y'].shape[1])


    def set_up_binned_variables(self,nc):
        if not self.params['write']: return
        si= self.shared_info
        stats_grid = self.grid

        dim_names= ['time_dim', 'release_group_dim', 'y_dim', 'x_dim']
        dim_sizes =[None, len(si.classes['release_groups']), stats_grid['y'].shape[1], stats_grid['x'].shape[1]]
        nc.create_a_variable('count', dim_names, np.int64, description= 'counts of particles in grid at given times, for each release group')
        nc.create_a_variable('count_all_particles', dim_names[:2], np.int64, description='counts of particles whether in grid or not')

        # set up space for requested particle properties
        # working count space, row are (y,x)
        self.count_time_slice = np.full(dim_sizes[1:], 0, np.int64)
        self.count_all_particles_time_slice = np.full((dim_sizes[1],), 0, np.int64)

        for p in self.params['particle_property_list']:
            if p in si.classes['particle_properties']:
                self.sum_binned_part_prop[p] = np.full(dim_sizes[1:], 0.)  # zero for  summing
                nc.create_a_variable( 'sum_' + p, dim_names, np.float64, description= 'sum of particle property inside bin' )
            else:
                si.msg_logger.msg('Part Prop "' + p + '" not a particle property, ignored and no stats calculated',warning=True)

    def do_counts(self, time_sec, sel):
        # do counts for each release  location and grid cell
        part_prop = self.shared_info.classes['particle_properties']
        stats_grid = self.grid

        # set up pointers to particle properties
        p_groupID = part_prop['IDrelease_group'].used_buffer()
        p_x= part_prop['x'].used_buffer()

        self.do_counts_and_summing_numba(p_groupID, p_x, stats_grid['x_bin_edges'], stats_grid['y_bin_edges'],
                                         self.count_time_slice, self.count_all_particles_time_slice, self.prop_list, self.sum_prop_list, sel)




    @staticmethod
    @njitOT
    def do_counts_and_summing_numba(group_ID, x, x_edges, y_edges, count, count_all_particles, prop_list, sum_prop_list, sel):
        # for time based heatmaps zero counts for one time slice
        count[:]=0
        count_all_particles[:] = 0
        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in sel:

            ng = group_ID[n]
            count_all_particles[ng] += 1

            # assumes equal spacing
            dx = x_edges[ng, 1] - x_edges[ng, 0]
            dy = y_edges[ng, 1] - y_edges[ng, 0]
            r = int(np.floor((x[n, 1] - y_edges[ng,0]) / dy))  # row is y, column x
            c = int(np.floor((x[n, 0] - x_edges[ng,0]) / dx))

            if 0 <= r < y_edges.shape[1] - 1 and 0 <= c < x_edges.shape[1] - 1:
                count[ng, r, c] += 1
                # sum particle properties
                for m in range(len(prop_list)):
                    sum_prop_list[m][ng,r,c] += prop_list[m][n]

class GriddedStats2D_agedBased(GriddedStats2D_timeBased):
    # does grid stats  based on age, but must keep whole stats grid in memory so ages can bw bined
    # bins all particles across all times into age bins,

    # NOTE: note to get unbiased stats, need to stop releasing particles 'max_age_to_bin' before end of run

    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag': PVC('stats_gridded_age',str),
                                 'min_age_to_bin':  PVC(0.,float),
                                 'max_age_to_bin':  PVC(30.*24*3600 ,float),
                                 'age_bin_size':    PVC(1.*24*3600.,float),
                                })

    def initial_setup(self):
        # set up info/attributes
        super().initial_setup()

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['age'])


    def set_up_time_bins(self,nc):
        # this set up age bins, not time
        si= self.shared_info
        stats_grid = self.grid

        # ages to bin particle ages into,  equal bins in given range
        age_min = abs(self.params['min_age_to_bin'])
        age_max = abs(self.params['max_age_to_bin'])

        # check age order and length
        if age_min >  si.run_info['model_duration']:
            self.msg(' parameter min_age_to_bin must be > duration of model run (min,max) = '
                                    + str([age_min, age_max]) + ', duration=' + str(si.run_info['model_duration']), fatal_error=True)

        if age_max <= age_min:
            self.msg(' parameter min_age_to_bin must be <  max_age_to_bin  (min,max)= '
                                    + str([age_min,age_max ]) + ', duration=' + str(si.run_info['model_duration']),fatal_error=True)

        # arange requites one mere step beyong required max_age
        dage= abs(int(self.params['age_bin_size']))
        stats_grid['age_bin_edges'] =  float(si.model_direction) * np.arange(int(age_min), int(age_max+dage), dage)

        if stats_grid['age_bin_edges'].shape[0] ==0:
            self.msg('Particle Stats, aged based: no age bins, check parms min_age_to_bin < max_age_to_bin, if backtracking these should be negative', fatal_error=True)

        stats_grid['age_bins'] = 0.5 * (stats_grid['age_bin_edges'][1:] + stats_grid['age_bin_edges'][:-1])  # ages at middle of bins

    def set_up_binned_variables(self, nc):
        # set up space for requested particle properties based on asge
        si =self.shared_info
        stats_grid = self.grid

        dim_sizes= (stats_grid['age_bins'].shape[0], len(si.classes['release_groups']), stats_grid['y'].shape[1], stats_grid['x'].shape[1])

        # working count space, row are (y,x)
        self.count_age_bins = np.full(dim_sizes, 0, np.int64)
        # counts in each age bin, whether inside grid cell or not
        self.count_all_particles =  np.full((stats_grid['age_bins'].shape[0], len(si.classes['release_groups'])) , 0, np.int64)

        for p_name in self.params['particle_property_list']:
            if p_name in si.classes['particle_properties']:
                self.sum_binned_part_prop[p_name] = np.full(dim_sizes, 0.)  # zero fro summing
            else:
                self.msg('Part Prop "' + p_name + '" not a particle property, ignored and no stats calculated', warning=True)

    def do_counts(self, time_sec, sel):
        # do counts for each release  location and grid cell, over rides parent

        stats_grid = self.grid

        # set up pointers to particle properties
        part_prop = self.shared_info.classes['particle_properties']
        p_groupID = part_prop['IDrelease_group'].used_buffer()
        p_x = part_prop['x'].used_buffer()
        p_age = part_prop['age'].used_buffer()

        self.do_counts_and_summing_numba(p_groupID, p_x, stats_grid['x_bin_edges'], stats_grid['y_bin_edges'], self.count_age_bins, self.count_all_particles, self.prop_list, self.sum_prop_list, stats_grid['age_bin_edges'], p_age, sel)


    @staticmethod
    @njitOT
    def do_counts_and_summing_numba(group_ID, x, x_edges, y_edges, count, count_all_particles, prop_list, sum_prop_list,
                                    age_bin_edges, age, active):

        # (no zeroing as accumulated over  whole run)
        da = age_bin_edges[1] - age_bin_edges[0]

        for n in active:
            ng = group_ID[n]
            dx = x_edges[ng, 1] - x_edges[ng, 0]
            dy = y_edges[ng, 1] - y_edges[ng, 0]

            r = int(np.floor((x[n, 1] - y_edges[ng, 0]) / dy))  # row is y, column x
            c = int(np.floor((x[n, 0] - x_edges[ng, 0]) / dx))
            na = int(np.floor((age[n] - age_bin_edges[0]) / da))

            if  0 <= na < (age_bin_edges.shape[0] - 1):
                count_all_particles[na, ng] += 1 # count all in each age band
                if 0 <= r < y_edges.shape[1] - 1 and 0 <= c < x_edges.shape[1] - 1 :
                    count[na, ng, r, c] += 1
                    # sum particle properties
                    for m in range(len(prop_list)):
                        sum_prop_list[m][na, ng, r, c] += prop_list[m][n]

    def write_time_varying_stats(self, n, time_sec): pass # no writing in the fly in agged based states

    def info_to_write_at_end(self):

        # only write variables as whole at end
        super().info_to_write_at_end()
        nc = self.nc
        stats_grid = self.grid

        nc.write_a_new_variable('count', self.count_age_bins, ['age_bin_dim', 'release_group_dim', 'y_dim', 'x_dim'],
                                description= 'counts of particles in grid at given ages, for each release group')
        nc.write_a_new_variable('count_all_particles', self.count_all_particles, ['age_bin_dim', 'release_group_dim'],
                                description='counts of all particles age bands for each release group')
        nc.write_a_new_variable('age_bins', stats_grid['age_bins'], ['age_bin_dim'], description= 'center of age bin, ie age axis of heat map in seconds')
        nc.write_a_new_variable('age_bin_edges', stats_grid['age_bin_edges'], ['age_bin_edges'],description='center of age bin, ie age axis of heat map in seconds')
        # particle property sums
        dims = ('age_bin_dim', 'release_group_dim', 'y_dim', 'x_dim')
        for key, item in self.sum_binned_part_prop.items():
            # need to write final sums of propetries  after all age counts done across all times
            nc.write_a_new_variable('sum_' + key, item[:], dims, description= 'sum of particle property inside bin  ' + key)

