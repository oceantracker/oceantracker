# modfiy aspects pof all active particles, ie moving and stranded

from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.util.basic_util import get_role_from_base_class_file_name

class _BaseTrajectoryModifier(ParameterBaseClass):
    role_name = get_role_from_base_class_file_name(__file__)
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

    # all particles checked to see if they need status changing
    def update(self,n_time_step, time_sec, active): pass