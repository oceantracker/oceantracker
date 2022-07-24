import  numpy as np

from oceantracker.fields._base_field import _BaseField

class ReaderField(_BaseField):
    # reader filds have extra info to unpack  variables in the file
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with given params
        self.info.update({'requires_depth_averaging': False,
                          'is3D_in_file': False,
                          'requires_depth_averaging' : False,
                          'variable_list': [],

                          })

    def initialize(self):
        si = self.shared_info
        # work out size from grid etc, tuple to garud against change
        self.info['shape_in_file']= tuple([si.classes['reader'].params['time_buffer_size'] if self.params['is_time_varying'] else 1,
                                   si.grid['x'].shape[0],
                                   si.grid['nz'] if self.info['is3D_in_file'] else 1,
                                   self.params['num_components'] if self.params['num_components'] is not None else 1 ])

        buffer_shape = list( self.info['shape_in_file'])
        if self.info['is3D_in_file'] and self.info['requires_depth_averaging']:
            buffer_shape[2 ] =1
            if  self.info['shape_in_file'][3] == 3:  buffer_shape[3 ] =2

        self.data = np.full(buffer_shape, 0, dtype=self.params[ 'dtype'])
