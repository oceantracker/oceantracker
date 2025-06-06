import numpy as np

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

    def get_number_required_per_release(self):
        return self.params['pulse_size']*self.params['points'].shape[0]

    def get_release_location_candidates(self):
         
        x = np.repeat(self.params['points'], self.params['pulse_size'], axis=0)

        if self.params['release_radius'] > 0.:
            rr = abs(float(self.params['release_radius']))
            n = x.shape[0]
            rr = np.repeat(rr, n, axis=0)
            r = np.random.random((n,)) * rr * np.exp(1.0j * np.random.random((n,)) * 2.0 * np.pi)
            r = r.reshape((-1, 1))
            x[:, :2] += np.hstack((np.real(r), np.imag(r)))

        return x





