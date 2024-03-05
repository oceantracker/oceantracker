from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC,ParameterCoordsChecker as PCC



class _BaseModel(ParameterBaseClass):
    def __init__(self):
        super().__init__()  # get parent defaults
        self.add_default_params(dict(
                                ))

        self.role_doc('Models are ')

    def initial_setup(self):
        self.add_shared_info_access()

    def add_shared_info_access(self):
        si = self.shared_info

        self.part_prop = si.classes['particle_properties']




