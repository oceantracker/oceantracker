import numpy as np
from oceantracker.particle_properties.util import particle_operations_util, particle_comparisons_util
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.common_info_default_param_dict_templates import particle_info
from oceantracker.util import time_util

class _BaseTimeVaringInfo(ParameterBaseClass):
    # single valued time varying information, ie not a particle property
    # eg  "time" data, numer released so far
    # properties which are maintained in memory and may be written out, eg group and particle

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params({   'description': PVC(None,str),
                                    'write': PVC(True, bool),
                                    'dtype':PVC(np.float64, np.dtype),
                                    'vector_dim': PVC(1, int, min=1),
                                    'prop_dim3': PVC(1, int, min=1),
                                    'initial_value':PVC(0.,float),
                                    'fill_value': PVC(None,[int,float]),
                                    'update':PVC(True,bool)
              })

        self.class_doc(role='Particle properties hold data at current time step for each particle, accessed using their ``"name"`` parameter. Particle properties  many be \n * core properties set internally (eg particle location x )\n * derive from hindcast fields, \n * be calculated from other particle properties by user added class.')

    def initial_setup(self, **kwargs):
        s=(1,)
        self.data = self.data = np.full(s, self.params['initial_value'], dtype=  self.get_dtype(),order='c')

    def update(self): pass # manual update by default
    def set_values(self, value): self.data[0]=value
    def get_values(self): return self.data[0]

    def initial_value_at_birth(self, released_IDs):  pass

    def get_dtype(self):  return self.params['dtype']


class TimeVaryingInfo(_BaseTimeVaringInfo):
    pass


