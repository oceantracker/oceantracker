from oceantracker.shared_info import shared_info as si
from oceantracker.reader._base_all_readers import _BaseReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterTimeChecker as PTC, ParameterListChecker as PLC
import numpy as np
from  oceantracker.util import time_util, numpy_util
import oceantracker.reader.util.hydromodel_grid_transforms as  hydromodel_grid_transforms

class _BaseUnstructuredReader(_BaseReader):
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params(
            dimension_map=dict(node=PVC(None, str, doc_str='Nodes in grid')),
        )  # list of normal required dimensions

    # Below are basic variable read methods for any new reader
    # ---------------------------------------------------------


    def read_water_depth(self, grid):
        ds = self.dataset
        gm = self.params['grid_variable_map']
        water_depth = ds.read_variable(gm['water_depth']).data
        return water_depth

    def read_file_var_as_4D_nodal_values(self, var_name, var_info, nt=None):
        # todo add name to params!!
        # read variable into 4D ( time, node, depth, comp) format
        # assumes same variable order in the file
        d= self.dataset.read_variable(var_name, nt=nt)  # returns xarray
        # get 4D size

        s = var_info['shape4D'].copy()
        time_dim = self.info[ 'time_dim']
        s[0] = d.coords[time_dim].size if time_dim in d.dims else 1
        return d.data.reshape(s)

