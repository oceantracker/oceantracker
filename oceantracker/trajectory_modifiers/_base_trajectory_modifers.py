# modfiy aspects pof all active particles, ie moving and stranded

from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC


class _BaseTrajectoryModifier(ParameterBaseClass):

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

    # all particles checked to see if they need status changing
    def update(self,n_time_step, time_sec, active): pass