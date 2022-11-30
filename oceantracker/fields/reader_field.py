import  numpy as np

from oceantracker.fields._base_field import _BaseField

class ReaderField(_BaseField):
    # reader fields have extra info to unpack based on variables in the file
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with given params
        self.info.update({'requires_depth_averaging': False,
                          'is3D_in_file': False,
                          'variable_list': [],    })

    def get_buffer_shape(self):
        # get buffer shape from file
        si = self.shared_info
        grid = si.classes['reader'].grid

        # work out size from grid etc, tuple to guard against change
        self.info['shape_in_file'] = tuple([si.classes['reader'].params['time_buffer_size'] if self.params['is_time_varying'] else 1,
                              grid['x'].shape[0],
                              grid['nz'] if self.params['is3D'] else 1,
                              self.params['num_components'] if self.params['num_components'] is not None else 1])

        buffer_shape = list(self.info['shape_in_file'])

        # make 3D field with only 2 vector components if 3D vector
        if self.info['requires_depth_averaging']:
            buffer_shape[2] = 1
            if self.info['shape_in_file'][3] == 3:  buffer_shape[3] = 2

        return buffer_shape

    def initialize(self):
        si = self.shared_info
        grid = si.classes['reader'].grid
        self.params['is3D']= True if self.info['is3D_in_file'] else False
        super().initialize()




