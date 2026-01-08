from os import path

import numba

from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, merge_params_with_defaults
from oceantracker.util.parameter_checking import ParameterCoordsChecker as PCC, ParameterTimeChecker as PTC
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util import cord_transforms, regular_grid_util
from oceantracker.particle_statistics.util import stats_util

import numpy  as np
from oceantracker.shared_info import shared_info as si


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
        counts_released_age_binned = self._add_age_binned_release_counts_to_file(nc)

        # add connectives, works for both polygon and grid stats, using s to reshape
        s = list(counts_inside_age_bins.shape[:2]) + (counts_inside_age_bins.ndim - counts_released_age_binned.ndim) * [1]
        with np.errstate(divide='ignore', invalid='ignore'):
            connectivity_matrix = counts_inside_age_bins / counts_released_age_binned.reshape(s)
        connectivity_matrix[~np.isfinite(connectivity_matrix)] = np.nan

        nc.write_variable('connectivity_matrix', connectivity_matrix, dim_names,
                          description='Age binned connectivity of each polygon as fraction =counts_inside/ counts_released_age_binned, ie includes dead and those outside open boundaries ')

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

    # setup and record number released for global counts of all released particles
    def _setup_release_counts(self):

        n_release = len(si.class_roles.release_groups)
        n_updates = self.schedulers['count_scheduler'].scheduled_times.size
        self.number_released_so_far= np.zeros((n_updates, n_release), dtype=np.int64)
        pass

    def _update_release_counts(self):
        nt = self.update_count
        for nrg, (name, i) in  enumerate(si.class_roles.release_groups.items()):
            self.number_released_so_far[nt, nrg] = i.info['number_released']

    def _add_age_binned_release_counts_to_file(self,nc):
        stats_grid = self.grid
        dn = si.dim_names
        n_times = self.update_count
        times =  self.schedulers['count_scheduler'].scheduled_times[:n_times]
        nc.write_variable('time_of_count',times, [dn.time], units='sec', description='times counts made for age stats')

        number_released_to_date=  self.number_released_so_far[:n_times, :]
        nc.write_variable('number_released_to_date',  number_released_to_date, [dn.time, dn.release_group],
                            description='total number released since start of run at counting times for  each release group')

        # age bin all released particles
        counts_released_age_binned= self._age_binned_release_counts(times, number_released_to_date, stats_grid['age_bin_edges'])
        nc.write_variable('counts_released', counts_released_age_binned, [dn.age_bin, dn.release_group],
                                description='all particles released in age bins for each release group')
        return  counts_released_age_binned

    def save_state(self, si, state_dir):
        fn = path.join(state_dir,f'stats_state_{self.params["name"]}.nc')
        nc = NetCDFhandler(fn,mode='w')
        self.info_to_write_on_file_close(nc)
        nc.close()
        return fn

    def restart(self, state_info):
        file_name = state_info['stats_files'][self.params['name']]
        nc = NetCDFhandler(file_name, mode='r')

        self.counts_inside_age_bins = nc.read_variable('count')
        self.count_all_alive_particles = nc.read_variable('count_all_alive_particles')

        # insert number released so far
        c = nc.read_variable('number_released_to_date')
        self.number_released_so_far[:c.shape[0], :] = c

        # copy in summed properties, to preserve references in sum_prop_data_list that is used inside numba
        for name, s in self.sum_binned_part_prop.items():
            self.sum_binned_part_prop[name][:] = nc.read_variable(f'sum_{name}')

        nc.close()
        pass
    pass

    @staticmethod
    @numba.njit
    def _age_binned_release_counts(times, number_released_to_date, age_bin_edges):
        age_binned_counts = np.zeros((age_bin_edges.size-1,number_released_to_date.shape[1]), dtype=np.int64)
        for nt, time in enumerate(times):
            age = time - times[0]
            na = stats_util._get_age_bin(age, age_bin_edges)  # time is age at this time step
            if 0 <= na < (age_bin_edges.shape[0] - 1):
                for nrg in range(number_released_to_date.shape[1]):
                    age_binned_counts[na, nrg] += number_released_to_date[nt, nrg]

        return age_binned_counts

