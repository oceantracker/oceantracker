
import numpy as np
from oceantracker.util.numba_util import njitOT

from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats
#from oceantracker.util.parameter_checking import ParameterListCheckerV2 as PLC2
from oceantracker.shared_info import shared_info as si
from oceantracker.particle_statistics.gridded_statistics_2D import GriddedStats2D_timeBased


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