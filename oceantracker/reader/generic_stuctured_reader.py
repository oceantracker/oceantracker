import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util, json_util
from oceantracker.reader.util.hydromodel_grid_transforms import convert_regular_grid_to_triangles
from oceantracker.reader.util import reader_util
from oceantracker.reader._base_generic_reader import _BaseGenericReader
from copy import  deepcopy

from oceantracker.shared_info import SharedInfo as si

class dev_GenericStructuredReader(_BaseGenericReader):

    def __init__(self):
        super().__init__()
        self.add_default_params(
                    dimension_map=dict(
                                rows =PVC('rows', str, is_required=True, doc_str='Row dimension name ie y cord of grid'),
                                cols=PVC('cols', str, is_required=True, doc_str='Column dimension name, x cord of grid'),
                                     ),
                            )
          # required in children to get parent defaults and merge with give params
        pass


    def read_horizontal_grid_coords(self, nc, grid):
        # read grid as rows and columns
        params= self.params
        var_name = params['grid_variable_map']['x']
        grid['xi'] = nc.read_a_variable(var_name[0])
        grid['yi'] = nc.read_a_variable(var_name[1])

        # convert to mesh grid if needed
        if grid['xi'].ndim ==1:
            grid['xi'],  grid['yi']= np.meshgrid(grid['xi'], grid['yi'])

        # nodal x's
        grid['x'] = np.column_stack(( grid['xi'].ravel(), grid['yi'].ravel() )).astype(np.float64)

        if self.params['hydro_model_cords_in_lat_long']:
            grid['x'] = self.convert_lon_lat_to_meters_grid(grid['x'])
            grid['hydro_model_cords_in_lat_long'] = True
        else:
            grid['hydro_model_cords_in_lat_long'] = False

        grid = self.get_land_mask(grid)

        return grid

    def get_land_mask(self,grid):
        si.msg_logger.msg('Todo- add land mask', caller=self, warning=True)
        grid['land_mask'] = np.full_like(grid['xi'], False)
        return grid
    def read_triangles_as_int32(self, nc, grid):
        # build triangles from regular grid
        grid = convert_regular_grid_to_triangles(grid, grid['land_mask'])
        # get nodes for each corner of quad

        return grid

    def read_file_var_as_4D_nodal_values(self,nc, grid, var_name, file_index=None):
        # reformat file variable into 4D time,node,depth, components  form
        #todo only works on 2D
        dm = self.params['dimension_map']

        data, data_dims = self.read_field_var(nc, var_name, sel=file_index)

        # add dummy time dim if none
        if  dm['time'] not in data_dims: data = data[np.newaxis,...]

        # data is now shaped as (time, row, col, depth)
        # now flatten (time,rows, col, depth)  to  (time,nodes, depth)
        s = data.shape
        data = data.reshape( (s[0],s[1]*s[2])) # this should match flatten in "C" order

        # add dummy depth, vector components axis,
        data = data[:, :, np.newaxis, np.newaxis]

        return data

    def read_open_boundary_data_as_boolean(self, grid):
        # and make this part of the read grid method


        # read hgrid file for open boundary data
        is_open_boundary_node = np.full((grid['land_mask'].shape), False)

        si.msg_logger.msg(f'Todo find open boundary nodes, all closed at the momment', warning=True, caller=self)

        return is_open_boundary_node.ravel()

        # flag all edges of regular as open boundaries
        # this will pick up most open boundary nodes, but not internal rivers
        is_open_boundary_node[:,[0,-1]] = True
        is_open_boundary_node[[0, -1],:] = True

        # only flag those  as open which are part of the ocean
        is_open_boundary_node = np.logical_and(is_open_boundary_node,~grid['land_mask'])
        #todo write note open boundary data avaible, chose OBC mode param

        return is_open_boundary_node.ravel()