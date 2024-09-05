from oceantracker.shared_info import shared_info as si
from oceantracker.reader._base_all_readers import _BaseReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterTimeChecker as PTC, ParameterListChecker as PLC
import numpy as np
from oceantracker.util.triangle_utilities import split_quad_cells
import oceantracker.reader.util.hydromodel_grid_transforms as  hydromodel_grid_transforms
from oceantracker.util.numpy_util import ensure_int32_dtype

class _BaseStructuredReader(_BaseReader):
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params(
            dimension_map=dict(
                            row = PVC(None, str, doc_str='row dim of grid ', is_required=True),
                            col = PVC(None, str, doc_str='column dim of grid ', is_required=True),
                               ),
        )  # list of normal required dimensions

    # Below are basic variable read methods for any new reader
    # ---------------------------------------------------------

    def read_triangles(self, grid):
        # build triangles from regular grid
        # get nodes for each corner of quad
        grid = hydromodel_grid_transforms.convert_regular_grid_to_triangles(grid, grid['land_mask'])

        return grid

    def read_open_boundary_data_as_boolean(self, grid):
        # and make this part of the read grid method

        # read hgrid file for open boundary data
        is_open_boundary_node = np.full((grid['land_mask'].shape), False)

        # flag all edges of regular as open boundaries
        # this will pick up most open boundary nodes, but not internal rivers

        # set water nodes on edge to be open
        is_open_boundary_node[:,[0,-1]] = True
        is_open_boundary_node[[0, -1],:] = True

        # only flag those  as open which are part of the ocean
        is_open_boundary_node = np.logical_and(is_open_boundary_node,~grid['land_mask'])
        return is_open_boundary_node.ravel()