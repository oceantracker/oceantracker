from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util import basic_util
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC




# make and access 4D fields from reader or custom fields with dims [ time,node,z, vector components]
class ReaderField(ParameterBaseClass):
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with given params

        self.add_default_params(dict(
                    time_varying= PVC(False, bool),
                    is3D = PVC(False, bool),
                    is_vector= PVC(False, bool),
                    write_interp_particle_prop_to_tracks_file = PVC(True, bool),
                    create_particle_property_with_same_name  = PVC(True, bool),
                            ))
        reader = None
        interp = None

    def initial_setup(self):
        si = self.shared_info
        params= self.params
        #todo attach reader to field
        reader = si.classes['reader']
        ncomp = 1
        if params['is_vector']:
            ncomp = 3 if params['is3D'] else 2

        s= [reader.params['time_buffer_size'] if params['time_varying'] else 1,
            reader.grid['x'].shape[0],
            reader.grid['nz'] if params['is3D'] else 1,
             ncomp]

        self.data = np.full(s, 0., dtype=np.float32, order='c')  # all fields are float 32

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


class CustomFieldBase(ReaderField):
    # same as above but update method is required
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with given params


    def update(self, active): basic_util.nopass('User fields must have update method')
    # if buffer index None, this  allows update of non-time varying use fields







