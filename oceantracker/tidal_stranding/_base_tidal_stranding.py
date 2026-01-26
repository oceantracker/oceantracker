from oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier
from oceantracker.util.basic_util import get_role_from_base_class_file_name

class _BaseTidalStranding(_BaseTrajectoryModifier):
    role_name = get_role_from_base_class_file_name(__file__)

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({})