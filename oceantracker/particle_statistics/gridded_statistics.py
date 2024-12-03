import numpy as np
from numba import njit
from oceantracker.util.numba_util import njitOT

from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats
#from oceantracker.util.parameter_checking import ParameterListCheckerV2 as PLC2
from oceantracker.shared_info import shared_info as si

class GriddedStats2D_timeBased(_BaseParticleLocationStats):
    # class to hold counts of particles inside grid squares

    def __init__(self):
        # set up info/attributes
        super().__init__()
        # set up info/attributes
        self.add_default_params({
                 'grid_size':  PLC([100, 99],int, fixed_len=2, min=1, max=10 ** 5, doc_str='number of (rows, columns) in grid, where rows is y size, cols x size, values should be odd, so will be rounded up to next '),
                 'release_group_centered_grids': PVC(False, bool),
                 'grid_center':         PCC(None, single_cord=True,is3D=False, doc_str='center of the statistics grid as (x,y), must be given if not using  release_group_centered_grids',
                                            units='meters'),
                 'grid_span':           PCC([10000,10000], single_cord=True, is3D=False,doc_str='(width-x, height-y)  of the statistics grid', units='meters only'),
                 'role_output_file_tag' :    PVC('stats_gridded_time',str),
                    })
        self.grid = {}

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['x', 'status'])

    def initial_setup(self):
        # set up regular grid for  stats

        super().initial_setup()
        self.open_output_file()
        nc = self.nc
        if self.params['write']:
              nc.add_dimension('release_group_dim', len(si.class_roles.release_groups))

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

        stats_grid= self.grid
        params= self.params
        info = self.info
        #todo mover from info to params??

        # default if no center given use release groups
        if params['grid_center'] is None:
            params['release_group_centered_grids'] = True
        else:
            if si.hydro_model_cords_in_lat_long:
                info['grid_center_lon_lat'] = params['grid_center'].copy()
                info['grid_center']= si._transform_lon_lat_to_meters( info['grid_center_lon_lat'], in_lat_lon_order=self.params['coords_in_lat_lon_order'])
            else:
                info['grid_center'] =  params['grid_center']

        gsize = np.asarray(params['grid_size'])
        gsize = gsize + (gsize+1) % 2  # grid size must be odd to ensure middle of center cell at mid point , a required by re
        gspan = params['grid_span']

        # make bin edges grid one larger than given grid_size  as (row, col), (y,x) size
        dx, dy = float(gspan[0]/gsize[1]), float(gspan[1]/gsize[0])

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
        s= (len(si.class_roles.release_groups), 1)
        stats_grid['x'] = np.tile(base_x[np.newaxis,:], s)
        stats_grid['y'] = np.tile(base_y[np.newaxis, :], s)
        stats_grid['x_bin_edges'] = np.tile(base_x_bin_edges[np.newaxis, :], s)
        stats_grid['y_bin_edges'] = np.tile(base_y_bin_edges[np.newaxis, :], s)
        stats_grid['cell_area'] = dx * dy

        if params['release_group_centered_grids']:
            # form grids around mean of each release group locations
            # loop over release groups to get bin edges
            for ngroup, name  in enumerate(si.class_roles.release_groups.keys()):
                rg = si.class_roles.release_groups[name]
                x0 = rg.info['bounding_box_ll_ul'] # works for point and polygon releases,
                x_release_group_center= np.nanmean(x0[:,:2], axis=0)
                stats_grid['x'][ngroup, :] += x_release_group_center[0]
                stats_grid['y'][ngroup, :] += x_release_group_center[1]
                stats_grid['x_bin_edges'][ngroup, :] += x_release_group_center[0]
                stats_grid['y_bin_edges'][ngroup, :] += x_release_group_center[1]
        else:
            # used same grid with single  given center for all particle release groups
            stats_grid['x'] += info['grid_center'][0]
            stats_grid['y'] += info['grid_center'][1]
            stats_grid['x_bin_edges'] += info['grid_center'][0]
            stats_grid['y_bin_edges'] += info['grid_center'][1]
        pass

        if self.params['write']:
            nc.add_dimension('x_dim', stats_grid['x'].shape[1])
            nc.add_dimension('y_dim', stats_grid['y'].shape[1])

    def set_up_binned_variables(self,nc):
        if not self.params['write']: return

        stats_grid = self.grid

        dim_names= ['time_dim', 'release_group_dim', 'y_dim', 'x_dim']
        dim_sizes =[None, len(si.class_roles.release_groups), stats_grid['y'].shape[1], stats_grid['x'].shape[1]]
        nc.create_a_variable('count', dim_names, np.int64, description= 'counts of particles in grid at given times, for each release group')
        nc.create_a_variable('count_all_particles', dim_names[:2], np.int64, description='counts of particles whether in grid or not')

        # set up space for requested particle properties
        # working count space, row are (y,x)
        self.count_time_slice = np.full(dim_sizes[1:], 0, np.int64)
        self.count_all_particles_time_slice = np.full((dim_sizes[1],), 0, np.int64)

        for p in self.params['particle_property_list']:
            if p in si.class_roles.particle_properties:
                self.sum_binned_part_prop[p] = np.full(dim_sizes[1:], 0.)  # zero for  summing
                nc.create_a_variable( 'sum_' + p, dim_names, np.float64, description= 'sum of particle property inside bin' )
            else:
                si.msg_logger.msg('Part Prop "' + p + '" not a particle property, ignored and no stats calculated',warning=True)

    def do_counts(self,n_time_step, time_sec, sel):
        # do counts for each release  location and grid cell
        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid

        # set up pointers to particle properties
        p_groupID = part_prop['IDrelease_group'].used_buffer()
        p_x= part_prop['x'].used_buffer()

        self.do_counts_and_summing_numba(p_groupID, p_x, stats_grid['x_bin_edges'], stats_grid['y_bin_edges'],
                                         self.count_time_slice, self.count_all_particles_time_slice, self.prop_data_list, self.sum_prop_data_list, sel)




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
                                 'max_age_to_bin':  PVC(si.info.large_float , float, min=1., doc_str='Max. particle age to count', units='sec'),
                                 'age_bin_size':    PVC(7*24*3600.,float,doc_str='Size of bins to count ages into, default= 1 week', units='sec'),
                                })

    def initial_setup(self):
        # set up info/attributes
        super().initial_setup()

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['age'])


    def set_up_time_bins(self,nc):
        # this set up age bins, not time
        ml = si.msg_logger
        stats_grid = self.grid

        # ages to bin particle ages into,  equal bins in given range
        age_min = abs(self.params['min_age_to_bin'])
        age_max = min(abs(self.params['max_age_to_bin']), si.run_info.duration)

        if age_max <= age_min:
            ml.msg(' parameter min_age_to_bin must be <  max_age_to_bin  (min,max)= '
                                    + str([age_min,age_max ]) + ', duration=' + str(si.run_info['duration']),
                   caller=self,   fatal_error=True)

        # set up age bin edges
        dage= abs((self.params['age_bin_size']))
        stats_grid['age_bin_edges'] = float(si.run_info.model_direction) * np.arange(age_min, age_max+dage, dage)

        if stats_grid['age_bin_edges'].shape[0] ==0:
            ml.msg('Particle Stats, aged based: no age bins, check parms min_age_to_bin < max_age_to_bin, if backtracking these should be negative',
                     caller=self, fatal_error=True)

        stats_grid['age_bins'] = 0.5 * (stats_grid['age_bin_edges'][1:] + stats_grid['age_bin_edges'][:-1])  # ages at middle of bins

    def set_up_binned_variables(self, nc):
        # set up space for requested particle properties based on asge

        ml = si.msg_logger
        stats_grid = self.grid

        dim_sizes= (stats_grid['age_bins'].shape[0], len(si.class_roles.release_groups), stats_grid['y'].shape[1], stats_grid['x'].shape[1])

        # working count space, row are (y,x)
        self.count_age_bins = np.full(dim_sizes, 0, np.int64)
        # counts in each age bin, whether inside grid cell or not
        self.count_all_particles =  np.full((stats_grid['age_bins'].shape[0], len(si.class_roles.release_groups)), 0, np.int64)

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

            if 0 <= na < (age_bin_edges.shape[0] - 1):
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

