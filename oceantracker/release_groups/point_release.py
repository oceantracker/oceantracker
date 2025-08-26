import numpy as np
from copy import deepcopy
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.release_groups._base_release_group import _BaseReleaseGroup

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

        # get release info for points inside domain and water depth limits
        self.release_info = self._check_points_inside_domain(params['points'], warn_some_outside=True)
        self.release_info = self._check_all_inside_water_depth_range(self.release_info)

        self._add_bounding_box( self.release_info['x'])
        params['points'] = self.release_info['x'] # keep those inside domain and water depth range

        self.info['number_per_release'] = params['pulse_size'] * self.release_info['x'].shape[0]

    def get_hori_release_locations(self, time_sec):
        # filter pre-calculated reslease info
        rg = self._apply_dry_cell_and_user_filters(self.release_info, time_sec)
        rg  = self._clone_release_info(rg,self.params['pulse_size'])
        return rg







