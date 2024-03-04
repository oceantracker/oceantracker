from oceantracker.release_groups._base_release_group import _BaseReleaseGroup
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC,ParameterCoordsChecker as PCC

class GridRelease(_BaseReleaseGroup):
    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params(dict(
                coords_ll_ur=PCC(None, is_required=True, is3D=False,
                            units='Meters, unless hydro-model coords are geographic then points must be given in  (lon, lat) order in decimal degrees.',
                            doc_str='Coordinates of lower left and upper right of grid release,, ie [[x_ll,y_ll],[x_ur,y_ur]]'),
              grid_size= PLC([100, 99], [int], fixed_len=2,
                             min =1,max=10**6,
                             doc_str='number of rows and colums in grid'),
                ))
        self.class_doc('Release pules of particles on a regular grid.')

        info = self.info
        info['release_type'] = 'grid'

    def initial_setup(self):
        params = self.params
        info = self.info

        # setup grid
        x = np.linspace(params['coords_ll_ur'][0,0], params['coords_ll_ur'][1,0], params['grid_size'][1])
        y = np.linspace(params['coords_ll_ur'][0,1], params['coords_ll_ur'][1,1], params['grid_size'][0])
        xi,yi = np.meshgrid(x,y)
        info['x_grid'] = np.stack((xi,yi),axis=2)

        # add points param for othe parts of code
        params['points'] = np.stack((xi.ravel(),yi.ravel()),axis=1)

        # build global grid index
        ri, ci = np.meshgrid(range(y.size),  range(x.size))
        info['map_grid_index_to_row_column'] = np.stack((ri.ravel(), ci.ravel()),axis=1)


        pass

    def get_number_required(self):
        return self.params['pulse_size'] * self.params['points'].shape[0]

    def get_release_location_candidates(self):
        x = np.repeat(self.params['points'], self.params['pulse_size'], axis=0)
        return x
