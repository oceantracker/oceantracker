import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.release_groups.point_release import _BaseReleaseGroup
from oceantracker.shared_info import shared_info as si
from oceantracker.util.cord_transforms import  local_meters_grid_to_deg

class RadiusRelease(_BaseReleaseGroup):
    '''
    Release particles at random locations within a radius of given points
    Points chosen are always inside the domain, also inside wet cells unless setting allow_release_in_dry_cells is True.
    '''
    development =  True
    def __init__(self):
        # set up info/attributes
        super().__init__()

        self.add_default_params(
                points= PCC(None, is_required=True, one_or_more_points=True,
                      doc_str='A N by 2 or 3 list or numpy array of locations of N circle centers for release, eg for 2D [[25,10],[23,2],....] ',
                      units='Meters, unless hydro-model coords are in (lon, lat) then points must be given in  (lon, lat) order in decimal degrees.'),
                radius= PVC(0., float, min=1.,is_required=True,
                                    doc_str='Particles are released from random locations in circle of same given radius around each point.',
                                     units='meters, even if hydromodel grid systen is (lon,lat)'),
                )

    def initial_setup(self):
        super().initial_setup()  # required to get base class set up
        super().initial_setup()  # required to get base class set up
        params = self.params
        info = self.info

        # get release info for points inside domain and water depth limits
        release_info= self._check_points_inside_domain(params['points'], warn_some_outside=True)
        params['points'] = release_info['x'] # keep those inside domain

        self._add_bounding_box(params['points'])
        info['number_per_release'] = params['pulse_size']*params['points'].shape[0]
        info['release_type'] = 'radius'

    def get_hori_release_locations(self, time_sec):
        release_info = self.find_enough_hori_release_locations(time_sec)
        return release_info
    def get_release_location_candidates(self):
        params = self.params
        # replicate points
        x = np.repeat(params['points'], params['pulse_size'], axis=0)

        # add random offset from center of circle
        rr = abs(float(params['radius']))
        n = x.shape[0]
        rr = np.repeat(rr, n, axis=0)
        r = np.random.random((n,)) * rr * np.exp(1.0j * np.random.random((n,)) * 2.0 * np.pi)
        r = r.reshape((-1, 1))
        offsets_meters= np.hstack((np.real(r), np.imag(r)))

        # lon,lat  tweaks
        if si.settings.use_geographic_coords:
            x[:, :2] =  local_meters_grid_to_deg(offsets_meters[:,0],offsets_meters[:,1], x[:,0], x[:,1], as_vector=True)
        else:
            x[:, :2] += offsets_meters

        return x




