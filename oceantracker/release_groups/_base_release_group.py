import numpy as np
from time import  perf_counter
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import  ParameterListChecker as PLC, ParameterCoordsChecker as PCC
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterTimeChecker as PTC
from numba import njit
from oceantracker.util.numba_util import njitOT
from oceantracker.util.basic_util import nopass
from oceantracker.shared_info import shared_info as si

class _BaseReleaseGroup(ParameterBaseClass):
    def __init__(self):
        super().__init__() # get parent defaults
        self.add_default_params(
            pulse_size =  PVC(1, int, min=1, doc_str='Number of particles released in a single pulse, this number is released every release_interval.'),
            release_interval =  PVC(0., float, min=0., units='sec', doc_str='Time interval between released pulses. To release at only one time use release_interval=0.'),
            start =PTC(None,doc_str='start date/time of first release" '),
            end =  PTC(None,doc_str='date/time of lase release, ignored if duration given'),
            duration =  PVC(None, float, min=0.,units='sec',
                            doc_str='How long particles are released for after they start being released, ie releases stop this time after first release.,an alternative to using "end"'),
            #coords_in_lat_lon_order=PVC(False, bool,
             #       doc_str='If hindcast is in geographic coords, allow user to give release point locations in (lat, lon) order rather than default (lon,lat) order.'),

            max_age =  PVC(None, float, min=1., units='sec',
                      doc_str='Particles older than this age in seconds are culled,ie. status=dead, and removed from computation, very useful in reducing run time'),
            user_release_groupID =  PVC(0, int, doc_str='User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.'),
            user_release_group_name =  PVC('no_given', str, doc_str='User given name/label to attached to this release groups to make it easier to distinguish.'),
            allow_release_in_dry_cells =  PVC(False, bool,
                    doc_str='Allow releases in cells which are currently dry, ie. either permanently dry or temporarily dry due to the tide.'),
            z_range =  PLC(None, float, min_len=2,  obsolete=True,  doc_str='use z_min and/or z_max'),
            z_min =  PVC(None, float, doc_str='min/ deepest z value to release for to randomly release in 3D, overrides any given release z value'),
            z_max =  PVC(None, float, doc_str='max/ highest z vale release for to randomly release in 3D, overrides any given release z value'),
            release_offset_from_surface_or_bottom =  PVC(0., float, min=0.,
                                                    doc_str=' 3D release particles at offset from free surface or bottom, if release_at_surface or  release_at_bottom = True', units='m'),
            release_at_surface =  PVC(False, bool, doc_str=' 3D release particles at free surface, ie tide height, with  offset given by release_offset_from_surface_or_bottom param, overrides any given release z value'),
            release_at_bottom =  PVC(False, bool, doc_str=' 3D release particles at bottom, with  offset given by release_offset_from_surface_or_bottom param, overrides any given release z value'),
            water_depth_min =  PVC(None, float,doc_str='min water depth to release in, normally >0, useful for releases with a depth rage, eg larvae from inter-tidal shellfish', units='m'),
            water_depth_max =  PVC(None, float, doc_str='max water depth to release in, normally >0', units='m'),

            # Todo implement release group particle with different parameters, eg { 'oxygen' : {'decay_rate: 0.01, 'initial_value =  5.}
            max_cycles_to_find_release_points =  PVC(100, int, min=1, doc_str='Maximum number of cycles to search for acceptable release points, ie. inside domain, polygon etc '),
            release_duration = PTC(None,   obsolete=True,  doc_str='use "duration" parameter instead'),
            release_start_date = PTC(None,   obsolete=True,  doc_str='use "start" parameter instead'),
            release_end_date = PTC(None,    obsolete=True,  doc_str='use "end" parameter instead' ),
            )

        self.role_doc('Release particles at 1 or more given locations. A pulse_size of particles are released every release_interval. All these particles have ID properties for their release_group and the pulese they were released in.')

        info = self.info
        info['number_released'] = 0  # count of particles released in this group
        info['pulseID'] = 0
        info['total_number_required'] = 0

    def initial_setup(self):
        params=self.params
        info = self.info
        info['depth_range']= [
                -float(np.inf) if params['water_depth_min'] is None else params['water_depth_min'],
                 float(np.inf) if params['water_depth_max'] is None else params['water_depth_max']
        ]
        info['depth_range'] = np.asarray( info['depth_range'])

     # optional filter on release points
    def user_release_point_filter(self, release_part_prop, time_sec= None):
        # user can create filter if points to keep from given points release points
        # by inheritance of this class and overriding this method
        # return boolean of kept points
        return np.full((release_part_prop['x'].shape[0],),True,dtype=bool)

    def _add_bookeeping_release_info(self, release_info):
        # add booking ID s before anny culling of candidates
        info = self.info
        # add release IDs as full arrays
        n = release_info['x'].shape[0]
        release_info['IDrelease_group'] = np.full((n,), info['instanceID'], dtype=np.int32)
        release_info['IDpulse'] = np.full((n,), info['pulseID'], dtype=np.int32)
        release_info['user_release_groupID'] = np.full((n,), self.params['user_release_groupID'], dtype=np.int32)
        return release_info

    def release_location_info(self, x):
        # get grid cell etc for given candidate locations
        fgm = si.core_class_roles.field_group_manager
        use_points, release_info = fgm.are_points_inside_domain(x)

        release_info['water_depth'] = fgm.interp_named_2D_scalar_fields_at_given_locations_and_time(
                                         'water_depth', release_info['x'],
                                        release_info['n_cell'], release_info['bc_coords'], time_sec=None,
                                        hydro_model_gridID=release_info['hydro_model_gridID'])

        self._add_bookeeping_release_info(release_info)

        # keep those inside domain
        release_info = self._retain_release_locations(release_info,use_points)

        return release_info

    def get_release_locations(self, time_sec):
        info = self.info
        release_info= self.get_hori_release_locations(time_sec)

        if si.run_info.is3D_run:
            self._add_vertical_release(release_info)

        info['pulseID'] += 1
        info['number_released'] += release_info['x'].shape[0]  # count number released in this group

        return release_info

    # needs to be overridden , put on no pass when all release types use it
    def get_hori_release_locations(self, time_sec):
        nopass(f'get_hori_release_locations must be added to this release name = {self.params["name"]} class= {self.params["class_name"]}')


    def find_enough_hori_release_locations(self, time_sec):
        # set up full set of release locations inside  polygons
        ml = si.msg_logger
        info= self.info
        params=self.params

        n_required = info['number_per_release']
        release_info =dict(x = np.full((0, params['points'].shape[1]), 0.,dtype=np.float64, order='C'),
                        )
        count = 0
        while release_info['x'].shape[0] < n_required:
            # get 2D release candidates
            x0 = self.get_release_location_candidates()

            # get candidate locations and if useable/inside domain
            rd = self.release_location_info(x0)

            # if any data concatenate it, add release particle prop
            for key, item in rd.items():
                # add keys  if not there as 0, by what is needed add to
                if key not in release_info:
                    s = (0,) + item.shape[1:] if item.ndim > 1 else (0,)
                    release_info[key]=np.zeros(s, dtype=item.dtype)
                # add on new release data to existing data
                if rd['x'].shape[0] > 0:
                    release_info[key] = np.concatenate((release_info[key], rd[key][:, ...]), axis=0)

            # allow max_cycles_to_find_release_points cycles to find points
            count += 1
            if count > params["max_cycles_to_find_release_points"]: break

        # trim initial locations, cell  etc to required number or points
        n_required = min(release_info['x'].shape[0], n_required)
        for key in release_info.keys():
            release_info[key] = release_info[key][:n_required,...]

        # discard those in dry cells if requested
        release_info = self._apply_dry_cell_and_user_filters(release_info, time_sec)

        return release_info

    def _apply_dry_cell_and_user_filters(self, release_info, time_sec):
        # Block dry cell release
        if not self.params['allow_release_in_dry_cells']:
             #usew time dependent dry cell index from reader to discard dry cells
            is_dry_cell = si.core_class_roles.field_group_manager.release_are_dry_cells(release_info)
            release_info= self._retain_release_locations(release_info, ~is_dry_cell)

        # add tide data
        # add time dependent tide
        fgm = si.core_class_roles.field_group_manager
        release_info['tide'] = fgm.interp_named_2D_scalar_fields_at_given_locations_and_time(
            'tide', release_info['x'],
            release_info['n_cell'], release_info['bc_coords'], time_sec=time_sec,
            hydro_model_gridID=release_info['hydro_model_gridID'])

        # apply user filter
        use_points = self.user_release_point_filter(release_info, time_sec=time_sec)
        release_info = self._retain_release_locations(release_info, use_points)

        return release_info

    def _add_vertical_release(self, release_info):
        params = self.params

        # add z if not given
        if  release_info['x'].shape[1] < 3:
            release_info['x']= np.concatenate(
                (
                    release_info['x'],
                    np.full((release_info['x'].shape[0], 1),
                    0,
                    dtype=release_info['x'].dtype)
                ),
                axis=1
            )

        if params['release_at_surface']:
            release_info['x'][:, 2] = release_info['tide'] - params['release_offset_from_surface_or_bottom']
        elif params['release_at_bottom']:
            release_info['x'][:, 2] = -release_info['water_depth'] + params['release_offset_from_surface_or_bottom']

        elif params['z_min'] is not None or params['z_max'] is not None:
            # release in random depth range if no given points have no z value, or zmin and/or zmax is set
            z_min = -si.info.large_float if params['z_min'] is None else params['z_min']
            z_max =  si.info.large_float if params['z_max'] is None else params['z_max']

            if z_min > z_max:
                si.msg_logger.msg(f'Must have zmin >= zmax, (zmin,zmax) =({z_min:.3e}, {z_max:.3e}) ',
                                  hint='z=0 is mean tide level and z < 0 below the mean tide level',   fatal_error=True, caller=self)
            release_info['x']  = self._get_z_release_in_depth_range(release_info['x'], z_min, z_max,
                                                                    release_info['water_depth'], release_info['tide'])
        return release_info

    @staticmethod
    @njitOT
    def _get_z_release_in_depth_range(x, z_min, z_max, water_depth, tide):
        # get random release within z_min and z_max and with water depth and tide

        for n in range(x.shape[0]):
            z1  = max(-water_depth[n], z_min)
            z2  = min(tide[n], z_max)
            x[n, 2] = np.random.uniform(z1, z2, size=1)[0]
        return x

    def _retain_release_locations(self,release_info,sel):
        # only keep release_locations_those with sel ==True
        result = dict()
        has_points = np.any(sel)
        for key in release_info.keys():
            data = release_info[key]
            if has_points:
                result[key] = data[sel, ...]
            else:
                # make empty output
                s = (0,) + data.shape[1:] if data.ndim > 1 else (0,)
                result[key] = np.zeros(s, dtype=data.dtype)
        return result

    def _check_points_inside_domain(self, points, warn_some_outside=False):

        # filters points based on inside domain/water depth range
        release_info = self.release_location_info(points)

        n_used, n_given = release_info['x'].shape[0], points.shape[0]
        if n_used == 0:  # check number # points inside
            si.msg_logger.msg(f'No points are inside domain for group "{self.params["name"]}" ',
                              hint='points not in grids coord. system?, or if geographic, not in (lon,lat) order',
                              warning=True, caller=self)

        if warn_some_outside and n_used < n_given:
            si.msg_logger.msg(f'Discarded {n_given-n_used} points of {n_given}  outside domain for group "{self.params["name"]}",  ',
                              hint='Wrong cord system? not in (lon, lat order) if geographic coords?',
                              warning=True, caller=self)

        return release_info


    def _add_bounding_box(self,points):
        self.info['bounding_box_ll_ul'] = np.stack(( np.nanmin(points[:,:2],axis=0), np.nanmax(points[:, :2],axis=0)))

    def _check_all_inside_water_depth_range(self, release_info):

        info = self.info
        water_depth = release_info['water_depth']
        in_range = np.logical_and(water_depth >= info['depth_range'][0] ,
                             water_depth <= info['depth_range'][1] )

        if ~np.any(in_range):  # check number # points in depth range
            si.msg_logger.msg(f'No release points are inside user given depth range "{self.params["name"]}" ',
                              hint='Fix depth range or move points',
                              fatal_error=True, caller=self)
        release_info = self._retain_release_locations(release_info,in_range)
        return release_info

    def _clone_release_info(self, release_info,n):
        result = dict()
        for key, val in release_info.items():
            result[key] = np.repeat(release_info[key],n,axis=0)
        return  result
