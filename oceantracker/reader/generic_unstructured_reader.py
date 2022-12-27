import numpy as np
from copy import copy, deepcopy
from oceantracker.util import triangle_utilities_code
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.message_and_error_logging import append_message, GracefulExitError, FatalError
from oceantracker.util import time_util
from oceantracker.fields.util import fields_util
from oceantracker.util.cord_transforms import WGS84_to_UTM

from oceantracker.reader._base_reader import _BaseReader

class GenericUnstructuredReader(_BaseReader):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({ 'dimension_map': {'node': PVC('node', str)}} )

        self.buffer_info ={'n_filled' : None}
        self.class_doc(description='Generic reader, reading netcdf file variables into variables using given name map between internal and file variable names')


    def setup_grid(self, nc,reader_build_info):
        si= self.shared_info
        self.grid = {'x': None, 'triangles': None, 'zlevel' : None,
              'has_open_boundary_data': False}
        grid= self.grid
        # load grid variables
        grid['time'] = np.full((self.params['time_buffer_size'],),0.) # time buffer
        grid['nt_hindcast'] = np.full((self.params['time_buffer_size'],),-10, dtype=np.int32) # what global hindcast timestesps are in the buffer
        grid['x'] =  self.read_x(nc)

        grid['triangles'] = self.read_triangles(nc)


        grid['nz'] = 1

        if self.params['grid_variables']['zlevel'] is not None:
            # set up zlevel
            zlevel_name =self.params['grid_variables']['zlevel']
            s = list(nc.get_var_shape(zlevel_name))
            s[0] = self.params['time_buffer_size']
            grid['zlevel'] = np.full(s, 0., dtype=np.float32)

            grid['nz'] = grid['zlevel'].shape[2]
            grid['vertical_grid_type'] = 'Slayer' if self.params['grid_variables']['bottom_cell_index'] is None else 'LSC'
            grid['bottom_cell_index'] = self.read_bottom_cell_index(nc)


        # split quad cells, find model outline, make adjacency matrix etc
        self._build_grid_attributes(grid)

        #now any quad cells are split set up, space for dry cell info
        grid['is_dry_cell'] = np.full((self.params['time_buffer_size'], grid['triangles'].shape[0]), 1, np.int8)
        grid['dry_cell_index'] = np.full((grid['triangles'].shape[0],), 0, np.uint8)  # 0-255 index of how dry each cell is currently, used in stranding, dry cell blocking, and plots

        # other grid info
        self.read_open_boundary_data(grid)


    def read_time(self, nc, file_index=None):
        vname=self.params['grid_variables']['time']
        if file_index is None : file_index = np.arange(nc.get_var_shape(vname)[0])

        time = nc.read_a_variable(vname, sel=file_index)

        if self.params['isodate_of_hindcast_time_zero'] is not None:
            time = time + time_util.date_to_seconds(time_util.date_from_iso8601str(self.params['isodate_of_hindcast_time_zero']))
        if self.params['time_zone'] is not None:
            time += self.params['time_zone']*3600.
        return time

    def read_x(self, nc):
        x = np.full((nc.get_dim_size(self.params['dimension_map']['node']), 2), 0.)
        x[:, 0] = nc.read_a_variable(self.params['grid_variables']['x'][0])
        x[:, 1] = nc.read_a_variable(self.params['grid_variables']['x'][1])
        if self.params['cords_in_lat_long']:
            x = WGS84_to_UTM(x)
        return x

    def read_time_variable_grid_variables(self, nc, buffer_index, file_index):
        # read time and  grid vaiables
        grid = self.grid

        grid['time'][buffer_index] = self.read_time(nc, file_index=file_index)

        if grid['zlevel'] is not None:
            grid['zlevel'][buffer_index, :] = self.read_zlevel(nc,file_index=file_index)



    def read_triangles(self, nc):
        data = nc.read_a_variable(self.params['grid_variables']['triangles'])
        if self.params['one_based_indices']:
            data -= 1

        if np.max(data[:,:3]) >= self.grid['x'].shape[0] or np.min(data[:,:3]) < 0:
            self.write_msg('Grid set up, out of bounds node number  node in triangulation, require zero based indices',
                           exception=FatalError,
                           hint='Ensure reader parameter "one_based_indices" is set correctly for hindcast file')

        elif np.min(data) == 1:
            self.write_msg('Grid set up, smallest node index in triangulation ==1, require zero based indices', warning=True, hint='Ensure reader parameter "one_based_indices" is set correctly for hindcast file')

        return data.astype(np.int32)

    def read_zlevel(self, nc, file_index):
        data = nc.read_a_variable(self.params['grid_variables']['zlevel'], sel=file_index)
        return data

    def read_bottom_cell_index(self, nc):
        # Slayer grid, bottom cell index = zero
        data = np.zeros((self.grid['x'].shape[0],), dtype=np.int32)
        return data


    def _build_grid_attributes(self, grid):
        # build adjacency etc from triangulation

        ntri_in_file = grid['triangles'].shape[0]
        grid['triangles'], grid['triangles_to_split'] = triangle_utilities_code.split_quad_cells(grid['triangles'])

        # expand time varying triangle properties buffers to include new cells, eg drycell buffer
        if grid['triangles_to_split'] is not None:
            for name, item in grid.items():
                if  isinstance(item,np.ndarray)  and len(item.shape) > 1 and item.shape[1] == ntri_in_file:  # those arrays matching  triangle size in file
                    grid[name]= np.full((item.data.shape[0], grid['triangles'].shape[0]), 0, dtype=grid[name].dtype)

        grid['node_to_tri_map'] = triangle_utilities_code.build_node_to_cell_map(grid['triangles'], grid['x'])
        grid['adjacency'] =  triangle_utilities_code.build_adjacency_from_node_cell_map(  grid['node_to_tri_map']  , grid['triangles'])
        grid['boundary_triangles'] = triangle_utilities_code.get_boundary_triangles(grid['adjacency'])
        grid['grid_outline'] = triangle_utilities_code.build_grid_outlines(grid['triangles'], grid['adjacency'], grid['x'],   grid['node_to_tri_map']  )

        # make island and domain nodes
        grid['node_type'] = np.zeros(grid['x'].shape[0], dtype=np.int8)
        for c in grid['grid_outline']['islands']:
            grid['node_type'][c['nodes']] = 1

        grid['node_type'][grid['grid_outline']['domain']['nodes']] = 2

        grid['triangle_area'] = triangle_utilities_code.calcuate_triangle_areas(grid['x'], grid['triangles'])








