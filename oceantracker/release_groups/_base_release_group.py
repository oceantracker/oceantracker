import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC, ParameterCoordsChecker as PCC
from oceantracker.util.parameter_checkingV2 import ParameterValueChecker2 as PVC2, ParameterTimeChecker as PTC
from numba import njit
from oceantracker.util.numba_util import njitOT

from oceantracker.util.basic_util import nopass
from oceantracker.shared_info import SharedInfo as si

class _BaseReleaseGroup(ParameterBaseClass):
    def __init__(self):
        super().__init__() # get parent defaults
        self.add_default_params(
                pulse_size =  PVC(1, int, min=1, doc_str='Number of particles released in a single pulse, this number is released every release_interval.'),
                release_interval =  PVC(0., float, min=0., units='sec', doc_str='Time interval between released pulses. To release at only one time use release_interval=0.'),
               # start =  PVC(None, 'iso8601date', doc_str='start date of release, Must be an ISO date as string eg. "2017-01-01T00:30:00" '),
                start=PTC(None,doc_str='start date/time of first release" '),
                end =  PTC(None,doc_str='date/time of lase release, ignored if duration given'),
                duration =  PVC(None, float, min=0.,units='sec',
                                    doc_str='How long particles are released for after they start being released, ie releases stop this time after first release.,an alternative to using "end"'),
                max_age =  PVC(None, float, min=1.,
                              doc_str='Particles older than this age in seconds are culled,ie. status=dead, and removed from computation, very useful in reducing run time'),
                user_release_groupID =  PVC(0, int, doc_str='User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.'),
                user_release_group_name =  PVC(None, str, doc_str='User given name/label to attached to this release groups to make it easier to distinguish.'),
                allow_release_in_dry_cells =  PVC(False, bool,
                            doc_str='Allow releases in cells which are currently dry, ie. either permanently dry or temporarily dry due to the tide.'),
               z_range =  PLC(None, [float, int], min_length=2, obsolete='use z_min and/or z_max'),
               z_min =  PVC(None, float, doc_str='min/ deepest z value to release for to randomly release in 3D, overrides any given release z value'),
               z_max =  PVC(None, float, doc_str='max/ highest z vale release for to randomly release in 3D, overrides any given release z value'),
               release_offset_from_surface_or_bottom =  PVC(0., [float, int], min=0.,
                                                            doc_str=' 3D release particles at offset from free surface or bottom, if release_at_surface or  release_at_bottom = True', units='m'),
               release_at_surface =  PVC(False, bool, doc_str=' 3D release particles at free surface, ie tide height, with  offset given by release_offset_from_surface_or_bottom param, overrides any given release z value'),
               release_at_bottom =  PVC(False, bool, doc_str=' 3D release particles at bottom, with  offset given by release_offset_from_surface_or_bottom param, overrides any given release z value'),
               # 'water_depth_min =  PVC(None, float,doc_str='min water depth to release in, useful for releases with a depth rage, eg larvae from inter-tidal shellfish', units='m'),
               # 'water_depth_max =  PVC(None, float, doc_str='max water depth to release in', units='m'),

               # Todo implement release group particle with different parameters, eg { 'oxygen' : {'decay_rate: 0.01, 'initial_value =  5.}
                max_cycles_to_find_release_points =  PVC(1000, int, min=100, doc_str='Maximum number of cycles to search for acceptable release points, ie. inside domain, polygon etc '),
                release_duration =  PVC(None, float, min=0., obsolete='use "duration" parameter instead'),
                release_start_date =  PVC(None, 'iso8601date', obsolete='use "start" parameter instead'),
                release_end_date =  PVC(None, 'iso8601date',  obsolete='use "end" parameter instead' ),
                )

        self.role_doc('Release particles at 1 or more given locations. A pulse_size of particles are released every release_interval. All these particles have ID properties for their release_group and the pulese they were released in.')

        info = self.info
        info['number_released'] = 0  # count of particles released in this group
        info['pulseID'] = 0
        info['total_number_required'] = 0

    def get_release_location_candidates(self): nopass()
    def get_number_required(self): nopass()

    # optional filter on release points
    def filter_release_points(self,is_inside, release_part_prop, time_sec= None):
        # user can filter release points by inheritance of this class and overriding this method
        # return booleaon of keeped points
        return is_inside, release_part_prop

    def add_bookeeping_particle_prop_data(self,release_part_prop):
        # add booking ID s before anny culling of candidates
        info = self.info
        # add release IDs as full arrays
        n = release_part_prop['x'].shape[0]
        info['IDrelease_group'] = info['instanceID']
        release_part_prop['IDrelease_group'] = np.full((n,), info['instanceID'], dtype=np.int32)
        release_part_prop['IDpulse'] = np.full((n,), info['pulseID'], dtype=np.int32)
        release_part_prop['user_release_groupID'] = np.full((n,), self.params['user_release_groupID'], dtype=np.int32)
        return release_part_prop

    def get_start_time_and_life_span(self):
        # gets relese start end and last ime allive from params
        # and any start and end times, or a duration

        hi = si.hindcast_info
        ri = si.run_info
        params = self.params

        if params['start'] is None:
            start =  si.hindcast_info['end_time'] if si.settings.backtracking else si.hindcast_info['start_time']
        else:
            start = params['start']

        # work out release duration
        if params['duration'] is None :
            # look at end date
            if params['end'] is None:
                end = si.hindcast_info['start_time'] if si.settings.backtracking else si.hindcast_info['end_time']
            else:
                end = params['end']
            duration = abs(end-start)
        else:
            duration = abs(params['duration'])

        life_span =  duration + 0. if params['max_age'] is None else abs(params['max_age'])
        return start, life_span

    def _check_potential_release_locations_in_bounds(self, x):
        # check cadiated in bound
        # there must be a particle property set up for every release_part_prop must have a
        # use KD tree to find points those inside model domain
        fgm = si.core_roles.field_group_manager
        is_inside, release_part_prop  = fgm.are_points_inside_domain(x, self.params['allow_release_in_dry_cells'])

        return is_inside, release_part_prop

    def get_release_locations(self, time_sec):
        # set up full set of release locations inside  polygons
         
        ml = si.msg_logger
        info= self.info
        params=self.params

        n_required = self.get_number_required()

        # there must be a particle property set up for every release_part_prop must have a


        if  'points' in params :
            self.points  = params['points'] # grid release does not have points param

        release_part_prop =dict(
                        x= np.full((0, self.points.shape[1]), 0.,dtype=np.float64, order='C'),
                        )
        count = 0
        while release_part_prop['x'].shape[0] < n_required:
            # get 2D release candidates
            x0 = self.get_release_location_candidates()

            # get candidate locations inside domain
            is_inside, rd  = self._check_potential_release_locations_in_bounds(x0)

            #
            rd = self.add_tide_and_depth_release_part_prop(rd,time_sec)

            # add booking IDs etrc before any culling of candidates
            rd = self.add_bookeeping_particle_prop_data(rd)

            #any filter added by child class added
            is_inside, rd = self.filter_release_points(is_inside,rd, time_sec=time_sec)

            # only keep those inside domain and keeped by filter:
            for key in rd.keys():
                rd[key] = rd[key][is_inside, ...]

            # if any data concatenate it
            # add release particle prop
            if rd['x'].shape[0] > 0:
                  # if any to list so far
                for key, item in rd.items():
                    # add keys  if not there as 0, by what is needed add to
                    if key not in release_part_prop:
                        s = [0]
                        if item.ndim ==2:
                            s += [item.shape[1]]
                        elif item.ndim > 2:
                            s += list(item.shape[1:])
                        release_part_prop[key]=np.zeros(s, dtype=item.dtype)
                    # add on new release data to existing data
                    release_part_prop[key] = np.concatenate((release_part_prop[key], rd[key][:, ...]), axis=0)

            # allow max_cycles_to_find_release_points cycles to find points
            count += 1
            if count > self.params["max_cycles_to_find_release_points"]: break

        info['pulseID'] += 1
        info['number_released'] += release_part_prop['x'].shape[0]  # count number released in this group
        info['total_number_required'] += n_required  # used to check what proportion  sucessfully release all that were required, used to find groups tha have no releaseses


        n_required = release_part_prop['x'].shape[0] #

        # trim initial location, cell  etc to required number
        for key in release_part_prop.keys():
            release_part_prop[key] = release_part_prop[key][:n_required, ...]

        # if nothing to release then return only 'x' is
        if release_part_prop['x'].shape[0] ==0:
            return release_part_prop

        if si.run_info.is3D_run:
            if release_part_prop['x'].shape[1] <= 2:
                # expand x0 to 3D if needed
                release_part_prop['x'] = np.concatenate((release_part_prop['x'], np.zeros((release_part_prop['x'].shape[0], 1), dtype=x0.dtype)), axis=1)

            if params['release_at_surface']:
                release_part_prop['x'][:, 2] = release_part_prop['tide'] - params['release_offset_from_surface_or_bottom']
            elif params['release_at_bottom']:
                release_part_prop['x'][:, 2] = release_part_prop['water_depth'] + params['release_offset_from_surface_or_bottom']

            elif params['z_min'] is not None or  params['z_max'] is not None:
                z_min = -si.info.large_float if params['z_min'] is None else params['z_min']
                z_max =  si.info.large_float if params['z_max'] is None else params['z_max']

                if z_min > z_max:
                    ml.msg(f'Must have zmin >= zmax, (zmin,zmax) =({z_min:.3e}, {z_max:.3e}) ',
                                      hint='z=0 is mean tide level and z < 0 below the mean tide level',
                                      fatal_error=True, exit_now=True, caller=self)
                release_part_prop['x']  = self.get_z_release_in_depth_range(release_part_prop['x'] ,z_min,z_max,
                                                                   release_part_prop['water_depth'],release_part_prop['tide'])
        return release_part_prop

    def add_tide_and_depth_release_part_prop(self,release_part_prop, time_sec):# get water depth and tide at particle locations, which may be needed to filter particle releases
             
            # add tide and water depth at released particle locations
            fgm = si.core_roles.field_group_manager
            release_part_prop['water_depth'] = fgm.interp_named_field_at_given_locations_and_time(
                                                'water_depth', release_part_prop['x'], time_sec=None,
                                                n_cell=release_part_prop['n_cell'],
                                                bc_cords=release_part_prop['bc_cords'],
                                                hydro_model_gridID=release_part_prop['hydro_model_gridID'])
            release_part_prop['tide'] = fgm.interp_named_field_at_given_locations_and_time(
                                                'tide', release_part_prop['x'], time_sec=time_sec,
                                                n_cell=release_part_prop['n_cell'],
                                                bc_cords=release_part_prop['bc_cords'],
                                                hydro_model_gridID=release_part_prop['hydro_model_gridID'])
            return release_part_prop

    def get_z_release_in_depth_range(x,z_min, z_max, water_depth,tide):
        # get random release within z_min and z_max and with water depth and tide

        for n in range(x.shape[0]):
            z1  = max(-water_depth[n], z_min)
            z2  = min(tide[n], z_max)
            x[n, 2] = np.random.uniform(z1, z2, size=1)[0]
        return x

    @staticmethod
    @njitOT
    def get_z_release_in_depth_range(x,z_min, z_max, water_depth,tide):
        # get random release within z_min and z_max and with water depth and tide

        for n in range(x.shape[0]):
            z1  = max(-water_depth[n], z_min)
            z2  = min(tide[n], z_max)
            x[n, 2] = np.random.uniform(z1, z2, size=1)[0]
        return x
