from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC,ParameterCoordsChecker as PCC
import oceantracker.definitions as ci
from oceantracker.shared_info import shared_info as si
from oceantracker.util.basic_util import nopass
from oceantracker.util.basic_util import get_role_from_base_class_file_name


class _BaseIntegratedModel(ParameterBaseClass):
    role_name = get_role_from_base_class_file_name(__file__)
    def __init__(self):
        super().__init__()  # get parent defaults
        self.add_default_params(dict(
                                ))
        self.role_doc('Models are ')


    def initial_setup(self): nopass('initial_setup method is required for integrated models ')

    def update(self, n_time_step, time_sec,active=None):   nopass('update method is required for integrated models ')





