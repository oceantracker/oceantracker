from oceantracker.release_groups._base_release_group import _BaseReleaseGroup
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC,ParameterCoordsChecker as PCC

from oceantracker.shared_info import SharedInfo as si

class GridRelease(_BaseReleaseGroup):
    '''
    Release pules of particles on a regular grid.
    '''

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.remove_default_params(['points'])
        self.add_default_params(
            grid_center= PCC(None, single_cord=True, is_required=True, is3D=False, doc_str='center of the grid release  (x,y) or (lon, lat) if hydromodel in geographic coords.', units='meters or decimal degrees'),
            grid_span= PCC(None, single_cord=True,is_required=True, is3D=False, doc_str='(width, height)  of the grid release', units='meters or decimal degrees'),
            grid_size= PLC([100, 99], [int], fixed_len=2,
                            min =1,max=10**6,  doc_str='number of rows and columns in grid'),
                )


        info = self.info
        info['release_type'] = 'grid'

    def initial_setup(self):
         
        params = self.params
        info = self.info

        # setup grid
        gs =params['grid_span'] / 2.
        x = params['grid_center'][0] + np.linspace(-gs[0], gs[0], params['grid_size'][1]).reshape(-1, 1)
        y = params['grid_center'][1] + np.linspace(-gs[1], gs[1], params['grid_size'][0]).reshape(-1, 1)

        xi, yi = np.meshgrid(x,y)
        info['x_grid'] = np.stack((xi,yi),axis=2)
        info['bounding_box_ll_ul'] = np.asarray([[x[0],y[0]],[ x[-1],y[-1]]] )

        # add points param for othe parts of code
        self.points = np.stack((xi.ravel(),yi.ravel()),axis=1)

        # build global grid index
        ci, ri = np.meshgrid(range(x.size),range(y.size))
        info['map_grid_index_to_row_column'] = np.stack((ri.ravel(), ci.ravel()),axis=1)

        # add particle prop fort row column only if nor already added by another grid release
        if 'grid_release_row_col' not in si.roles.particle_properties:
            pgm = si.core_roles.particle_group_manager
            pgm.add_particle_property('grid_release_row_col','manual_update', dict(write=True, time_varying= False, vector_dim=2,dtype=np.int32,
                                                                                  description='(row , column) of grid point which released the particle' ))
            pass

        pass

    def get_number_required(self):
        return self.params['pulse_size'] * self.points.shape[0]

    def get_release_location_candidates(self):
        x = np.repeat(self.points, self.params['pulse_size'], axis=0)
        return x
    
    def add_bookeeping_particle_prop_data(self,release_part_prop):
        super().add_bookeeping_particle_prop_data(release_part_prop) # get standard release bookeeping prop

        # add row column origin part prop data, for each pulse
        release_part_prop['grid_release_row_col'] = np.repeat(self.info['map_grid_index_to_row_column'], self.params['pulse_size'], axis=0)
        return release_part_prop
