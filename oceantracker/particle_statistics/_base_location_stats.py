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

class _BaseParticleLocationStats(ParameterBaseClass):


    def __init__(self):
        # set up info/attributes
        super().__init__()

        self.add_default_params(
                update_interval =   PVC(60*60.,float,units='sec',
                               doc_str='Time in seconds between calculating statistics, wil be rounded to be a multiple of the particle tracking time step'),
                start =  PTC(None,doc_str= 'Start particle counting from this date-time, default is start of model run'),
                end =  PTC(None,  doc_str='Stop particle counting from this iso date-time, default is end of model run'),
                duration =  PVC(None, float, min=0.,units='sec',
                        doc_str='How long to do counting after start time, can be used instead of "end" parameter'),
                role_output_file_tag =            PVC('stats_base',str,doc_str='tag on output file for this class'),
                write =                       PVC(True,bool,doc_str='Write statistcs to disk'),
                status_list= PLC(['stationary','stranded_by_tide','on_bottom','moving'], str,
                                 doc_str='List of particle status types to count,eg  ["on_bottom","moving"], other status types will be ignored in statistcs',
                                 possible_values=si.particle_status_flags.possible_values()),
                z_min =  PVC(None, float, doc_str=' Count only those particles with vertical position >=  to this value', units='meters above mean water level, so is < 0 at depth'),
                z_max =  PVC( None, float,  doc_str='Count only those particles with vertical position <= to this value', units='meters above mean water level, so is < 0 at depth'),
                near_seabed=PVC(None, float, doc_str='Count only those particles within this distance of bottom', units='meters above seabed', min = 0.001),
                near_seasurface=PVC(None, float, doc_str='Count only those particles within this distance of tidal sea surface', units='meters below sea surface', min=0.001),

                water_depth_min =  PVC(None, float, min=0.,doc_str='Count only those particles in water depths greater than this value'),
                water_depth_max =  PVC(None, float,min=0., doc_str='Count only those particles in water depths less than this value'),
                particle_property_list = PLC(None, str, make_list_unique=True, doc_str='Create statistics for these named particle properties, list = ["water_depth"], for average of water depth at particle locations inside the counted regions') ,

                #coords_in_lat_lon_order =  PVC(False, bool,
                #    doc_str='Allows points to be given (lat,lon) and order will be swapped before use, only used if hydro-model coords are in degrees '),
                status_min=PVC('stationary', str, possible_values=si.particle_status_flags.possible_values(),obsolete=True,
                               doc_str='Use parameter "status_list" to name which status values to count, eg ["on_bottom","moving"]'),
                status_max=PVC('moving', str, possible_values=si.particle_status_flags.possible_values(),obsolete=True,
                             doc_str='Use parameter "status_list" to name which status values to count, eg ["on_bottom","moving"]'),
                )

        self.add_default_params(count_start_date= PTC(None,  obsolete=True,  doc_str='Use "start" parameter'),
                                count_end_date= PTC(None,   obsolete=True,  doc_str='Use "end" parameter'))
        self.nc = None
        info = self.info
        self.grid = {}
        self.sum_binned_part_prop = {}
        info['output_file'] = None
        self.role_doc('Particle statistics, based on spatial particle counts and particle properties in a grid or within polygons. Statistics are \n * separated by release group \n * can be a time series of statistics or put be in particle age bins.')

    def initial_setup(self):

        ml = si.msg_logger
        info = self.info
        params = self.params

        self.check_part_prop_list()
        # to spped status check make map with trues at index of status to include in counts
        self.statuses_to_count_map = status_util.build_select_status_map(params['status_list'])

        # set water depth range (not using tide)
        f = si.info.large_float
        info['water_depth_range'] = np.asarray([-f, f])
        if params['water_depth_min'] is not None:  info['water_depth_range'][0] = params['water_depth_min']
        if params['water_depth_max'] is not None:  info['water_depth_range'][1] = params['water_depth_max']

        if info['water_depth_range'][0] > info['water_depth_range'][1]:
            ml.msg(
                f'Require water_depth_min > water_depth_max, (water_depth_min,water_depth_max) =({info["water_depth_range"][0]:.3e}, {info["water_depth_range"][1]:.3e}) ',
                caller=self, error=True)
        # set what z values to count bewteen, or near sea bed etc in 2D counts
        self.set_z_range_for_counts()

        self.add_scheduler('count_scheduler', start=params['start'], end=params['end'], duration=params['duration'], interval=params['update_interval'], caller=self)
        pass

    def set_z_range_for_counts(self):
        # set particle depth and water depth limits for 2D counting of particles
        ml = si.msg_logger
        info = self.info
        params = self.params

        info['depth_sel_mode'] = 0
        f = si.info.large_float
        if params['z_min'] is not None or params['z_max'] is not None:
            # count based on give z values
            info['depth_sel_mode'] = 1
            info['z_range'] = np.asarray([-f, f])
            if params['z_min'] is not None:  info['z_range'][0] = params['z_min']
            if params['z_max'] is not None:  info['z_range'][1] = params['z_max']
            if info['z_range'][0] > info['z_range'][1]:
                ml.msg(f'Require zmin > zmax, (z_min,z_max) =({info["z_range"][0]:.3e}, {info["z_range"][1]:.3e}) ',
                       error=True, caller=self,
                       hint='z=0 is mean water level, so z is mostly < 0')

            if params['near_seabed'] is not None or params['near_seasurface'] is not None:
                ml.msg(f'Have set  one of params  "near_seabed" or  "near_seasurface" and also one of (z_min,z_max)',
                       fatal_error=True, caller=self,
                       hint='Cannot set both depth selections , add different particle_statistics  class for each type of depth selection')

        elif params['near_seabed'] is not None:
            info['depth_sel_mode'] = 2

        elif params['near_seasurface'] is not None:
            info['depth_sel_mode'] = 3


    def check_part_prop_list(self):

        part_prop = si.class_roles.particle_properties
        names=[]
        for name in self.params['particle_property_list']:

            si.msg_logger.spell_check(f'Particle property name "{name}" not recognised',
                                      name, si.class_roles.particle_properties.keys(),
                                      hint='check parameter "particle_property_list"',
                                      crumbs=f'Particle Statistic "{self.params["name"]}" >',
                                      caller = self)

            if part_prop[name].is_vector():
                si.msg_logger.msg('On the fly statistical Binning of vector particle properties,eg  "' + name + '" not yet implemented', warning=True)

            elif part_prop[name].get_dtype() != np.float64:
                si.msg_logger.msg(f'On the fly statistics can currently only track np.float64 particle properties, ignoring property  "{name}", of type "{str(part_prop[name].get_dtype())}"',
                                  warning=True)
            else:
                names.append(name)

        # set params to reduced list
        self.params['particle_property_list'] = names

    def set_up_spatial_bins(self):

        basic_util.nopass()

    def open_file_if_needed(self):
        info = self.info

        if self.nc is None:
            info['output_file'] = si.run_info.output_file_base + '_' + self.params['role_output_file_tag']
            info['output_file'] += f'_{info["instanceID"]:03}_{self.params["name"]}.nc'
            file_name = path.join(si.run_info.run_output_dir, info['output_file'])
            # add counting dims to file
            self.nc = self.open_output_file(file_name)

    def open_output_file(self,file_name):
        nc = NetCDFhandler(file_name, 'w')
        info = self.info
        for name, s in info['count_dims'].items():
            nc.create_dimension(name, s)
        return nc

    def create_time_variables(self):
        self.nWrites = 0
    def create_grid_variables(self):
        # creates 2D grid variables
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
    def create_polygon_variables_part_prop(self):
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
    def create_age_variables(self):
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


    def set_up_part_prop_lists(self):
        # set up list of part prop and sums to enable averaging of particle properties

        part_prop = si.class_roles.particle_properties
        self.prop_data_list, self.sum_prop_data_list = [],[]
        # todo put this in numba uti;, for other classes to use
        names=[]
        for key, prop in self.sum_binned_part_prop.items():
            if part_prop[key].is_vector():
                si.msg_logger.msg('On the fly statistical Binning of vector particle properties, eg.  "' + key + '" not yet implemented', warning=True)

            elif part_prop[key].get_dtype() != np.float64:
                si.msg_logger.msg(f'On the fly statistics  can currently only track float64 particle properties, ignoring property  "{key}", of type "{str(part_prop[key].get_dtype())}"',
                                  error=True)
            else:
                names.append(names)
                self.prop_data_list.append(part_prop[key].data) # must used dataptr here
                self.sum_prop_data_list.append(self.sum_binned_part_prop[key][:])

        # convert to a numba list
        if len(self.prop_data_list) ==0:
            # must set yp typed empty lists for numba to have right signatures of numba functions
            # make list the right shape and pop to make it empty
            #todo a cleaner way to do this with NumbaList.empty??
            self.prop_data_list =  NumbaList([np.empty((1,))])
            self.prop_data_list.pop(0)
            self.sum_prop_data_list = NumbaList([np.empty((1, 1, 1, 1))])
            self.sum_prop_data_list.pop(0)
        else:
            # otherwise use types of arrays
            self.prop_data_list = NumbaList(self.prop_data_list)
            self.sum_prop_data_list = NumbaList(self.sum_prop_data_list)
        pass


    # user overload this method to subset indicies in out of particles to count
    def select_particles_to_count(self, sel): # dummy method
        return sel

    def sel_depth_range(self,sel):
        # find subset of sel that meet depth range requirements
        part_prop = si.class_roles.particle_properties
        info = self.info
        params = self.params
        buffer = self.get_partID_buffer('depth_sel')
        match info['depth_sel_mode']:
            case 0:
                return sel # no depth selection
            case 1: # first select in z range
                return stats_util._sel_z_range(part_prop['x'].data, info['z_range'], sel, buffer)
            case 2: # near sea bed
                return stats_util._sel_z_near_seabed(part_prop['x'].data, part_prop['water_depth'].data, params['near_seabed'], sel, buffer)
            case 3:  # near sea surface
                return stats_util._sel_z_near_seasurface(part_prop['x'].data, part_prop['tide'].data, params['near_seasurface'], sel, buffer)


    def update(self,n_time_step, time_sec, alive):
        '''do particle counts'''
        part_prop = si.class_roles.particle_properties
        info = self.info
        self.start_update_timer()

        num_in_buffer = si.run_info.particles_in_buffer

        #  count alive particles in each release group (plus age for age based stats)
        # children must implement their own count_alive_particles

        # first select those to count based on status and z location
        sel = stats_util._sel_status_waterdepth(part_prop['status'].data,
                                    part_prop['x'].data, part_prop['water_depth'].data.ravel(),
                                    self.statuses_to_count_map, info['water_depth_range'],
                                    num_in_buffer, self.get_partID_buffer('B1'))

        if si.run_info.is3D_run:
            sel = self.sel_depth_range(sel)
        # users over ride thismethod  to further sub-select those to count
        sel = self.select_particles_to_count(sel)

        #update prop list data, as buffer may have expanded
        # todo , do this only when part buffer expansion occurs as array changes, add expanf bffer to all clases??
        part_prop = si.class_roles.particle_properties
        for n, name in enumerate(self.sum_binned_part_prop.keys()):
            self.prop_data_list[n]= part_prop[name].data

        self.do_counts(n_time_step, time_sec, sel, alive)

        self.write_time_varying_stats(time_sec)

        self.stop_update_timer()


    def write_time_varying_stats(self, time):
        # write nth step in file
        n_write = self.nWrites
        fh = self.nc.file_handle
        fh['time'][n_write] = time

        release_groups = si.class_roles.release_groups

        # write number released
        num_released = np.zeros((len(release_groups),), dtype=np.int32)
        for nrg, rg in enumerate(release_groups.values()):
            num_released[nrg] = rg.info['number_released']

        fh['num_released'][n_write, :] = num_released # for each release group so far
        fh['num_released_total'][n_write] = num_released.sum() # total all release groups so far

        fh['count'][n_write, ...] = self.count_time_slice[:, ...]
        fh['count_all_alive_particles'][n_write, ...] = self.count_all_alive_particles[:, ...]

        for key, item in self.sum_binned_part_prop.items():
            self.nc.file_handle['sum_' + key][n_write, ...] = item[:]  # write sums  working in original view
        self.nWrites += 1

    def info_to_write_on_file_close(self) : pass

    def close_file(self):
        nc = self.nc
        self.info_to_write_on_file_close()
        # write total released in each release group
        num_released = [i.info['number_released'] for name, i in si.class_roles.release_groups.items()]
        nc.write_variable('number_released_each_release_group', np.asarray(num_released, dtype=np.int64),
                          ['release_group_dim'], description='Total number released in each release group')

        nc.create_attribute('total_num_particles_released',
                            si.core_class_roles.particle_group_manager.info['particles_released'])
        nc.create_attribute('particle_status_values_counted', str(self.params['status_list']))
        nc.create_attribute('backtracking', int(si.settings.backtracking))
        nc.close()
        self.nc = None

    def save_state(self, si, state_dir):
        basic_util.nopass(f'Restarting from saved state using "save_state" and "restart" methods not yet implemented for class {self.__class__.__name__}S')

    def restart(self, state_info):
        # code require to reload save state for this class
        basic_util.nopass(f'Restarting from saved state using "save_state" and "restart" methods not yet implemented for class {self.__class__.__name__}S')

    def close(self):

        if self.params['write']:
            self.close_file()

    # add file variables
    def add_time_variables_to_file(self,nc):

        # stats time variables commute to all 	for progressive writing
        nc.create_variable('time', ['time_dim'], np.float64,
                           units='seconds since 1970-01-01 00:00:00',
                           description='time in seconds since 1970/01/01 00:00')

        # other output common to all types of stats
        nc.create_variable('num_released_total', ['time_dim'], np.int32, description='total number released')

        nc.create_variable('num_released', ['time_dim', 'release_group_dim'], np.int32,
                           description='number released so far from each release group')

    def add_grid_variables_to_file(self, nc):
        dn = si.dim_names
        stats_grid = self.grid

        dim_names = [key for key in self.info['count_dims']]
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

    def create_count_variables(self,dims:dict, mode:str):
        # set up space for requested particle properties
        # working count space, row are (y,x)
        params = self.params
        dim_sizes =[ val for val in dims.values()]

        if mode=='time':
            use_dims =dim_sizes[1:]
            self.count_time_slice = np.full(use_dims, 0, np.int64)
            self.count_all_alive_particles = np.full((use_dims[0],), 0, np.int64)

        elif mode =='age':
            use_dims = dim_sizes
            self.count_age_bins = np.full(use_dims, 0, np.int64)
            self.count_all_alive_particles = np.full(use_dims[:2], 0, np.int64)

        for p in params['particle_property_list']:
            self.sum_binned_part_prop[p] = np.full(use_dims, 0.)  # zero for  summing

    def add_grid_params(self):
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

    def add_polygon_params(self):
        self.add_default_params( polygon_list= [],
                                 use_release_group_polygons= PVC(False, bool,doc_str = 'Omit polygon_list param and use all polygon release polygons as statistics/counting polygons, useful for building release group polygon to polygon connectivity matrix.'),
                                 )
        self.info['type'] = 'polygon'

    def add_age_params(self):
        self.add_default_params({'role_output_file_tag': PVC('stats_gridded_age',str),
                                 'min_age_to_bin':  PVC(0.,float,min=0., doc_str='Min. particle age to count', units='sec'),
                                 'max_age_to_bin':  PVC(None , float, min=1., doc_str='Max. particle age to count', units='sec', is_required=True),
                                 'age_bin_size':    PVC(7*24*3600.,float,min=1,doc_str='Size of bins to count ages into, default= 1 week', units='sec'),
                                })