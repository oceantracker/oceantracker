import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.numpy_util import possible_dtypes
from oceantracker.shared_info import shared_info as si

class _BaseTimeVaringInfo(ParameterBaseClass):
    # single valued time varying information, ie not a particle property
    # eg  "time" data, numer released so far
    # properties which are maintained in memory and may be written out, eg group and particle

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params({   'description': PVC(None,str),
                                    'units': PVC(None, str),
                                    'write': PVC(True, bool),
                                    'dtype':PVC('float64', str, possible_values=possible_dtypes),
                                    'vector_dim': PVC(1, int, min=1),
                                    'prop_dim3': PVC(1, int, min=1),
                                    'initial_value':PVC(0.,float),
                                    'update':PVC(True,bool)
              })

        self.role_doc('Particle properties hold data at current time step for each particle, accessed using their ``"name"`` parameter. Particle properties  many be \n * core properties set internally (eg particle location x )\n * derive from hindcast fields, \n * be calculated from other particle properties by user added class.')

    def initial_setup(self, **kwargs):
        params = self.params
        s=(1,)
        self.data = np.full(s, params['initial_value'], dtype=  self.get_dtype(),order='c')

        if False and si.settings.write_tracks and params['write']:
            w = si.core_class_roles.tracks_writer
            w.create_variable_to_write(params['name'], 'time', None, params['vector_dim'],
                                    units=params['units'], description=params['description'],
                      dtype=params['dtype'])

    def update(self,n_time_step, time_sec, active): pass # manual update by default
    def set_values(self, value): self.data[0]=value
    def get_values(self): return self.data[0]

    def initial_value_at_birth(self, released_IDs):  pass

    def get_dtype(self):  return np.dtype(self.params['dtype'])


class TimeVaryingInfo(_BaseTimeVaringInfo):
    pass