class GriddedStats3D_timeBased(GriddedStats2D_timeBased):
    # class to hold counts of particles inside 3D grid cells
    
    def __init__(self):
        # set up info/attributes
        super().__init__()
        # add 3D specific parameters
        self.add_default_params({
            'vertical_grid_size': PVC(20, int, min=1, max=10**3, 
                                    doc_str='Number of vertical grid cells'),
            'vertical_range': PCC([0.0, 100.0], single_cord=True, is3D=True,
                                  doc_str='Vertical extent of the statistics grid as (min, max). Depth is positive down e.g. 0 is surface and 100 is 100m below surface', 
                                  units='meters'),
            'role_output_file_tag': PVC('stats_gridded_time_3d', str),
        })

    def check_requirements(self):
        # Add z coordinate requirement
        self.check_class_required_fields_prop_etc(required_props_list=['x', 'status', 'z'])


    def info_to_write_at_end(self):
        nc = self.nc
        stats_grid = self.grid
        
        # Write x, y grid info using parent method
        super().info_to_write_at_end()
        
        # Write z grid info
        nc.write_a_new_variable('z', stats_grid['z'], ['release_group_dim', 'z_dim'], description='Mid point of vertical grid cell')

        # Calculate grid cell volume
        dx = np.diff(stats_grid['x_bin_edges'][0,:]).reshape(( 1, 1,-1))
        dy = np.diff(stats_grid['y_bin_edges'][0,:]).reshape(( 1,-1, 1)) 
        dz = np.diff(stats_grid['z_bin_edges'][0,:]).reshape((-1, 1, 1))
        volume = dx * dy * dz

        # Write grid cell volume
        nc.write_a_new_variable('grid_cell_volume', volume, ['z_dim', 'y_dim','x_dim'], 
                                description='Volume of each 3D grid cell')
        

    def set_up_spatial_bins(self, nc):
        # First set up x,y bins using parent method
        super().set_up_spatial_bins(nc)
        
        # Then add z bins
        stats_grid = self.grid
        params = self.params
        
        # Set up vertical grid
        vsize = params['vertical_grid_size']
        vmin, vmax = params['vertical_range']
        
        # Make vertical bin edges
        base_z_bin_edges = np.linspace(vmin, vmax, vsize +1)


        dz = float((vmax - vmin) / vsize)
        # Make vertical bin centers
        # via convolution
        base_z = 0.5 * (base_z_bin_edges[1:] + base_z_bin_edges[:-1])
        
        # make copies for each release group
        s= (len(si.class_roles.release_groups), 1)
        stats_grid['z'] = np.tile(base_z[np.newaxis,:], s)
        stats_grid['z_bin_edges'] = np.tile(base_z_bin_edges[np.newaxis,:], s)
        stats_grid['cell_volume'] = stats_grid['cell_area'] * dz

        if self.params['write']:
            nc.add_dimension('z_dim', vsize)

    def set_up_binned_variables(self, nc):
        if not self.params['write']: 
            return

        stats_grid = self.grid
        
        # Add z dimension to dimension lists
        dim_names = ['time_dim', 'release_group_dim', 'z_dim', 'y_dim', 'x_dim']
        dim_sizes = [None, len(si.class_roles.release_groups), 
                    stats_grid['z'].shape[1], stats_grid['y'].shape[1], stats_grid['x'].shape[1]]

        nc.create_a_variable('count', dim_names, np.int64, 
                          description='counts of particles in 3D grid at given times, for each release group')
        nc.create_a_variable('count_all_particles', dim_names[:2], np.int64,
                          description='counts of particles whether in grid or not')

        # Set up working count space
        self.count_time_slice = np.full(dim_sizes[1:], 0, np.int64)
        self.count_all_particles_time_slice = np.full((dim_sizes[1],), 0, np.int64)

        for p in self.params['particle_property_list']:
            if p in si.class_roles.particle_properties:
                self.sum_binned_part_prop[p] = np.full(dim_sizes[1:], 0.)
                nc.create_a_variable('sum_' + p, dim_names, np.float64,
                                   description='sum of particle property inside bin')
            else:
                si.msg_logger.msg('Part Prop "' + p + '" not a particle property, ignored and no stats calculated',
                                warning=True)

    @staticmethod
    @njitOT
    def do_counts_and_summing_numba(group_ID, x, x_edges, y_edges, z_edges, count, 
                                   count_all_particles, prop_list, sum_prop_list, sel):
        # Zero counts for this time slice
        count[:] = 0
        count_all_particles[:] = 0
        for m in range(len(prop_list)):
            sum_prop_list[m][:] = 0.

        for n in sel:
            ng = group_ID[n]
            count_all_particles[ng] += 1

            # Get grid spacings
            dx = x_edges[ng, 1] - x_edges[ng, 0]
            dy = y_edges[ng, 1] - y_edges[ng, 0]
            dz = z_edges[ng, 1] - z_edges[ng, 0]

            # Calculate grid indices
            r = int(np.floor((x[n, 1] - y_edges[ng,0]) / dy))  # row is y
            c = int(np.floor((x[n, 0] - x_edges[ng,0]) / dx))  # column is x
            k = int(np.floor((-x[n, 2] - z_edges[ng,0]) / dz))    # k is z

            # Check if particle is inside grid bounds
            if (0 <= r < y_edges.shape[1] - 1 and 
                0 <= c < x_edges.shape[1] - 1 and
                0 <= k < z_edges.shape[0] - 1):
                
                count[ng, k, r, c] += 1
                # Sum particle properties
                for m in range(len(prop_list)):
                    sum_prop_list[m][ng, k, r, c] += prop_list[m][n]

    def do_counts(self, n_time_step, time_sec, sel):
        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid

        # Get particle properties
        p_groupID = part_prop['IDrelease_group'].used_buffer()
        p_x = part_prop['x'].used_buffer()

        self.do_counts_and_summing_numba(p_groupID, p_x, 
                                      stats_grid['x_bin_edges'],
                                      stats_grid['y_bin_edges'],
                                      stats_grid['z_bin_edges'],
                                      self.count_time_slice,
                                      self.count_all_particles_time_slice,
                                      self.prop_data_list,
                                      self.sum_prop_data_list,
                                      sel)