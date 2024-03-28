import numpy as np
from oceantracker.particle_properties.util import particle_operations_util, particle_comparisons_util
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util
from oceantracker.shared_info import SharedInfo as si

class _BaseParticleProperty(ParameterBaseClass):
    # property of each particle individually, eg x, time released etc , status
    # or non-time varying parameter eg ID,
    # properties which are maintained in memory and may be written out, eg group and particle

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params({   'description': PVC(None,str),
                                    'units': PVC(None, str),
                                    'time_varying':PVC(True, bool),
                                    'vector_dim': PVC(1, int, min = 1 ),
                                    'prop_dim3': PVC(1, int, min=1),
                                    'dtype':PVC(np.float64, np.dtype),
                                    'initial_value':PVC(0.,float),
                                    'fill_value': PVC(None,[int,float]),
                                    'update':PVC(True,bool),
                                    'write': PVC(True, bool, doc_str='Write particle property to tracks or event files file'),
                                    'type': PVC('user', str,
                                                doc_str='type of particle property, used to manage how to update particle property',
                                                possible_values=si.info.known_prop_types),
                                     'release_group_parameters':PVC([], list, doc_str='In development: release group specific particle prop params'),
              })

        self.role_doc('Particle properties hold data at current time step for each particle, accessed using their ``"name"`` parameter. Particle properties  many be \n * core properties set internally (eg particle location x )\n * derive from hindcast fields, \n * be calculated from other particle properties by user added class.')

    def initial_setup(self):

        s = (si.core_roles.particle_group_manager.info['current_particle_buffer_size'],)
        if self.params['vector_dim'] > 1:
            s += (self.params['vector_dim'],)

        # third matrix dim, so far only used recording vertical cell at each node  3D for 2 time steps
        if self.params['prop_dim3'] > 0 and self.params['prop_dim3'] > 1:
            s += (self.params['prop_dim3'],)

        self.info['array_size'] = s
        # set up data buffer
        self.data = np.full(s, self.params['initial_value'], dtype=self.get_dtype(), order='c')

    def final_setup(self, **kwargs): pass  # stuff done after intiail setup of all classes/properties

    def initial_value_at_birth(self, new_part_IDs):
        # need to set at birth, as in compact mode particle buffer changes,
        # so cant rely on value at matrix construction in initialize
        value = self.params['initial_value']

        if self.get_dtype() == np.dtype('<M8[s]'):  # datetime64 in seconds
            value = time_util.seconds_to_datetime64(value)

        self.set_values(value, new_part_IDs)  # sets this properties values

    def update(self,n_time_step,time_sec,active): pass

    def is_vector(self): return self.data.ndim > 1

    def num_vector_dimensions(self):  return 0 if self.data.ndim == 1 else self.data.shape[1]

    def get_dtype(self): return self.params['dtype']

    def set_values(self, values, active):

        if type(values) == np.ndarray:
            if values.shape[0] != active.shape[0] :
                raise Exception('set_values: shape of values must match number of indices to set')
            particle_operations_util.set_values(self.data, values, active)
        else:
            # scalar
            particle_operations_util.set_value(self.data, values, active)

    def copy(self, prop_name, active):
        # copy from named particle
        part_prop= si.roles.particle_properties
        particle_operations_util.copy(self.data, part_prop[prop_name].data, active)

    def fill_buffer(self,value):
        n_in_buffer = si.core_roles.particle_group_manager.info['particles_in_buffer']
        self.data[:n_in_buffer,...] = value


    def get_values(self, sel):
        # get property values using indices sel
        return np.take(self.data,sel, axis=0)  # for integer index sel, take is faster than numpy fancy indexing and numba

    def used_buffer(self): return self.data[:si.core_roles.particle_group_manager.info['particles_in_buffer'], ...]

    def full_buffer(self):  return self.data

    # particle selection methods
    # if out given, uses index buffers to speed, by reducing memory creation, and making it more likely index values are in chip cache
    # WARNING!!! if out supplied then returned matrix is view of out, so careful with reuse of out!!!!!!!!!!!!!!!! otherwise strange results!!!
    def compare_all_to_a_value(self, test, value, out = None):
        # find indices where prop[prop_name] (test)  value is true
        # if out is None, given result returns a view of new variable

        if self.is_vector():
            raise Exception('compare_all_to_a_value: particle property ' + self.info['name'] +'>> particle comparisons using compare_prop_to_value only possible for scalar particle properties, not vectors')

        # to search only those in buffer use used_buffer()
        data = self.used_buffer()
        if out is None: out = np.full((data.shape[0],), -127, np.int32)
        found = particle_comparisons_util.compared_prop_to_value(data, test, value, out)
        return found

    def find_subset_where(self, active, test, value, out=None):
        # searches a subset of active particles to find indicies
        #  where prop[prop_name][active] (test)  value is true and returns a view of out,
        # if out is None, given result returns a view of new variable

        if self.is_vector():
            raise Exception('find_subset_where: particle property ' + self.info['name'] + '>> particle comparisons using compare_prop_to_value only possible for scalar particle properties, not vectors')

        return particle_comparisons_util.prop_subset_compared_to_value(active, self.used_buffer(), test, value, out)

    def find_those_in_range_of_values(self,value1,value2, out):
        data = self.used_buffer()
        if out is None: out = np.full((data.shape[0],), -127, np.int32)

        found= particle_comparisons_util._find_all_in_range(data, value1, value2, out)
        return found


class ParticleProperty(_BaseParticleProperty):
    pass