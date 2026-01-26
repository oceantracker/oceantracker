from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
import oceantracker.util.basic_util  as basic_util
from oceantracker.util.basic_util import get_role_from_base_class_file_name

class _BaseInterp(ParameterBaseClass):
    # prototype for interplotor
    role_name = get_role_from_base_class_file_name(__file__)
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params(dict( debug_check_cell= PVC(False, bool, doc_str='checks particles are inside the cell found by interp')))

    def initial_setup(self, grid): pass

    # find hori and vertical cell containing each particle
    def find_cell(self, xq, current_buffer_steps,weight_time_steps, active): basic_util.nopass(' must supply find_cells method')

    # return cell number for xq without a guess
    def initial_horizontal_cell(self, grid, xq): pass

    def close(self): pass



