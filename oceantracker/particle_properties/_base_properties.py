import numpy as np
from oceantracker.particle_properties.util import particle_operations_util, particle_comparisons_util
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import  ParamDictValueChecker as PVC
from oceantracker.common_info_default_param_dict_templates import particle_info
class BasePropertyInfo(ParameterBaseClass):
    # properties which are maintained in memory and may be written out, eg group and particle

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params({ 'description': PVC(None,str), 'time_varying':PVC(True, bool),'name': PVC(None, str),
            'write': PVC(True, bool), 'vector_dim': PVC(1, int, min = 1 ), 'prop_dim3': PVC(1, int, min=1),
             'dtype':PVC(np.float64,type,possible_values=[np.float32, np.float64, np.int8, np.int16, np.int32, bool]),
             'initial_value':PVC(0., (int,float, bool)),'update':PVC(True,bool)})


    def initialize(self, **kwargs): pass

    def initial_value_at_birth(self, released_IDs):  pass

    def update(self,t,active): pass

    def is_vector(self): return self.data.ndim > 1

    def num_vector_dimensions(self):  return 0 if self.data.ndim == 1 else self.data.shape[1]

    def get_dtype(self): return self.data.dtype


class TimeVaryingInfo(BasePropertyInfo):
    # single valued time varying information, ie not a particle property
    # eg  "time" data, numer released so far

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults and merge with give params


    def initialize(self,**kwargs):

        s=(1,)
        if self.params['vector_dim'] > 1:
            s += (self.params['vector_dim'],)
        self.data = self.data = np.full(s, self.params['initial_value'], dtype=  self.params['dtype'])

    def update(self): pass # manual update by default
    def set_values(self, value): self.data[0]=value
    def get_values(self): return self.data[0]

class ParticleProperty(BasePropertyInfo):
    # property of each particle individually, eg x, time released etc , status
    # or non-time varying parameter eg ID,

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({'write': PVC(True, bool),
                                 'type': PVC('user', str,
                                            doc_str='particle property',
                                            possible_values=particle_info['known_prop_types']),
                                 })
    def initialize(self):
        s=(self.shared_info.particle_buffer_size,)
        if self.params['vector_dim'] > 1:
            s += (self.params['vector_dim'],)

        # third matrix dim, so far only used recording vertical cell at each node  3D for 2 time steps
        if self.params['prop_dim3'] > 0 and self.params['prop_dim3'] > 1:
            s += (self.params['prop_dim3'],)

        # set up data buffer
        self.data = np.full(s, self.params['initial_value'], dtype=  self.params['dtype'])

    def initial_value_at_birth(self, released_IDs):
        # need to set at birth, as in compact mode particle buffer changes,
        # so cant rely on value at matrix construction in initialize
        self.set_values(self.params['initial_value'], released_IDs)

    def update(self): pass # manual update by default

    def set_values(self, values, active):

        if type(values) == np.ndarray:
            if values.shape[0]  != active.shape[0] : raise Exception('set_values: shape of values must match number of indices to set')
            particle_operations_util.set_values(self.data, values, active)
        else:
            particle_operations_util.set_value(self.data, values, active)

    def add_values_to(self, values, active):
        # set property using using indicies sel
        if type(values) == np.ndarray:
            if values.shape[0]  != active.shape[0] : raise Exception('add_values_to: shape of values must match number of indices to set in active')
            particle_operations_util.add_values_to(self.data, values, active)
        else:
            particle_operations_util.add_value_to(self.data, values, active)

    def add_prop_to(self, prop_name, sel, scale = 1.0):
        particle_operations_util.add_to(self.dataInBufferPtr(), self.shared_info.classes['particle_properties'][prop_name].dataInBufferPtr(), sel, scale= scale)

    def get_values(self, sel):
        # get property values using indices sel
        return np.take(self.data,sel, axis=0)  # for integer index sel, take is faster than numpy fancy indexing and numba

    def copy_prop(self,prop_name, sel):
        particle_operations_util.copy(self.dataInBufferPtr(), self.shared_info.classes['particle_properties'][prop_name].dataInBufferPtr(), sel)

    def dataInBufferPtr(self): return self.data[:self.shared_info.classes['particle_group_manager'].particles_in_buffer, ...]

    # particle selection methods
    # if out given, uses index buffers to speed, by reducing memory creation, and making it more likely index values are in chip cache
    # WARNING!!! if out supplied then returned matrix is view of out, so careful with reuse of out!!!!!!!!!!!!!!!! otherwise strange results!!!
    def compare_all_to_a_value(self, test, value, out = None):
        # find indices where prop[prop_name] (test)  value is true
        # if out is None, given result returns a view of new variable

        if self.is_vector():
            raise Exception('compare_all_to_a_value: particle property ' + self.params['name'] +'>> particle comparisons using compare_prop_to_value only possible for scalar particle properties, not vectors')

        # to search only those in buffer use dataInBufferPtr()
        return particle_comparisons_util.prop_compared_to_value(self.dataInBufferPtr(), test, value, out)

    def find_subset_where(self, active, test, value, out=None):
        # searches a subset of active particles to find indicies
        #  where prop[prop_name][active] (test)  value is true and returns a view of out,
        # if out is None, given result returns a view of new variable

        if self.is_vector():
            raise Exception('find_subset_where: particle property ' + self.params['name'] + '>> particle comparisons using compare_prop_to_value only possible for scalar particle properties, not vectors')

        return particle_comparisons_util.prop_subset_compared_to_value(active, self.dataInBufferPtr(), test, value, out)

