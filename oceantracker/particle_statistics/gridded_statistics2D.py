import numpy as np
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange
from oceantracker.util import cord_transforms

from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats
#from oceantracker.util.parameter_checking import ParameterListCheckerV2 as PLC2
from oceantracker.shared_info import shared_info as si

stationary_status = int(si.particle_status_flags.stationary)  # compile this constant into numba code

class GriddedStats2D_timeBased(_BaseParticleLocationStats):
    # class to hold counts of particles inside grid squares

    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({
                 'grid_size':  PLC([100, 99],int, fixed_len=2, min=1, max=10 ** 5, doc_str='number of (rows, columns) in grid, where rows is y size, cols x size, values should be odd, so will be rounded up to next '),
                 'release_group_centered_grids': PVC(False, bool, doc_str='Center grid on the release groups  mean horizontal location or center of release polygon. '),
                 'grid_center':         PCC(None, single_cord=True,is3D=False, doc_str='center of the statistics grid as (x,y), must be given if not using  release_group_centered_grids',
                                            units='meters'),
                 'grid_span':           PLC(None, float, doc_str='(width-x, height-y)  of the statistics grid', units='meters (dx,dy) or degrees (dlon, dlat) if geographic',
                                            is_required=True),
                 'role_output_file_tag' :    PVC('stats_gridded_time_2D',str),
                    })
        self.grid = {}

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['x', 'status'])

    def initial_setup(self):
        # set up regular grid for  stats

        super().initial_setup()
        self.open_output_file()
        nc = self.nc

        # get release group IDs to split bt
        self.set_up_spatial_bins(nc)
        self.set_up_time_bins(nc)

        # set up space for sums of requested particle properties
        self.set_up_binned_variables(nc)
        self.info['type'] = 'gridded'
        self.set_up_part_prop_lists()



    def info_to_write_at_end(self):
        nc = self.nc
        pass

    def set_up_spatial_bins(self,nc):

        stats_grid= self.grid
        params= self.params
        info = self.info
        #todo mover from info to params??

        # default if no center given use release groups
        if params['grid_center'] is None:
            params['release_group_centered_grids'] = True

        if params['release_group_centered_grids']:
            # get centers from mid release group
            # loop over release groups to get bin edges
            info['grid_centers']= []
            for ngroup, name in enumerate(si.class_roles.release_groups.keys()):
                rg = si.class_roles.release_groups[name]
                x0 = rg.info['bounding_box_ll_ul']  # works for point and polygon releases,
                x_release_group_center = np.nanmean(x0[:, :2], axis=0)
                info['grid_centers'].append(x_release_group_center)
            info['grid_centers'] = np.asarray(info['grid_centers'])

        else:
            # use given grid center for all
            info['grid_centers'] =  np.tile(params['grid_center'],(len(si.class_roles.release_groups),1))

        gsize = np.asarray(params['grid_size'])
        gsize = gsize + (gsize+1) % 2  # grid size must be odd to ensure middle of center cell at mid point , a required by re
        gspan = params['grid_span']

        # make bin centers
        base_x = np.linspace(-gspan[0] / 2, gspan[0] / 2, gsize[1] )
        base_y = np.linspace(-gspan[1] / 2, gspan[1] / 2, gsize[0])

        # make bin edges for counting inside, which is one grid cell larger
        # deal with special case of unit grid

        dx = gspan[0] if gsize[1] == 1 else float(np.diff(base_x[:2]))
        dy = gspan[1] if gsize[0] == 1 else float(np.diff(base_y[:2]))
        gspan_edges = gspan + np.asarray([dx,dy]) #  edges are one cell larger
        base_x_bin_edges = np.linspace(-gspan_edges[0]/2, gspan_edges[0]/2, gsize[1] + 1)
        base_y_bin_edges = np.linspace(-gspan_edges[1]/2, gspan_edges[1]/2, gsize[0] + 1)

        # make copies for each release group
        #   make empty arrays
        n_grids= info['grid_centers'].shape[0]
        stats_grid['x'] = np.zeros((n_grids, base_x.size), dtype=np.float64)
        stats_grid['y'] = np.zeros( (n_grids, base_y.size), dtype=np.float64)
        stats_grid['x_grid'] = np.zeros((n_grids, base_y.size,base_x.size), dtype=np.float64)
        stats_grid['y_grid'] = np.zeros((n_grids,base_y.size,base_x.size), dtype=np.float64)
        stats_grid['cell_area'] = np.zeros((n_grids, base_y.size,base_x.size), dtype=np.float64)
        stats_grid['x_bin_edges'] = np.zeros( (n_grids, base_x_bin_edges.size), dtype=np.float64)
        stats_grid['y_bin_edges'] = np.zeros( (n_grids, base_y_bin_edges.size), dtype=np.float64)



        for n_grid, p in enumerate(info['grid_centers']):
            stats_grid['x'][n_grid, :] = p[0] + base_x
            stats_grid['y'][n_grid, :] = p[1] + base_y
            stats_grid['x_bin_edges'][n_grid, :] = p[0] + base_x_bin_edges
            stats_grid['y_bin_edges'][n_grid, :] = p[1] + base_y_bin_edges

            # full mesh x, y
            x, y = np.meshgrid(stats_grid['x'][n_grid, :], stats_grid['y'][n_grid, :])
            stats_grid['x_grid'][n_grid, :, :], stats_grid['y_grid'][n_grid, :, :] = x, y

            # get cell area im meters even if in geographic coords
            x,y = np.meshgrid(stats_grid['x_bin_edges'][n_grid, :], stats_grid['y_bin_edges'][n_grid, :])

            if si.settings.use_geographic_coords:
                x,y = cord_transforms.local_grid_deg_to_meters(x,y, x[0,0], y[0,0])
            stats_grid['cell_area'][n_grid, :, :] =(x[:-1, 1:]-x[:-1, :-1])*(y[1:,:-1]-y[:-1:,:-1])

        if self.params['write']:
            nc.add_dimension('x_dim', stats_grid['x'].shape[1])
            nc.add_dimension('y_dim', stats_grid['y'].shape[1])
            nc.write_a_new_variable('x', stats_grid['x'], ['release_groups_dim', 'x_dim'], description='Mid point of grid cell', units='m or deg')
            nc.write_a_new_variable('y', stats_grid['y'], ['release_group_dim', 'y_dim'], description='Mid point of grid cell')
            nc.write_a_new_variable('x_grid', stats_grid['x_grid'], ['release_groups_dim', 'y_dim', 'x_dim'], description='x for mid point of grid cell, full grid')
            nc.write_a_new_variable('y_grid', stats_grid['y_grid'], ['release_groups_dim', 'y_dim', 'x_dim'], description='y for mid point of grid cell, full grid')


            nc.write_a_new_variable('cell_area', stats_grid['cell_area'], ['release_groups_dim','y_dim', 'x_dim'], description='Horizontal area of each cell', units='m^2')

    def set_up_binned_variables(self,nc):
        if not self.params['write']: return

        stats_grid = self.grid

        dim_names= ['time_dim', 'release_group_dim', 'y_dim', 'x_dim']
        dim_sizes =[None, len(si.class_roles.release_groups), stats_grid['y'].shape[1], stats_grid['x'].shape[1]]
        nc.create_a_variable('count', dim_names, np.int64, compression_level=si.settings.NCDF_compression_level,
                             description= 'counts of particles in grid at given times, for each release group')
        nc.create_a_variable('count_all_selected_particles', dim_names[:2], np.int64, compression_level=si.settings.NCDF_compression_level,
                             description='counts of particles selected to be counted, eg by depth range etc wherethe inside grid or not')
        nc.create_a_variable('count_all_alive_particles', dim_names[:2], np.int64, compression_level=si.settings.NCDF_compression_level,
                             description='counts of all alive particles everywhere')


        # set up space for requested particle properties
        # working count space, row are (y,x)
        self.count_time_slice = np.full(dim_sizes[1:], 0, np.int64)
        self.count_all_particles_time_slice = np.full((dim_sizes[1],), 0, np.int64)
        self.count_all_alive_particles = np.full((dim_sizes[1],), 0, np.int64)

        for p in self.params['particle_property_list']:
            if p in si.class_roles.particle_properties:
                self.sum_binned_part_prop[p] = np.full(dim_sizes[1:], 0.)  # zero for  summing
                nc.create_a_variable( 'sum_' + p, dim_names, np.float64, description= 'sum of particle property inside bin' )
            else:
                si.msg_logger.msg('Part Prop "' + p + '" not a particle property, ignored and no stats calculated',warning=True)

    def do_alive_particle_counts(self, count_all_alive, alive):
        part_prop = si.class_roles.particle_properties

        self._do_alive_particle_counting(part_prop['status'].data,part_prop['IDrelease_group'].data,
                                         self.count_all_alive_particles, alive)



    @staticmethod
    @njitOTparallel
    def _do_alive_particle_counting(status,  release_group, count_all_alive, alive):

        count_all_alive[:]  = 0.

        for nn in prange(alive.size):
            n = alive[nn]
            count_all_alive[release_group[n]] += status[n] >= stationary_status


    def do_counts(self,n_time_step, time_sec, sel):
        # do counts for each release  location and grid cell
        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid

        # set up pointers to particle properties
        p_groupID = part_prop['IDrelease_group'].used_buffer()
        p_x= part_prop['x'].used_buffer()

        self.do_counts_and_summing_numba(p_groupID, p_x, stats_grid['x_bin_edges'], stats_grid['y_bin_edges'],
                                        self.count_time_slice, self.count_all_particles_time_slice,
                                        self.prop_data_list, self.sum_prop_data_list, sel)
        pass

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

