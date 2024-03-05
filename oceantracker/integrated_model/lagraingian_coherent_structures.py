import numpy as np

from oceantracker.integrated_model._base_model import  _BaseModel
from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.common_info_default_param_dict_templates import default_polygon_dict_params

class LagarangianCoherentStructures(_BaseModel):
    # random polygon release in 2D or 3D

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({
                'update_interval':       PVC(60*60.,float,units='sec',
                                               doc_str='Time in seconds between calculating statistics, wil be rounded to be a multiple of the particle tracking time step'),
            'lags': PLC([60 * 60.*24], [float,int], units='sec',
                        doc_str='List of one or more times after particle release to calculate Lagarangian Coherent Structures, default is 1 day'),
            'grid_size':           PLC([100, 99],[int], fixed_len=2,  min=1, max=10 ** 5,
                                            doc_str='number of rows and columns in grid'),
                'grid_center': PCC(None, single_cord=True, is3D=False, doc_str='center of the statitics grid as (x,y) or (lon, lat) if hydromodel in geographic coords.', units='meters or decimal degrees'),
                'grid_span': PCC(None, single_cord=True, is3D=False, doc_str='(width, height)  of the statistics grid', units='meters or decimal degrees'),
            'z_min': PVC(None, float, doc_str=' Only allow particles to be above this vertical position', units='meters above mean water level, so is < 0 at depth'),
            'z_max': PVC(None, float, doc_str=' Only allow particles to be below this vertical position', units='meters above mean water level, so is < 0 at depth'),

        })

    def initial_setup(self):
        si = self.shared_info
        ml = si.msg_logger
        params = self.params

        # remove any existing release groups
        if len(si.classes['release_groups']):
            si.classes['release_groups']= {}
            ml.msg('Lagarangian Coherent Structures cannot be run with other release groups, removed existing release groups', warning=True, caller=self)

        # set
        pass

