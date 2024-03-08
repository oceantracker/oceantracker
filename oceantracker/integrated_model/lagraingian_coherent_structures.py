import numpy as np

from oceantracker.integrated_model._base_model import  _BaseModel
from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.common_info_default_param_dict_templates import default_polygon_dict_params
from oceantracker.util import time_util
class LagarangianCoherentStructures(_BaseModel):
    # random polygon release in 2D or 3D

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({
            'update_interval': PVC(60*60.,float,units='sec',
                                    doc_str='Time in seconds between calculating statistics, will be rounded to be a multiple of the particle tracking time step'),
            'lags': PLC(None, [float,int], units='sec',
                        doc_str='List of one or more times after particle release to calculate Lagarangian Coherent Structures, default is 1 day'),
            'grid_size':           PLC([100, 99],[int], fixed_len=2,  min=1, max=10 ** 5,
                                            doc_str='number of rows and columns in grid'),
            'grid_center': PCC(None, one_or_more_points=True, is3D=False, doc_str='center of the grid release  (x,y) or (lon, lat) if hydromodel in geographic coords.', units='meters or decimal degrees'),
            'grid_span': PCC(None, one_or_more_points=True, is3D=False, doc_str='(width, height)  of the grid release', units='meters or decimal degrees'),
            'z_min': PVC(None, float, doc_str=' Only allow particles to be above this vertical position', units='meters above mean water level, so is < 0 at depth'),
            'z_max': PVC(None, float, doc_str=' Only allow particles to be below this vertical position', units='meters above mean water level, so is < 0 at depth'),

        })

    def initial_setup(self):
        si = self.shared_info
        ml = si.msg_logger
        params = self.params
        info = self.info

        # remove any existing release groups
        if len(si.classes['release_groups']):
            si.classes['release_groups']= {}
            ml.msg('Lagarangian coherent structures cannot be run with other release groups, removed existing release groups', warning=True, caller=self)

        # set

        if params['lags'] is None: params['lags']  = [24*3600.]

        # round interval and lags to model time step
        params['update_interval'] = si.round_interval_to_model_time_step(params['update_interval'],caller=self, crumbs='update_interval param> ')
        params['lags'] = si.round_times_to_model_times(params['lags'], lags=True, caller=self, crumbs='lags param> ')

        self._add_grid_releases()

    def update(self,n_time_step, time_sec):
        si = self.shared_info
        pgm = si.classes['particle_group_manager']
        info = self.info
        si.settings['include_dispersion'] = False
        #self._add_grid_releases(n_time_step)
        pass

    def _add_grid_releases(self):
        si = self.shared_info
        pgm = si.classes['particle_group_manager']
        params = self.params

        release_params = dict(class_name= 'oceantracker.release_groups.grid_release.GridRelease',
                              pulse_size=1, z_min= params['z_min'], z_max= params['z_max'],
                              grid_size = params['grid_size'],
                              release_interval=0.
                              )
        # make a release group at each time interval and grid
        for nt,t in enumerate(np.arange(si.run_info['model_start_time'],si.run_info['model_end_time'],params['update_interval'])):

            for n_grid, (center,span)  in enumerate(zip(params['grid_center'], params['grid_span'])):

                release_params['coords_ll_ur'] = center + np.asarray([[-span[0]/2, -span[1]/2],
                                                                  [ span[0]/2,  span[1]/2]])
                release_params['release_start_date'] = time_util.seconds_to_isostr(t)
                release_params['max_age'] = params['lags'][-1] # run each to largest lag

                i = pgm.add_release_group(f'LCS_grid{n_grid:03d}_time_step{nt:04d}', release_params)
                #i.calculation_scheduler = si.make_scheduler(interval=params['update_interval'], caller=self)
        pass
