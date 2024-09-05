from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC,ParameterCoordsChecker as PCC
import oceantracker.definitions as ci
from oceantracker.shared_info import shared_info as si
from oceantracker.util.basic_util import nopass
class _BaseIntegratedModel(ParameterBaseClass):
    def __init__(self):
        super().__init__()  # get parent defaults
        self.add_default_params(dict(
                                ))
        self.role_doc('Models are ')


    def initial_setup(self): nopass('initial_setup method is required for integrated models ')

    def update(self, n_time_step, time_sec):   nopass('update method is required for integrated models ')

    def add_release_groups_and_settings(self,crumbs=''):
        # must add relase grouspad seeting before initial setup
        # adds settings and classes  needed by the model using helper class approach with keyword arguments
        #  these are in addition to any other params the user sets
        pass





