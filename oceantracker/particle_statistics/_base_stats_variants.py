from os import path
from copy import copy
import numba

from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, merge_params_with_defaults
from oceantracker.util.parameter_checking import ParameterCoordsChecker as PCC, ParameterTimeChecker as PTC
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util import cord_transforms, regular_grid_util
from oceantracker.particle_statistics.util import stats_util

import numpy  as np
from oceantracker.shared_info import shared_info as si
from oceantracker.util.numba_util import njitOT

# compile this constant into numba cod
status_outside_open_boundary = int(si.particle_status_flags.outside_open_boundary)

class _BaseTimeStats(ParameterBaseClass):

    def _add_time_params(self):
        self.add_default_params( )

    def _create_common_time_varying_stats(self,nc):
        params = self.params
        dims =  self.info['count_dims']
        dim_names =  stats_util.get_dim_names(dims)
        nc.create_variable('count_all_alive_particles', dim_names[:2], np.int64,
                           compression_level=si.settings.NCDF_compression_level,
                           description='counts of all alive particles everywhere')
        nc.create_variable('count', dim_names, np.int64, compression_level=si.settings.NCDF_compression_level,
                           description='counts of particles in spatial bins at given times, for each release group')

        if 'particle_property_list' in params:
            for p in params['particle_property_list']:
                nc.create_variable('sum_' + p,dim_names, dtype= np.float64, description= f'sum of particle property {p} inside bin')
                nc.create_variable(p, dim_names, dtype=np.float32, description=f'Average particle property {p} inside cell  = sum prop/counts_inside')

    def count_all_currently_alive(self, alive):
        part_prop = si.class_roles.particle_properties
        self._count_all_alive_time(part_prop['status'].used_buffer(), part_prop['IDrelease_group'].data,
                                         self.count_all_alive_particles, alive)
    @staticmethod
    @njitOT
    def _count_all_alive_time(status, release_group, count_all_alive, alive):
        count_all_alive[:] = 0.

        for nn in range(alive.size):
            n = alive[nn]
            count_all_alive[release_group[n]] += status[n] >= status_outside_open_boundary
        pass

    def _write_common_time_varying_stats(self, time_sec):
        # write nth step in file
        n_write = self.nWrites
        fh = self.nc.file_handle
        fh['time'][n_write] = time_sec

        release_groups = si.class_roles.release_groups

        # write number released
        num_released = np.zeros((len(release_groups),), dtype=np.int32)
        for nrg, rg in enumerate(release_groups.values()):
            num_released[nrg] = rg.info['number_released']

        fh['num_released'][n_write, :] = num_released # for each release group so far
        fh['num_released_total'][n_write] = num_released.sum() # total all release groups so far

        fh['count'][n_write, ...] = self.counts_inside_time_slice[:, ...]
        fh['count_all_alive_particles'][n_write, ...] = self.count_all_alive_particles[:, ...]

        for key, item in self.sum_binned_part_prop.items():
            fh['sum_' + key][n_write, ...] = item[:]  # write sums  working in original view

            # write mean
            with np.errstate(divide='ignore', invalid='ignore'):
                val = item / self.counts_inside_time_slice  # calc mean
            val[~np.isfinite(val)] = np.nan
            fh[key][n_write, ...] = val[:]  # write sums  working in original view

    # add file variables
    def _create_time_file_variables(self, nc):

        # stats time variables commute to all 	for progressive writing
        nc.create_variable('time', ['time_dim'], np.float64,
                           units='seconds since 1970-01-01 00:00:00',
                           description='time in seconds since 1970/01/01 00:00 counts were made')

        # other output common to all types of stats
        nc.create_variable('num_released_total', ['time_dim'], np.int32, description='total number released to date')

        nc.create_variable('num_released', ['time_dim', 'release_group_dim'], np.int32,
                           description='number released so far from each release group')


