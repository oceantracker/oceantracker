from datetime import  datetime
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from oceantracker.util import basic_util, triangle_utilities_code, time_util
from oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np

from oceantracker.reader.generic_unstructured_reader import GenericUnstructuredReader

class GenericStucturedGridReader(GenericUnstructuredReader):
    # loads a standard SCHISM netcdf output file with nodal data
    # variable names can be tweaked via maps in shared_params, if non-standard names used


    def __init__(self):
        super().__init__()  # required in children to get parent defaults
        #  update parent defaults with above
        self.add_default_params({'dimension_map': {'node': PVC(None, str, is_required=True)}})

    def preprocess_grid_variable_at_start(self, name, data, nc=None):
        si = self.shared_info
        if name == 'triangles':
            data -= 1  # make triangle nodes 0 based index
        if name == 'bottom_cell_index':
            data -= 1
        return data