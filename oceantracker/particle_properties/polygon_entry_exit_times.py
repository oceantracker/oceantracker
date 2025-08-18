from oceantracker.particle_properties._base_particle_properties import CustomParticleProperty
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.util.numba_util import njitOT,njitOTparallel, prange

from oceantracker.shared_info import shared_info as si

class PolygonEntryExitTimes(CustomParticleProperty):
    '''
    records time particle enters given polygon,nan if not inside
    '''
    def __init__(self):
        super().__init__()
        self.add_default_params(
                initial_value= PVC(np.nan, float),
                dtype= PVC('float64',str),
                vector_dim= PVC(2, int, doc_str='Two columns for entry and exit times'),
                # default is non-vector
                points=PCC(None, doc_str='Points for 2D polygon to calc residence times, as N by 2 list or numpy array')
                )

    def add_required_classes_and_settings(self,**kwargs):
        params = self.params
        info = self.info
        info['entry_exit_times_prop_name'] = f'{params["name"]}_{["instanceID"]:03d}'
        si.add_class('particle_properties',
                     class_name='InsidePolygonsNonOverlapping2D',
                     name= info['entry_exit_times_prop_name'],
                     write=False,
                     polygon_list=dict(points=params['points']))

    def initial_setup(self, **kwargs):
        super().initial_setup()
        # nothing extra to add?

    def update(self,n_time_step, time_sec, alive):
        # find polygon each particle is inside

        part_prop = si.class_roles.particle_properties

        self._get_entry_exit_times(part_prop[self.info['entry_exit_times_prop_name']].data,
                                   time_sec, self.data, alive)

    @staticmethod
    @njitOTparallel
    def _get_entry_exit_times(is_inside, time_sec, entry_exit_times, alive):

        for nn in prange(alive.size):
            n = alive[nn]
            if is_inside[n]:
                if np.isnan(entry_exit_times[n,0]) :
                    # record time of new entry
                    entry_exit_times[n, 0] = time_sec
                    entry_exit_times[n, 1] = np.nan # flag as not yet exited
            else:
                # is not inside now
                if ~np.isnan(entry_exit_times[n, 0]):
                    # if previously entered, but now not inside, record exit time
                    entry_exit_times[n, 1] = time_sec
                else:
                    # flag as not inside
                    entry_exit_times[n, 0] = np.nan
                    entry_exit_times[n, 1] = np.nan
