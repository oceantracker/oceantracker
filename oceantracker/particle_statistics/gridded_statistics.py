import numpy as np
from numba import njit

from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamDictValueChecker as PVC

from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats

class GriddedStats2D_timeBased(_BaseParticleLocationStats):
    # class to hold counts of particles inside grid squares

    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({
                                 'grid_size':           PLC([100, 99],[int], fixed_len=2),
                                 'release_group_centered_grids': PVC(False, bool),
                                 'grid_center':         PLC([], [float, int], fixed_len=2),
                                 'grid_span': PLC([], [float, int], fixed_len=2),
                                 'role_output_file_tag' :    PVC('stats_gridded_time',str),
                                 'calculation_interval':PVC(3600., float,doc_str=' time in sec, between calculating statistics'),
                                 })
        self.grid = {}

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['x', 'status'], required_grid_var_list=['x'])

    def initialize(self):
        # set up regular grid for  stats
        si =self.shared_info
        super().initialize()
        self.open_output_file()
        nc = self.nc
        if self.params['write']:
              nc.add_dimension('release_group_dim', len(si.classes['particle_release_groups']))

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
        nc.write_a_new_variable('x', stats_grid['x'], ['release_groups_dim', 'x_dim'], {'Notes': 'Mid point of grid cell'})
        nc.write_a_new_variable('y', stats_grid['y'], ['release_group_dim', 'y_dim'], {'Notes': 'Mid point of grid cell'})

        area = np.diff(stats_grid['y_bin_edges'][0,:]).reshape((-1,1))*np.diff(stats_grid['x_bin_edges'][0,:]).reshape((1,-1))
        nc.write_a_new_variable('grid_cell_area', area, [ 'y_dim','x_dim'], {'Notes': 'Horizontal area of each cell'})

    def set_up_spatial_bins(self,nc):
        si = self.shared_info
        grid = si.classes['reader'].grid
        stats_grid= self.grid
        params= self.params

        x = grid['x']
        xlims= [np.amin(x[:, 0]), np.amax(x[:, 0]), np.amin(x[:, 1]), np.amax(x[:, 1])]

        # if not given choose grid center/bounds based on extent of the grid

        if len(params['grid_center'])==0:
            params['grid_center']= np.array([np.mean(xlims[:2]), np.mean(xlims[2:])])

        # get grid span as (2,) array
        if len(params['grid_span']) ==0:
            params['grid_span'] = np.hstack((np.diff(xlims[:2]), np.diff(xlims[2:])))
        else:
            params['grid_span'] = np.asarray(params['grid_span'])

        # ensure grid sizes are odd, so grid center is in middle of center cell
        for n in range(len(params['grid_size'])):
            if params['grid_size'][n] %2 != 0: params['grid_size'][n]+=1

        # uncentered bin edges as N by 1 to allow replication
        base_x = np.linspace(-params['grid_span'][0]/2., params['grid_span'][0]/2., params['grid_size'][1]).reshape(-1,1)
        base_y = np.linspace(-params['grid_span'][1]/2., params['grid_span'][1]/2., params['grid_size'][0]).reshape(-1,1)

        # center of grid cells
        ngroups= len(si.classes['particle_release_groups'])

        if params['release_group_centered_grids']:
            # form grids around mean of each release group locations

            stats_grid['x_bin_edges'] = np.full((ngroups,len(base_x)), 0., dtype=np.float64)
            stats_grid['y_bin_edges'] = np.full((ngroups,len(base_y)), 0., dtype=np.float64)

            # loop over release groups to get bin edges
            for ngroup, name  in enumerate(si.classes['particle_release_groups'].keys()):
                x0 = si.classes['particle_release_groups'][name].info['points'] # works for point and polygon releases,
                x_release_group_center= np.nanmean(x0[:,:2], axis=0)
                stats_grid['x_bin_edges'][ngroup, :] = base_x.T + x_release_group_center[0]
                stats_grid['y_bin_edges'][ngroup, :] = base_y.T + x_release_group_center[1]

        else:
            # used same grid with single  given center for all particle release groups
            stats_grid['x_bin_edges'] = np.tile(base_x.T, (ngroups, 1)) + params['grid_center'][0]
            stats_grid['y_bin_edges'] = np.tile(base_y.T, (ngroups, 1)) + params['grid_center'][1]

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
        dim_sizes =[None, len(si.classes['particle_release_groups']), stats_grid['y'].shape[1], stats_grid['x'].shape[1]]
        nc.create_a_variable('count', dim_names,
                             {'notes': 'counts of particles in grid at given times, for each release group'}, np.int64)

        nc.create_a_variable('count_all_particles', dim_names[:2],
                             {'notes': 'counts of particles whether in grid or not'}, np.int64)

        # set up space for requested particle properties
        # working count space, row are (y,x)
        self.count_time_slice = np.full(dim_sizes[1:], 0, np.int64)
        self.count_all_particles_time_slice = np.full((dim_sizes[1],), 0, np.int64)

        for p in self.params['particle_property_list']:
            if p in si.classes['particle_properties']:
                self.sum_binned_part_prop[p] = np.full(dim_sizes[1:], 0.)  # zero for  summing
                nc.create_a_variable( 'sum_' + p, dim_names, {'notes': 'sum of particle property inside bin  ' + p}, np.float64)
            else:
                si.msg_logger.msg('Part Prop "' + p + '" not a particle property, ignored and no stats calculated',warning=True)

    def update(self, **kwargs):
        # do counts for each release  location and grid cell
        self.start_update_timer()
        time = kwargs['time']
        self.record_time_stats_last_recorded(time)

        part_prop = self.shared_info.classes['particle_properties']
        stats_grid = self.grid

        # set up pointers to particle properties
        p_groupID = part_prop['IDrelease_group'].dataInBufferPtr()
        p_x= part_prop['x'].dataInBufferPtr()

        sel = self.select_particles_to_count(self.get_particle_index_buffer())

        self.do_counts_and_summing_numba(p_groupID, p_x, stats_grid['x_bin_edges'], stats_grid['y_bin_edges'],
                                         self.count_time_slice, self.count_all_particles_time_slice, self.prop_list, self.sum_prop_list, sel)

        self.write_time_varying_stats(self.nWrites, time)
        self.nWrites += 1
        self.stop_update_timer()

    @staticmethod
    @njit
    def do_counts_and_summing_numba(group_ID, x, x_edges, y_edges, count, count_all_particles, prop_list, sum_prop_list, active):
        # for time based heatmaps zero counts for one time slice
        count[:]=0
        count_all_particles[:] = 0
        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in active:

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

    def initialize(self):
        # set up info/attributes
        super().initialize()

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['age'])



    def set_up_time_bins(self,nc):
        # this set up age bins, not time
        si= self.shared_info
        stats_grid = self.grid

        si.msg_logger.msg('When use aged binned particle stats, to get un biases stats., need to stop releasing particles "max_age_to_bin" '
                           + ' or max("user_age_bin_edges")  before end of run, by setting  particle param "release_duration"', note=True)

        # ages to bin particle ages into,  equal bins in given range
        age_min = abs(self.params['min_age_to_bin'])
        age_max = abs(self.params['max_age_to_bin'])

        # check age order and length
        if age_min >  si.solver_info['model_duration']:
            si.msg_logger.msg(' parameter min_age_to_bin must be > duration of model run (min,max) = '
                                    + str([age_min, age_max]) + ', duration=' + str(si.solver_info['model_duration']), fatal_error=True)

        if age_max <= age_min:
            si.msg_logger.msg(' parameter min_age_to_bin must be <  max_age_to_bin  (min,max)= '
                                    + str([age_min,age_max ]) + ', duration=' + str(si.solver_info['model_duration']),fatal_error=True)

        # arange requites one mere step beyong required max_age
        dage= abs(int(self.params['age_bin_size']))
        stats_grid['age_bin_edges'] =  float(si.model_direction) * np.arange(int(age_min), int(age_max+dage), dage)

        if stats_grid['age_bin_edges'].shape[0] ==0:
            si.msg_logger.msg('Particle Stats, aged based: no age bins, check parms min_age_to_bin < max_age_to_bin, if backtracking these should be negative', fatal_error=True)

        stats_grid['age_bins'] = 0.5 * (stats_grid['age_bin_edges'][1:] + stats_grid['age_bin_edges'][:-1])  # ages at middle of bins

    def set_up_binned_variables(self, nc):
        # set up space for requested particle properties based on asge
        si =self.shared_info
        stats_grid = self.grid

        dim_sizes= (stats_grid['age_bins'].shape[0], len(si.classes['particle_release_groups']), stats_grid['y'].shape[1], stats_grid['x'].shape[1])

        # working count space, row are (y,x)
        self.count_age_bins = np.full(dim_sizes, 0, np.int64)
        # counts in each age bin, whether inside grid cell or not
        self.count_all_particles =  np.full((stats_grid['age_bins'].shape[0], len(si.classes['particle_release_groups'])) , 0, np.int64)

        for p_name in self.params['particle_property_list']:
            if p_name in si.classes['particle_properties']:
                self.sum_binned_part_prop[p_name] = np.full(dim_sizes, 0.)  # zero fro summing
            else:
                self.msg('Part Prop "' + p_name + '" not a particle property, ignored and no stats calculated', warning=True)

    def update(self, **kwargs):
        # do counts for each release  location and grid cell, over rides parent
        self.start_update_timer()
        time = kwargs['time']
        self.record_time_stats_last_recorded(time)
        stats_grid = self.grid

        # set up pointers to particle properties
        part_prop = self.shared_info.classes['particle_properties']
        p_groupID = part_prop['IDrelease_group'].dataInBufferPtr()
        p_x = part_prop['x'].dataInBufferPtr()
        p_age = part_prop['age'].dataInBufferPtr()

        sel = self.select_particles_to_count(self.get_particle_index_buffer())

        self.do_counts_and_summing_numba(p_groupID, p_x, stats_grid['x_bin_edges'], stats_grid['y_bin_edges'], self.count_age_bins, self.count_all_particles, self.prop_list, self.sum_prop_list, stats_grid['age_bin_edges'], p_age, sel)

        self.stop_update_timer()

    @staticmethod
    @njit
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

    def info_to_write_at_end(self):

        # write variables whole
        super().info_to_write_at_end()
        nc = self.nc
        stats_grid = self.grid

        nc.write_a_new_variable('count', self.count_age_bins, ['age_bin_dim', 'release_group_dim', 'y_dim', 'x_dim'],
                                {'notes': 'counts of particles in grid at given ages, for each release group'}, np.int64)

        nc.write_a_new_variable('count_all_particles', self.count_all_particles, ['age_bin_dim', 'release_group_dim'],
                                {'notes': 'counts of all particles age bands for each release group'}, np.int64)

        nc.write_a_new_variable('age_bins', stats_grid['age_bins'], ['age_bin_dim'], {'notes': 'center of age bin, ie age axis of heat map in seconds'}, np.float64)
        nc.write_a_new_variable('age_bin_edges', stats_grid['age_bin_edges'], ['age_bin_edges'], {'notes': 'center of age bin, ie age axis of heat map in seconds'}, np.float64)
        # particle property sums
        dims = ('age_bin_dim', 'release_group_dim', 'y_dim', 'x_dim')
        for key, item in self.sum_binned_part_prop.items():
            # need to write final sums of propetries  after all age counts done across all times
            nc.write_a_new_variable('sum_' + key, item[:], dims, {'notes': 'sum of particle property inside bin  ' + key}, np.float64)

