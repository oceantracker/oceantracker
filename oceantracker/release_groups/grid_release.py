from oceantracker.release_groups._base_release_group import _BaseReleaseGroup
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC,ParameterCoordsChecker as PCC
from oceantracker.util import regular_grid_util
from oceantracker.shared_info import shared_info as si

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
            grid_span= PCC(None, single_cord=True,is_required=True, is3D=False, doc_str='(dx, dy)  of the grid release', units='meters or decimal degrees (dlon, dlat)  if geographic coords'),
            grid_size= PLC([10, 9], int, fixed_len=2,
                            min =1,max=10**6,
                           doc_str='number of rows and columns in grid'),
                            )

        info = self.info
        info['release_type'] = 'grid'

    def add_required_classes_and_settings(self, settings, reader_builder, msg_logger):
        info = self.info
        if 'grid_release_row_col' not in si.class_roles.particle_properties:
            si.add_class('particle_properties', name='grid_release_row_col',
                         class_name='ManuallyUpdatedParticleProperty',
                         write=True, time_varying=False, vector_dim=2, dtype='int32',
                         description='(row , column) of grid point which released the particle')
            pass
    def initial_setup(self):
         
        params = self.params
        info = self.info

        # setup grid
        xi, yi, info['bounding_box_ll_ul'] = regular_grid_util.make_regular_grid(params['grid_center'], params['grid_size'], params['grid_span'])
        info['x_grid'] = np.stack((xi,yi),axis=2)

        # add points param for other parts of code
        self.points = np.stack((xi.ravel(),yi.ravel()),axis=1)

        # build global grid index
        ci, ri = np.meshgrid(range(xi.shape[1]),range(xi.shape[0]))
        info['map_grid_index_to_row_column'] = np.stack((ri.ravel(), ci.ravel()),axis=1)

        # add particle prop fort row column only if nor already added by another grid release


        pass

    def get_number_required(self):
        return self.params['pulse_size'] * self.points.shape[0]

    def get_release_location_candidates(self):
        x = np.repeat(self.points, self.params['pulse_size'], axis=0)
        return x
    
    def _add_bookeeping_particle_prop_data(self, release_part_prop):
        super()._add_bookeeping_particle_prop_data(release_part_prop) # get standard release bookeeping prop

        # add row column origin part prop data, for each pulse
        release_part_prop['grid_release_row_col'] = np.repeat(self.info['map_grid_index_to_row_column'], self.params['pulse_size'], axis=0)
        return release_part_prop
