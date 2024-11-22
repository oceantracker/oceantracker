from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util import basic_util
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.shared_info import shared_info as si



# make and access 4D fields from reader or custom fields with dims [ time,node,z, vector components]
class _BaseField(ParameterBaseClass):
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with given params

        self.add_default_params(
                    name=PVC(None, str, doc_str='Name to refer to this field internally within code, must be given', is_required=True),
                    time_varying= PVC(False, bool,doc_str='Does field vary with time', is_required=True),
                    is3D = PVC(False, bool,is_required=True,doc_str='is field 3D'),
                    is_vector= PVC(False, bool),
                    write_interp_particle_prop_to_tracks_file = PVC(True, bool),
                    create_particle_property_with_same_name  = PVC(True, bool),
                            )
        reader = None
        interp = None

    def initial_setup(self,time_buffer_size, reader_info, reader_fields):

        params= self.params

        s= [time_buffer_size if params['time_varying'] else 1,
            reader_info['num_nodes'],
            reader_info['num_z_levels'] if params['is3D'] else 1,
            (3 if params['is3D'] else 2) if params['is_vector'] else 1
        ]

        self.data = np.full(s, 0., dtype=np.float32)  # all fields are float 32

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

    def update(self, fields, grid):    basic_util.nopass(' Fields must have update method')

class CustomFieldBase(_BaseField):
    # same as above but update method is required
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with given params

        self.add_default_params(requires3D=PVC(False, bool, doc_str='Must be a 3D run to be used', is_required=True))

    def update(self,fields, grid, buffer_index=None): basic_util.nopass(' Custom User fields must have update method')
    # if buffer index None, this  allows update of non-time varying use fields






