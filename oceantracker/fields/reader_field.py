
from oceantracker.fields._base_field import _BaseField
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.shared_info import shared_info as si

class ReaderField(_BaseField):
    "Feild to hold ring buffer of a variable read from hindcast files"
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with given params

        self.add_default_params(
                name= PVC(None, str, is_required=True,
                    doc_str='Name used internally to refer to this field within the code')
                )

    def update(self, fields, grid):
        # todo add reading update using reader class?
        pass