class _BaseGrid2DStats(ParameterBaseClass):

    def _add_2D_grid_params(self):
        self.add_default_params({

            'grid_size': PLC([100, 99], int, fixed_len=2, min=1, max=10 ** 5,
                             doc_str='number of (rows, columns) in grid, where rows is y size, cols x size, values should be odd, so will be rounded up to next '),
            'release_group_centered_grids': PVC(False, bool,
                                                doc_str='Center grid on the release groups  mean horizontal location or center of release polygon. '),
            'grid_center': PCC(None, single_cord=True, is3D=False,
                               doc_str='center of the statistics grid as (x,y), must be given if not using  release_group_centered_grids',
                               units='meters'),
            'grid_span': PLC(None, float, doc_str='(width-x, height-y)  of the statistics grid',
                             units='meters (dx,dy) or degrees (dlon, dlat) if geographic',
                             is_required=True),
            'role_output_file_tag': PVC('stats_gridded_time_2D', str),
        })
        self.info['type'] = 'gridded'

    def _create_grid_variables(self):
        # creates 2D grid variables
        stats_grid = self.grid
        params = self.params
        info = self.info
        # todo mover from info to params??

        # default if no center given use release groups
        if params['grid_center'] is None:
            params['release_group_centered_grids'] = True

        if params['release_group_centered_grids']:
            # get centers from midrelease group
            # loop over release groups to get bin edges
            params['grid_centers'] = np.zeros((len(si.class_roles.release_groups), 2), dtype=np.float64)
            for ngroup, name in enumerate(si.class_roles.release_groups.keys()):
                rg = si.class_roles.release_groups[name]
                x0 = rg.info['bounding_box_ll_ul']  # works for point and polygon releases,
                params['grid_centers'][ngroup, :] = np.nanmean(x0[:, :2], axis=0)
        else:
            # use given grid centers
            if params['grid_centers'].shape[0] == 1:
                # if only one use all  for all
                params['grid_centers'] = np.tile(params['grid_center'], (len(si.class_roles.release_groups), 1))
            else:
                # one for each release group
                if params['grid_centers'].shape[0] != len(si.class_roles.release_groups):
                    si.msg_logger.msg(
                        'Number of points in "grid_centers" param. is >1 , then it must have the same number of center points',
                        hint=f'Number of points given = {info["grid_centers"].shape[0]}  number of release groups= {len(si.class_roles.release_groups)} ',
                        fatal_error=True, caller=self)
                params['grid_centers'] = params['grid_centers'].shape[0]

        # ensure grid size is odd, so that center of middle cell is at grid center coods
        grid_size = params['grid_size'][:2] + (np.asarray(params['grid_size'][:2]) % 2 == 0).astype(np.int32)

        # make space for coords
        n_grids = params['grid_centers'].shape[0]  #
        s1 = [n_grids, ] + grid_size.tolist()
        s2 = [n_grids, ] + (grid_size + 1).tolist()
        stats_grid['x_grid'] = np.zeros(s1, dtype=np.float64)
        stats_grid['y_grid'] = np.zeros(s1, dtype=np.float64)
        stats_grid['cell_area'] = np.zeros(s1, dtype=np.float64)
        stats_grid['x_bin_edges'] = np.zeros([n_grids, grid_size[1] + 1], dtype=np.float64)
        stats_grid['y_bin_edges'] = np.zeros([n_grids, grid_size[0] + 1], dtype=np.float64)

        # grids may have release group centers, so grid coords differ by release group
        for n_grid, p in enumerate(params['grid_centers']):
            x_cell_edges, y_cell_edges, info['bounding_box'] = regular_grid_util.make_regular_grid(
                                        params['grid_centers'][n_grid, :],  grid_size + 1, params['grid_span'])
            # get midpoints of cells
            x_grid = 0.5 * (x_cell_edges[:-1, 1:] + x_cell_edges[:-1, :-1])
            y_grid = 0.5 * (y_cell_edges[1:, :-1] + y_cell_edges[:-1, :-1])

            stats_grid['x_bin_edges'][n_grid, ...] = x_cell_edges[0, :]
            stats_grid['y_bin_edges'][n_grid, ...] = y_cell_edges[:, 0]

            stats_grid['x_grid'][n_grid, ...] = x_grid
            stats_grid['y_grid'][n_grid, ...] = y_grid

            if False:
                # check grid points
                from matplotlib import pyplot as plt
                plt.scatter(x_cell_edges, y_cell_edges, color='r')
                plt.scatter(stats_grid['x_grid'][n_grid, ...], stats_grid['y_grid'][n_grid, ...], color='g')
                plt.show(block=True)

            # get cell area im meters even if in geographic coords
            x, y = x_cell_edges.copy(), y_cell_edges.copy()

            if si.settings.use_geographic_coords:
                x, y = cord_transforms.local_grid_deg_to_meters(x, y, x[0, 0], y[0, 0])
            stats_grid['cell_area'][n_grid, :, :] = (x[:-1, 1:] - x[:-1, :-1]) * (y[1:, :-1] - y[:-1:, :-1])

        # non meshed versions
        stats_grid['x'] = stats_grid['x_grid'][:, 0, :]
        stats_grid['y'] = stats_grid['y_grid'][:, :, 0]

        # spacings the same for all release group grids, in meters  degrees
        stats_grid['grid_spacings'] = np.asarray([x[1, 1] - x[0, 0], y[1, 1] - y[0, 0]])
        params['grid_size'][:2] = grid_size
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
                p = merge_params_with_defaults(p, si.default_polygon_dict_params,
                                               si.msg_logger, crumbs='polygon_statistics_merging polygon list')

        if len(params['polygon_list']) == 0:
            ml.msg('Must have polygon_list parameter  with at least one polygon dictionary', caller=self,
                   fatal_error=True, hint='eg. polygon_list =[ {"points": [[2.,3.],....]} ]')

        # make a particle property to hold which polygon particles are in, but need instanceID to make it unique beteen different polygon stats instances
        info['inside_polygon_particle_prop'] = f'inside_polygon_for_onfly_stats_{self.info["instanceID"]:03d}'
        si.add_class('particle_properties', class_name='InsidePolygonsNonOverlapping2D',
                     name=info['inside_polygon_particle_prop'], initialize=True,
                     polygon_list=params['polygon_list'], write=False)