class _BaseAgeStats(ParameterBaseClass):

    def _add_age_params(self):
        self.add_default_params({
                 'min_age_to_bin': PVC(0., float, min=0., doc_str='Min. particle age to count',
                                       units='sec'),
                 'max_age_to_bin': PVC(None, float, min=1., doc_str='Max. particle age to count',
                                       units='sec', is_required=True),
                 'age_bin_size': PVC(None, float, min=1,
                                     doc_str='Size of bins to count ages into',
                                     units='sec', is_required=True),
                                 })

    def _create_age_variables(self):
        # this set up age bins, not time
        params = self.params
        ml = si.msg_logger
        stats_grid = self.grid

        # check age limits to bin particle ages into,  equal bins in given range
        params['max_age_to_bin'] = max(params['age_bin_size'], params['max_age_to_bin']) # at least one bin
        if params['min_age_to_bin'] >=  params['max_age_to_bin']: params['min_age_to_bin'] = 0
        age_range = params['max_age_to_bin'] - params['min_age_to_bin']
        if params['age_bin_size'] > age_range:  params['age_bin_size'] = age_range

        # set up age bin edges
        dage= params['age_bin_size']
        stats_grid['age_bin_edges'] = float(si.run_info.model_direction) * np.arange(params['min_age_to_bin'], params['max_age_to_bin']+dage, dage)

        if stats_grid['age_bin_edges'].shape[0] ==0:
            ml.msg('Particle Stats, aged based: no age bins, check parms min_age_to_bin < max_age_to_bin',
                     caller=self, error=True)
        if stats_grid['age_bin_edges'].shape[0] >10000:
            ml.msg('Particle Stats, aged based: there are more than 10,000  age bins, may run out of memory?',
                caller=self, strong_warning=True)

        stats_grid['age_bins'] = 0.5 * (stats_grid['age_bin_edges'][1:] + stats_grid['age_bin_edges'][:-1])  # ages at middle of bins


    def count_all_alive_by_age(self, alive):
        part_prop = si.class_roles.particle_properties
        stats_grid = self.grid
        release_groupID = part_prop['IDrelease_group'].used_buffer()
        self._count_all_alive_age_bins(part_prop['status'].data,
                            part_prop['IDrelease_group'].data,
                            part_prop['age'].data,  stats_grid['age_bin_edges'],
                            self.count_all_alive_particles, alive)

    @staticmethod
    @njitOT
    def _count_all_alive_age_bins(status, release_group, age, age_bin_edges, count_all_alive, alive):
        da = age_bin_edges[1] - age_bin_edges[0]

        for nn in range(alive.size):
            n = alive[nn]
            na = int(np.floor((age[n] - age_bin_edges[0]) / da))
            if 0 <= na < (age_bin_edges.size - 1):
                count_all_alive[na, release_group[n]] += status[n] >= status_outside_open_boundary

    def info_to_write_on_file_close(self, nc):
        # write variables whole
        stats_grid = self.grid
        counts_inside_age_bins = self.counts_inside_age_bins

        dim_names =  stats_util.get_dim_names(self.info['count_dims'])
        nc.write_variable('count', counts_inside_age_bins, dim_names,
                          description='counts of particles in each stats polygon at given ages, for each release group')

        nc.write_variable('count_all_alive_particles', self.count_all_alive_particles, dim_names[:2],
                          description='counts of  all alive particles, not just those selected to be counted')

        self._add_age_bins_to_file(nc)

        # add connectives, works for both polygon and grid stats, using s to reshape
        s = list(counts_inside_age_bins.shape[:2]) \
                    + (counts_inside_age_bins.ndim - self.count_all_alive_particles.ndim) * [ 1]
        with np.errstate(divide='ignore', invalid='ignore'):
            connectivity_matrix = counts_inside_age_bins / self.count_all_alive_particles.reshape(s)

        connectivity_matrix[~np.isfinite(connectivity_matrix)] = np.nan

        nc.write_variable('connectivity_matrix', connectivity_matrix, dim_names,
                          description='Age binned connectivity of each polygon as fraction =counts_inside/ counts_all_alive (includes thoise  outside open boundaries )')

        # particle property sums
        for key, item in self.sum_binned_part_prop.items():
            # need to write final sums of properties  after all age counts done across all times
            nc.write_variable('sum_' + key, item[:], dim_names, description='sum of particle property inside bin  ' + key)
            name = key.removeprefix('sum_')
            with np.errstate(divide='ignore', invalid='ignore'):
                val = item / self.counts_inside_age_bins  # calc mean
            val[~np.isfinite(val)] = np.nan
            nc.write_variable(key, val, dim_names, dtype=np.float32,
                              description=f'Average particle property {name} for particles inside bin  = sum_{key}/counts_inside')

    def _add_age_bins_to_file(self,nc):
        stats_grid = self.grid
        nc.write_variable('age_bins', stats_grid['age_bins'], [si.dim_names.age_bin], units='sec',
                                        description='center of stats. age bin')
        nc.write_variable('age_bin_edges', stats_grid['age_bin_edges'], [si.dim_names.age_bin_edges],units='sec',
                                        description='edges of stats. age bins')



    def save_state(self, si, state_dir):
        fn = path.join(state_dir,f'stats_state_{self.params["name"]}.nc')
        nc = NetCDFhandler(fn,mode='w')
        self.info_to_write_on_file_close(nc)
        nc.close()
        return fn

    def restart(self, state_info):
        # open "saved state" stats file
        saved_state_file_name = state_info['stats_files'][self.params['name']]
        nc = NetCDFhandler(saved_state_file_name, mode='r')

        self.counts_inside_age_bins = nc.read_variable('count')
        self.count_all_alive_particles = nc.read_variable('count_all_alive_particles')

        # copy in summed properties, to preserve references in sum_prop_data_list that is used inside numba
        for name, s in self.sum_binned_part_prop.items():
            self.sum_binned_part_prop[name][:] = nc.read_variable(f'sum_{name}')

        nc.close()

        # reopen the output file
        output_stats_file_name = path.join(si.run_info.run_output_dir,state_info['stats_files'][self.params['name']].split('/')[-1])
        nc = NetCDFhandler(output_stats_file_name, 'w')

        self.nc = nc