class GriddedStats2D_ageBased(GriddedStats2D_timeBased):
    # does grid stats  based on age, but must keep whole stats grid in memory so ages can bw bined
    # bins all particles across all times into age bins,

    # NOTE: note to get unbiased stats, need to stop releasing particles 'max_age_to_bin' before end of run

    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag': PVC('stats_gridded_age',str),
                                 'min_age_to_bin':  PVC(0.,float,min=0., doc_str='Min. particle age to count', units='sec'),
                                 'max_age_to_bin':  PVC(None , float, min=1., doc_str='Max. particle age to count', units='sec', is_required=True),
                                 'age_bin_size':    PVC(7*24*3600.,float,min=1,doc_str='Size of bins to count ages into, default= 1 week', units='sec'),
                                })

    def initial_setup(self):
        # set up info/attributes
        super().initial_setup()

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['age'])


    def set_up_time_bins(self,nc):
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

    def set_up_binned_variables(self, nc):
        # set up space for requested particle properties based on asge

        ml = si.msg_logger
        stats_grid = self.grid

        dim_sizes= (stats_grid['age_bins'].shape[0], len(si.class_roles.release_groups), stats_grid['y'].shape[1], stats_grid['x'].shape[1])

        # working count space, row are (y,x)
        self.count_age_bins = np.full(dim_sizes, 0, np.int64)
        # counts in each age bin, whether inside grid cell or not
        s = (stats_grid['age_bins'].shape[0], len(si.class_roles.release_groups))
        self.count_all_particles =  np.full(s, 0, np.int64)
        self.count_all_alive_particles = np.full(s, 0, np.int64)

        for p_name in self.params['particle_property_list']:
            if p_name in si.class_roles.particle_properties:
                self.sum_binned_part_prop[p_name] = np.full(dim_sizes, 0.)  # zero fro summing
            else:
                ml.msg('Part Prop "' + p_name + '" not a particle property, ignored and no stats calculated', warning=True, caller=self)

    def do_counts(self,n_time_step, time_sec, sel):
        # do counts for each release  location and grid cell, overrides parent
        # set up pointers to particle properties
        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid
        p_groupID = part_prop['IDrelease_group'].used_buffer()
        p_x = part_prop['x'].used_buffer()
        p_age = part_prop['age'].used_buffer()

        self.do_counts_and_summing_numba(p_groupID, p_x, stats_grid['x_bin_edges'], stats_grid['y_bin_edges'], self.count_age_bins,
                                         self.count_all_particles, self.prop_data_list, self.sum_prop_data_list, stats_grid['age_bin_edges'], p_age, sel)


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

            if 0 <= na < (age_bin_edges.size - 1):
                count_all_particles[na, ng] += 1 # count all in each age band
                if 0 <= r < y_edges.shape[1] - 1 and 0 <= c < x_edges.shape[1] - 1 :
                    count[na, ng, r, c] += 1
                    # sum particle properties
                    for m in range(len(prop_list)):
                        sum_prop_list[m][na, ng, r, c] += prop_list[m][n]

    def do_alive_particle_counts(self, count_all_alive, alive):
        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid

        self._do_alive_particle_counting(part_prop['status'].data,part_prop['IDrelease_group'].data,
                                         part_prop['age'].data,  stats_grid['age_bin_edges'],
                                         self.count_all_alive_particles, alive)

    @staticmethod
    @njitOTparallel
    def _do_alive_particle_counting(status,  release_group, age, age_bin_edges, count_all_alive, alive):

        da = age_bin_edges[1] - age_bin_edges[0]

        for nn in prange(alive.size):
            n = alive[nn]
            na = int(np.floor((age[n] - age_bin_edges[0]) / da))
            if 0 <= na < (age_bin_edges.size - 1):
                count_all_alive[na, release_group[n]] += status[n] >= stationary_status

    def write_time_varying_stats(self, n, time_sec): pass # no writing in the fly in agged based states

    def info_to_write_at_end(self):

        # only write variables as whole at end
        super().info_to_write_at_end()
        nc = self.nc
        stats_grid = self.grid

        nc.write_a_new_variable('count', self.count_age_bins, ['age_bin_dim', 'release_group_dim', 'y_dim', 'x_dim'],
                                description= 'counts of particles in grid at given ages, for each release group')
        nc.write_a_new_variable('count_all_selected_particles', self.count_all_particles, ['age_bin_dim', 'release_group_dim'],
                                description='counts of all particles selected to be counted in age bands for each release group ( eg selected by z range)')
        nc.write_a_new_variable('count_all_alive_particles', self.count_all_alive_particles, ['age_bin_dim', 'release_group_dim'],
                                description='counts of all particles alive from each release group, into age bins')
        nc.write_a_new_variable('age_bins', stats_grid['age_bins'], ['age_bin_dim'], description= 'center of age bin, ie age axis of heat map in seconds')
        nc.write_a_new_variable('age_bin_edges', stats_grid['age_bin_edges'], ['age_bin_edges'],description='center of age bin, ie age axis of heat map in seconds')
        # particle property sums
        dims = ('age_bin_dim', 'release_group_dim', 'y_dim', 'x_dim')
        for key, item in self.sum_binned_part_prop.items():
            # need to write final sums of propetries  after all age counts done across all times
            nc.write_a_new_variable('sum_' + key, item[:], dims, description= 'sum of particle property inside bin  ' + key)

