import  numpy as np

from oceantracker.fields._base_field import _BaseField

class ReaderField(_BaseField):
    # reader fields have extra info to unpack based on variables in the file
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with given params
        si= self.shared_info

    def initialize(self):

        # make 2D if depth averaging
        if self.info['variable_info']['requires_depth_averaging']:
            self.params['is3D']= False
            self.params['num_components']=  min(2,self.params['num_components']) # make sure 3D vectors are 2D

        # todo, write use  shared memory if requeste
        super().initialize()

class DepthAveragedReaderField(_BaseField):
    # depth averaged reader field on reading main field
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with given params
        si = self.shared_info

    def initialize(self):
        self.params['is3D'] = False
        self.params['num_components'] = min(2, self.params['num_components'])  # make sure 3D vectors are 2D

        # todo, write use  shared memory if requeste
        super().initialize()
        pass