class _BaseGrid2DStats(ParameterBaseClass):

    def _add_2D_grid_params(self):
        self.add_default_params({

            'release_group_centered_grids': PVC(False, bool,
                                                doc_str='Center grid on the release groups  mean horizontal location or center of release polygon. '),
            'output_file_base': PVC('stats_gridded_time_2D', str, doc_str='start of output file names'),
        })
        regular_grid_util.add_grid_default_params(self.default_params, grid_center_required=False)

        self.info['type'] = 'gridded'

    def _create_grid_variables(self):
        # creates 2D grid variables
        stats_grid = self.grid
        params = self.params
        info = self.info

        if params['release_group_centered_grids']  :
            # get centers of each grid as middle of each release group
            info['grid_centers'] = np.zeros((len(si.class_roles.release_groups), 2), dtype=np.float64)
            for ngroup, name in enumerate(si.class_roles.release_groups.keys()):
                rg = si.class_roles.release_groups[name]
                x0 = rg.info['bounding_box_ll_ul']  # works for point and polygon releases,
                info['grid_centers'][ngroup, :] = np.nanmean(x0[:, :2], axis=0)
        elif params['grid_center'] is not None:
            # use given grid center for all release groups
            info['grid_centers'] = np.tile(params['grid_center'], (len(si.class_roles.release_groups), 1))
        else:
            si.msg_logger.msg('For gridded stats must supply a "grid_center"  or set "release_group_centered_grids=True"',
                        hint=f'Set one of these parameters for gridded stat {params["name"]}', fatal_error=True, caller=self)

        # make space for coords
        # dummy call build grid to check for deprecated params, eg get new params rows, cols , span_x, span_y
        regular_grid_util.build_grid_from_params(params, self, center=info['grid_centers'][0])

        n_grids = info['grid_centers'].shape[0]
        stats_grid['cell_area'] = np.zeros((n_grids,params['rows'],params['cols']), dtype=np.float64)
        stats_grid['x_bin_edges'] = np.zeros([n_grids, params['cols']+1], dtype=np.float64)
        stats_grid['y_bin_edges'] = np.zeros([n_grids, params['rows']+1], dtype=np.float64)
        stats_grid['x'] = np.zeros([n_grids, params['cols']], dtype=np.float64)
        stats_grid['y'] = np.zeros([n_grids, params['rows']], dtype=np.float64)
        stats_grid['x_grid'] = np.zeros([n_grids, params['rows'], params['cols']], dtype=np.float64)
        stats_grid['y_grid'] = np.zeros(stats_grid['x_grid'].shape, dtype=np.float64)
        stats_grid['cell_area'] = np.zeros(stats_grid['x_grid'].shape, dtype=np.float64)

        # grids may have release group centers, so grid coords differ by release group
        for n_grid, p in enumerate(info['grid_centers']):
            x_cell_edges, y_cell_edges, info['bounding_box'] = regular_grid_util.build_grid_from_params(
                                                                            params,self,center=p)
            x_cell_edges,y_cell_edges = x_cell_edges[0, :],y_cell_edges[:, 0] # all the same so take one col or row
            stats_grid['x_bin_edges'][n_grid, ...] = x_cell_edges
            stats_grid['y_bin_edges'][n_grid, ...] = y_cell_edges

            # non-meshed versions of grid centers
            stats_grid['x'][n_grid,...]  = 0.5 * (x_cell_edges[1:] + x_cell_edges[:-1])
            stats_grid['y'][n_grid, ...] = 0.5 * (y_cell_edges[1:] + y_cell_edges[:-1])
            # get full grid of coords
            stats_grid['x_grid'][n_grid,...],stats_grid['y_grid'][n_grid,...]\
                                = np.meshgrid( stats_grid['x'][n_grid,...], stats_grid['y'][n_grid,...])

            # get cell area im meters even if in geographic coords
            # all grids have same cell sizes, but cell area varies across grid if in geographic coords
            x, y = stats_grid['x_bin_edges'][n_grid,...], stats_grid['y_bin_edges'][n_grid,...]
            x,y = np.meshgrid(x, y)
            if si.settings.use_geographic_coords:
                x, y = cord_transforms.local_grid_deg_to_meters(x, y, x[0, 0], y[0, 0])
            stats_grid['cell_area'][n_grid,...] = (x[ 1:, 1:] - x[ :-1, :-1]) * (y[ 1:, 1:] - y[:-1, :-1])

        # spacings the same for all cells and release group grids, whether in meters or degrees
        stats_grid['grid_spacings'] = np.asarray([stats_grid['x_bin_edges'][0, 1] - stats_grid['x_bin_edges'][0, 0],
                                                  stats_grid['y_bin_edges'][0, 1] - stats_grid['y_bin_edges'][0, 0]])
        pass


    def add_grid_variables_to_file(self, nc):
        dn = si.dim_names
        stats_grid = self.grid

        dim_names =  stats_util.get_dim_names(self.info['count_dims'])
        nc.write_variable('x', stats_grid['x'], [dim_names[1], dim_names[3]], description='Mid point of grid cell',
                          units='m or deg')
        nc.write_variable('y', stats_grid['y'], [dim_names[1], dim_names[2]],
                          description='Mid point of grid cell', units='m or degrees',)

        nc.write_variable('x_grid', stats_grid['x_grid'],dim_names[1:4]                        ,
                          description='x for mid point of grid cell, full grid',  units='m or degrees')
        nc.write_variable('y_grid', stats_grid['y_grid'], dim_names[1:4],
                          description='y for mid point of grid cell, full grid', units='m or degrees')
        nc.write_variable('cell_area', stats_grid['cell_area'], dim_names[1:4],
                          description='Horizontal area of each cell', units='m^2')
        nc.write_variable('grid_spacings', stats_grid['grid_spacings'], 'spacings_dim',
                          description='x for mid point of grid cell, full grid', units='m or degrees')

