import numpy as np

from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.release_groups._base_release_group import _BaseReleaseGroup
from oceantracker.util.numba_util import njitOT


from oceantracker.shared_info import SharedInfo as si


class PointRelease(_BaseReleaseGroup):
    # releases particles at fixed points, inside optional radius
    # add checks to see if points inside domain and dry if released in a radius

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({
                 'points':          PCC(None, is_required=True,one_or_more_points=True,
                                        doc_str='A N by 2 or 3 list or numpy array of locations where particles are released. eg for 2D [[25,10],[23,2],....] ',
                                        units='Meters, unless hydro-model coords are in (lon, lat) then points must be given in  (lon, lat) order in decimal degrees.'),
                  'release_radius':  PVC(0., float, min= 0., doc_str= 'Particles are released from random locations in circle of given radius around each point.'),

                                  })
        self.class_doc('Release pules of particles at given points.')
        info= self.info
        info['number_released'] = 0 # count of particles released in this group
        info['pulseID'] = 0
        info['release_type'] = 'point'

    def initial_setup(self):
        # must be called after unpack_x0
        # tidy up parameters to make them numpy arrays with first dimension equal to number of locations

        params = self.params
        info = self.info

        # ensure points are  meters
        if si.hydro_model_cords_in_lat_long:
            params['points_lon_lat'] = params['points'].copy()
            params['points'] =  si._transform_lon_lat_to_meters(params['points_lon_lat'], in_lat_lon_order=params['coords_allowed_in_lat_lon_order'],
                                                    crumbs=f'Point release #[{info["instanceID"]}] : {info["name"]}')

        info['bounding_box_ll_ul'] = np.stack(( np.nanmin(params['points'][:2],axis=0),
                                                np.nanmax(params['points'][:2],axis=0)))


    def get_number_required(self):
        return self.params['pulse_size']*self.params['points'].shape[0]

    def get_release_location_candidates(self):
         
        x = np.repeat(self.params['points'], self.params['pulse_size'], axis=0)

        if self.params['release_radius']> 0.:
            rr = abs(float(self.params['release_radius']))
            n = x.shape[0]
            rr = np.repeat(rr, n, axis=0)
            r = np.random.random((n,)) * rr * np.exp(1.0j * np.random.random((n,)) * 2.0 * np.pi)
            r = r.reshape((-1, 1))
            x[:, :2] += np.hstack((np.real(r), np.imag(r)))

        return x





