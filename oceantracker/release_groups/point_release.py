import numpy as np
from copy import deepcopy
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.release_groups._base_release_group import _BaseReleaseGroup
from oceantracker.util.cord_transforms import fix_any_spanning180east


from oceantracker.shared_info import shared_info as si


class PointRelease(_BaseReleaseGroup):
    '''
    Release pulse of particles at given points, or in circle around points.
    '''
    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({
                 'points':          PCC(None, is_required=True,one_or_more_points=True,
                                        doc_str='A N by 2 or 3 list or numpy array of locations where particles are released. eg for 2D [[25,10],[23,2],....] ',
                                        units='Meters, unless hydro-model coords are in (lon, lat) then points must be given in  (lon, lat) order in decimal degrees.'),
                  'release_radius':  PVC(0., float, min= 0., doc_str= 'Particles are released from random locations in circle of given radius around each point.'),

                                  })

        info= self.info
        info['number_released'] = 0 # count of particles released in this group
        info['pulseID'] = 0
        info['release_type'] = 'point'

    def initial_setup(self):
        # must be called after unpack_x0
        # tidy up parameters to make them numpy arrays with first dimension equal to number of locations
        super().initial_setup()  # required to get base class set up
        params = self.params
        info = self.info

        # ensure points are  meters
        if si.settings.use_geographic_coords:
            # check points for wrap around 180
            params['points'] = fix_any_spanning180east( params['points'], msg_logger=si.msg_logger, caller=self,
                                                crumbs=f'Point release#{self.info["instanceID"]}, name "{params["name"]}"')

        info['bounding_box_ll_ul'] = np.stack(( np.nanmin(params['points'][:2],axis=0),
                                                np.nanmax(params['points'][:2],axis=0)))

        # get release info for points inside domain and water depth limits
        self.release_info = self._check_all_outside_domain_water_depth_range(params['points'])
        self._check_some_outside_domain_water_depth_range(self.release_info['x'], params['points'])

    def get_number_required_per_release(self):
        return self.params['pulse_size']*self.params['points'].shape[0]

    def get_hori_release_locations(self, time_sec):
        rg = self._apply_dry_cell_and_user_filters(self.release_info, time_sec)
        return rg

    def _check_all_outside_domain_water_depth_range(self,points):

        # filters points based on inside domain/water depth range
        release_info = self.release_location_info(points)
        if release_info['x'].shape[0] == 0:  # check number # points inside
            si.msg_logger.msg(f'No release points are inside domain for group "{self.params["name"] }" ',
                              hint='points not in grids coord. system?, or if geographic, not in (lon,lat) order',
                              error=True,caller = self)
        return release_info

    def _check_some_outside_domain_water_depth_range(self,points_used,points_given):
        n_used,n_given =  points_used.shape[0],  points_given.shape[0]
        if points_used.shape[0] <  points_given.shape[0]:
            si.msg_logger.msg(f'Only {n_used} release of {n_given}  points used for group "{self.params["name"]}",  ',
                              hint='Some points are outside domain or not in requested water depth range?',
                              warning=True, caller=self)





