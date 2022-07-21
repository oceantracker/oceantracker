# modfiy aspects pof all active particles, ie moving and stranded

from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC


class TrajectoryModifiersBase(ParameterBaseClass):

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'name': PVC(None, str),
                                 'requires_3D': PVC(False, bool)})

    # all particls checked to see if they need status changing
    def update(self,buffer_index, time, active): pass