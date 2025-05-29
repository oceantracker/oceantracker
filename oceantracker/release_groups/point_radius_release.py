import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.release_groups.point_release import PointRelease
from oceantracker.shared_info import shared_info as si

class PointRadiusRelease(PointRelease):
    '''
    Release particles at random locations within given polygon.
    Points chosen are always inside the domain, also inside wet cells unless setting allow_release_in_dry_cells is True.
    '''
    development =  True
    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params(si.default_polygon_dict_params)


        # below are not needed for polygons
        self.add_default_params(
                release_radius = PVC(0., float, min=0., doc_str='Particles are released from random locations in circle of given radius around each point.'),
                )


    def initial_setup(self):
        super().initial_setup()  # required to get base class set up

    def get_release_location_candidates(self):
        info = self.info
        # replicate points
        x = np.repeat(self.params['points'], self.params['pulse_size'], axis=0)

        # add random offset from center of circle
        rr = abs(float(self.params['release_radius']))
        n = x.shape[0]
        rr = np.repeat(rr, n, axis=0)
        r = np.random.random((n,)) * rr * np.exp(1.0j * np.random.random((n,)) * 2.0 * np.pi)
        r = r.reshape((-1, 1))
        x[:, :2] += np.hstack((np.real(r), np.imag(r)))

        return x




