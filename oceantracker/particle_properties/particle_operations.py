from oceantracker.particle_properties.util import particle_operations_util as __part_op_util
import numpy as np

def set_values(part_prop: 'part. prop. instance', values, select: np.ndarray):
    """Set particle properties value for array indices in select array
    values can be a single value or array of a size matching select
    """
    if type(values) == np.ndarray:
        if values.shape[0] != select.shape[0]:
            raise Exception('set_values: shape of values must match number of indices to set')
        __part_op_util.set_values(part_prop.data, values, select)
    else:
        # scalar
        __part_op_util.set_value(part_prop.data, values, select)

def get_values(part_prop :  'part. prop. instance', sel:'np.array(np.int32)'):
    # get property values using indices sel
    return np.take(part_prop.data, sel, axis=0)  # for integer index sel, take is faster than numpy fancy indexing and numba

