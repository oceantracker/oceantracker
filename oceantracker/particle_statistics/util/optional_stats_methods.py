import numpy as np
from oceantracker.util import basic_util, status_util
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util.parameter_base_class import ParameterBaseClass
from os import  path
from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC
from oceantracker.util.parameter_checking import ParameterCoordsChecker as PCC, ParameterTimeChecker as PTC
from oceantracker.util.parameter_checking import  merge_params_with_defaults
from numba.typed import List as NumbaList
from oceantracker.util import cord_transforms
from oceantracker.particle_statistics.util import stats_util
from oceantracker.shared_info import shared_info as si
class _OptionalStatsMethods(ParameterBaseClass):
    '''
    Methods addded to base class but used by only some stats variants
    '''

    def _add_polygon_params(self):
        self.add_default_params(polygon_list=[],
                                use_release_group_polygons=PVC(False, bool,
                                                               doc_str='Omit polygon_list param and use all polygon release polygons as statistics/counting polygons, useful for building release group polygon to polygon connectivity matrix.'),
                                )
        self.info['type'] = 'polygon'


    def _create_grid_variables(self):
        # creates 2D grid variables
        stats_grid= self.grid
        params= self.params
        info = self.info
        #todo mover from info to params??

        # default if no center given use release groups
        if params['grid_center'] is None:
            params['release_group_centered_grids'] = True

        if params['release_group_centered_grids']:
            # get centers from midrelease group
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

        # grids may have release group centers, so grid coords differ by release group
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
                x, y = cord_transforms.local_grid_deg_to_meters(x,y, x[0,0], y[0,0])
            stats_grid['cell_area'][n_grid, :, :] =(x[:-1, 1:]-x[:-1, :-1])*(y[1:,:-1]-y[:-1:,:-1])

        #spacings the same for all release group grids
        stats_grid['grid_spacings'] = np.asarray([base_x[1] - base_x[0], base_y[1] - base_y[0], ])
        pass

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
                     name=info['inside_polygon_particle_prop'],initialize=True,
                     polygon_list=params['polygon_list'], write=False)