class _BasePolygonStats(ParameterBaseClass):
    def _add_polygon_params(self):
        self.add_default_params(polygon_list=[],
                                use_release_group_polygons=PVC(False, bool,
                                                               doc_str='Omit polygon_list param and use all polygon release polygons as statistics/counting polygons, useful for building release group polygon to polygon connectivity matrix.'),
                                )
        self.info['type'] = 'polygon'

    def _create_polygon_variables_part_prop(self):
        ml = si.msg_logger
        params = self.params
        info = self.info
        # pre fill  polygon list from release groups if requested
        if params['use_release_group_polygons']:
            params['polygon_list'] = []
            for name, i in si.class_roles.release_groups.items():
                if i.info['release_type'] == 'polygon':
                    params['polygon_list'].append({'name': name, 'points': i.params['points']})

            if len(params['polygon_list']) == 0:
                ml.msg('There are no polygon releases to use as statistic polygons',
                       hint='must have at least one polygon release defined to use the use_release_group_polygons parameter, or use statistics polygon_list parameter',
                       fatal_error=True, caller=self)
        else:
            # use given polygon list
            for n, p in enumerate(params['polygon_list']):
                p = merge_params_with_defaults(p, si.default_polygon_dict_params, si.msg_logger)

        if len(params['polygon_list']) == 0:
            ml.msg('Must have polygon_list parameter  with at least one polygon dictionary', caller=self,
                   fatal_error=True, hint='eg. polygon_list =[ {"points": [[2.,3.],....]} ]')

        # make a particle property to hold which polygon particles are in, but need instanceID to make it unique beteen different polygon stats instances
        info['inside_polygon_particle_prop'] = f'inside_polygon_for_onfly_stats_{self.info["instanceID"]:03d}'
        si.add_class('particle_properties', class_name='InsidePolygonsNonOverlapping2D',
                     name=info['inside_polygon_particle_prop'], initialize=True,
                     polygon_list=params['polygon_list'], write=False)