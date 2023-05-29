from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util import basic_util
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from copy import  copy

class _BaseField(ParameterBaseClass):
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with given params
        self.add_default_params({'write_interp_particle_prop_to_tracks_file': PVC(True, bool),
                               # 'create_particle_property_with_same_name': PVC( True, bool),
                                 'is_time_varying': PVC(True, bool,is_required=True),
                                 'is3D': PVC(True, bool,is_required=True ),
                                  'num_components': PVC(None, int,is_required=True),
                                  })

    def initial_setup(self):

        si = self.shared_info
        grid = si.classes['reader'].grid
        # work out size from grid etc, tuple to garud against change
        self.info['shape_in_file'] = tuple([si.classes['reader'].params['time_buffer_size'] if self.params['is_time_varying'] else 1,
                                            grid['x'].shape[0],
                                            grid['nz'] if self.params['is3D'] else 1,
                                            self.params['num_components'] if self.params['num_components'] is not None else 1])

        buffer_shape = tuple([si.classes['reader'].params['time_buffer_size'] if self.params['is_time_varying'] else 1,
                                            grid['x'].shape[0],
                                            grid['nz'] if self.params['is3D'] else 1,
                                            self.params['num_components'] if self.params['num_components'] is not None else 1])

        self.data = np.full(buffer_shape, 0, dtype=np.float32)  # all fields are float 32

    def is_time_varying(self): return self.data.shape[0] > 1
    def is3D(self): return  self.data.shape[2] > 1
    def is_vector(self): return self.data.shape[3] > 1
    def get_number_components(self): return self.data.shape[3]

    def get_dtype(self): return self.data.dtype

    def get_data(self, nb=0):
        # return view of data buffer
        if self.is_time_varying():
            return self.data[nb,...]
        else:
            return self.data[:] # give whole
    def update(self): pass

class UserFieldBase(_BaseField):
    # same as above but update method is required
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with given params

    def update(self, time_sec): basic_util.nopass('User fields must have update method')
    # if buffer index None, this  allows update of non-time varying use fields