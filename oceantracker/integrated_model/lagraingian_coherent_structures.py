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
            'start_date': PVC(None, 'iso8601date', doc_str='start date of LSC calculation, Must be an ISO date as string eg. "2017-01-01T00:30:00" '),
            'end_date': PVC(None, 'iso8601date', doc_str=' end date of LSC calculation, Must be an ISO date as string eg. "2017-01-01T00:30:00"'),
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

    def add_settings_and_class_params(self):
        # change parameters
        si = self.shared_info
        info = self.info
        hi = si.hindcast_info
        params = self.params

        # turn off dispersion
        self.settings(include_dispersion=False)

        # make a grid release group at each time interval and grid
        self.clear_class_role('release_groups') # cannot use with other releases

        release_params = dict(class_name='oceantracker.release_groups.grid_release.GridRelease',
                              pulse_size=1, z_min=params['z_min'], z_max=params['z_max'],
                              grid_size=params['grid_size'],
                              release_interval=0.  )
        # get time for releases
        a = time_util.get_regular_events(
            hi, si.backtracking, params['update_interval'],
            si.msg_logger, self,
            start=params['start_date'],
            end=params['end_date'],
            crumbs='LCS: ')
        info.update(a)
        for nt in range(info['times'].size):
            for n_grid, (center, span) in enumerate(zip(params['grid_center'], params['grid_span'])):
                release_params['coords_ll_ur'] = center + np.asarray([[-span[0] / 2, -span[1] / 2],
                                                                      [span[0] / 2, span[1] / 2]])
                release_params['release_start_date'] = time_util.seconds_to_isostr(info['times'][nt])
                release_params['max_age'] = params['lags'][-1]  # run each to largest lag
                # add param dict as keyword arguments
                self.add_class('release_groups', name= f'LCS_grid{n_grid:03d}_time_step{nt:04d}', **release_params )
                pass


    def initial_setup(self):
        si = self.shared_info
        ml = si.msg_logger
        params = self.params
        info = self.info


        if params['lags'] is None: params['lags']  = [24*3600.]

        return

        # todo move to sheduler ? -- round interval and lags to model time step
        params['update_interval'] = si.round_interval_to_model_time_step(params['update_interval'],caller=self, crumbs='update_interval param> ')
        params['lags'] = si.round_times_to_model_times(params['lags'], lags=True, caller=self, crumbs='lags param> ')

        # add a
        for name, rg in si.classes['release_groups'].items():
            t = rg.info['release_info']['times'][0] +  params['lags']  # time of lags after start of release group
            si.add_scheduler_to_class(rg, times= t,  caller=self, crumbs='Adding lagged calculation times')

        pass

    def update(self, n_time_step, time_sec):
        si = self.shared_info

        for n, rg in enumerate(si.release_groups.values()):
  #          if rg.calculation_scheduler.task[n_time_step]:
   #             pass # cal LSC
            pass
        pass

    def _calculate_LCS(self,n):
        # for nth release
        pass



