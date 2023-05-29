import numpy as np
from oceantracker.util import triangle_utilities_code
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util
from oceantracker.reader._base_reader import _BaseReader
from oceantracker.reader.util import reader_util, shared_reader_memory_util
from datetime import datetime
from time import  perf_counter
from oceantracker.util import json_util, ncdf_util
from os import  path

class GenericUnstructuredReader(_BaseReader):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({ 'dimension_map': {'node': PVC('node', str,is_required=True)},
                                'grid_variables': {'triangles': PVC(None, str, is_required=True)}})

        self.info['buffer_info'] ={'n_filled' : None}
        self.class_doc(description='Generic reader, reading netcdf file variables into variables using given name map between internal and file variable names')


      
    #@profile
    def build_grid(self, nc, grid):
        # set up grid variables which don't vary in time and are shared by all case runners and main
        # add to reader build info
        si = self.shared_info

        grid['x'] = self.read_nodal_x_as_float64(nc).astype(np.float64)
        grid['triangles'], grid['quad_cells_to_split'] = self.read_triangles_as_int32(nc)
        grid['quad_cells_to_split'] = np.flatnonzero(grid['quad_cells_to_split']) # make as list of indcies for calculations


        if self.is_hindcast3D(nc):
            grid['bottom_cell_index'] = self.read_bottom_cell_index_as_int32(nc)
            # below are used in cell find and 3D interp evaluation
            grid['bottom_cell_index_at_triangle_nodes'] = grid['bottom_cell_index'][grid['triangles']]

        # find model outline, make adjacency matrix etc

        grid = self._add_grid_attributes(grid)

        # adjust node type and adjacent for open boundaries
        # todo define node and adjacent type values in dict, for single definition and case info output?
        is_open_boundary_node = self.read_open_boundary_data_as_boolean(grid)
        grid['node_type'][is_open_boundary_node] = 3

        is_open_boundary_adjacent = reader_util.find_open_boundary_faces(grid['triangles'], grid['is_boundary_triangle'],grid['adjacency'], is_open_boundary_node)
        grid['adjacency'][is_open_boundary_adjacent] = -2
        grid['limits'] = np.asarray([np.min(grid['x'][:,0]),np.max(grid['x'][:,0]),np.min(grid['x'][:,1]),np.max(grid['x'][:,1])])

        # now set up time buffers
        time_buffer_size = self.params['time_buffer_size']
        grid['time'] = np.zeros((time_buffer_size,), dtype=np.float64)
        grid['date'] = np.zeros((time_buffer_size,), dtype='datetime64[s]')# time buffer
        grid['nt_hindcast'] = np.full((time_buffer_size,), -10, dtype=np.int32)  # what global hindcast timestesps are in the buffer

        # set up zlevel
        if self.is_hindcast3D(nc) and not si.settings['run_as_depth_averaged']:
            s = [self.params['time_buffer_size'], grid['x'].shape[0], self.get_number_of_z_levels(nc)]
            grid['zlevel'] = np.full(s, 0., dtype=np.float32)
            grid['nz'] = grid['zlevel'].shape[2]
        else:
            grid['zlevel'] = None
            grid['nz'] = 1 # note if 3D

            # space for dry cell info
        grid['is_dry_cell'] = np.full((self.params['time_buffer_size'], grid['triangles'].shape[0] ), 1, np.int8)

        # working space for 0-255 index of how dry each cell is currently, used in stranding, dry cell blocking, and plots
        grid['dry_cell_index'] = np.full((grid['triangles'].shape[0],), 0, np.uint8)

        # note which are time buffers
        return grid

    def check_grid(self,grid):
        tt='Grid Check, '
        # check types of grid variables
        si =self.shared_info
        type_checks={'x': np.float32,'triangles':np.int32}
        for name,t in type_checks.items():
            if grid[name] is not None and grid[name].dtype != t:
                si.msg_logger.msg(tt + 'array dtype of grid variable"' + name + '" does not match required type "' +str(t)+ '"',
                               fatal_error= True,
                               hint='Check read method for this variable converts to required type')

        # check triangulation appears to be zero based index
        if np.max(grid['triangles'][:, :3]) >= self.grid['x'].shape[0] or np.min(grid['triangles'][:, :3]) < 0:
            si.msg_logger.msg(tt+ 'out of bounds node number  node in triangulation, require zero based indices',
                           fatal_error= True, exit_now=True,
                           hint='Ensure reader parameter "one_based_indices" is set correctly for hindcast file')

        elif np.min(grid['triangles']) == 1:
            si.msg_logger.msg(tt+ 'smallest node index in triangulation ==1, require zero based indices',
                           warning=True,
                           hint='Ensure reader parameter "one_based_indices" is set correctly for hindcast file')

    def read_time_sec_since_1970(self, nc, file_index=None):
        vname=self.params['grid_variables']['time']
        if file_index is None : file_index = np.arange(nc.get_var_shape(vname)[0])

        time = nc.read_a_variable(vname, sel=file_index)

        if self.params['isodate_of_hindcast_time_zero'] is not None:
            time +=  time_util.isostr_to_seconds(self.params['isodate_of_hindcast_time_zero'])

        if self.params['time_zone'] is not None:
            time += self.params['time_zone'] * 3600.
        return time

    def read_nodal_x_as_float64(self, nc):
        si=self.shared_info
        gv= self.params['grid_variables']
        x = np.stack((nc.read_a_variable(gv['x'][0]), nc.read_a_variable(gv['x'][1])), axis=1).astype(np.float64)
        if self.params['cords_in_lat_long']:
            #todo write warning of conversion to meters grid
            x = self.convert_lon_lat_to_meters_grid(x)
        return x

    def read_time_variable_grid_variables(self, nc, buffer_index, file_index):
        # read time and  grid variables, eg time, tide, zlevel
        grid = self.grid

        grid['time'][buffer_index] = self.read_time_sec_since_1970(nc, file_index=file_index)

        # add date for convenience
        grid['date'][buffer_index] = time_util.seconds_to_datetime64(grid['time'][buffer_index])

        if grid['zlevel'] is not None:
            # read zlevel inplace to save memory?
            self.read_zlevel_as_float32(nc, file_index, grid['zlevel'], buffer_index)

        self.read_dry_cell_data(nc, file_index, grid['is_dry_cell'],buffer_index)

    def read_triangles_as_int32(self, nc):
        data = nc.read_a_variable(self.params['grid_variables']['triangles'])
        if self.params['one_based_indices']:  data -= 1
        quad_cells_to_split = np.full((data.shape[0],),False,dtype=bool)
        return data[:, :3].astype(np.int32), quad_cells_to_split

    def read_zlevel_as_float32(self, nc, file_index, zlevel_buffer, buffer_index):
        # read in place
        zlevel_buffer[buffer_index,:] = nc.read_a_variable(self.params['grid_variables']['zlevel'], sel=file_index).astype(np.float32)

    def read_bottom_cell_index_as_int32(self, nc):
        # Slayer grid, bottom cell index = zero
        data = np.zeros((self.grid['x'].shape[0],), dtype=np.int32)
        return data

    #@profile
    def _add_grid_attributes(self, grid):
        # build adjacency etc from triangulation
        msg_logger = self.msg_logger

        t0 = perf_counter()
        grid['node_to_tri_map'],grid['tri_per_node'] = triangle_utilities_code.build_node_to_cell_map(grid['triangles'], grid['x'])
        msg_logger.progress_marker('built node to triangles map', start_time=t0)

        t0 = perf_counter()
        grid['adjacency'] =  triangle_utilities_code.build_adjacency_from_node_cell_map(grid['node_to_tri_map'],grid['tri_per_node'], grid['triangles'])
        msg_logger.progress_marker('built triangle adjacency matrix', start_time=t0)

        t0 = perf_counter()
        grid['is_boundary_triangle'] = triangle_utilities_code.get_boundary_triangles(grid['adjacency'])
        msg_logger.progress_marker('found boundary triangles', start_time=t0)
        t0 = perf_counter()
        grid['grid_outline'] = triangle_utilities_code.build_grid_outlines(grid['triangles'], grid['adjacency'],
                                                    grid['is_boundary_triangle'], grid['node_to_tri_map'], grid['x'])

        msg_logger.progress_marker('built domain and island outlines', start_time=t0)

        # make island and domain nodes
        grid['node_type'] = np.zeros(grid['x'].shape[0], dtype=np.int8)
        for c in grid['grid_outline']['islands']:
            grid['node_type'][c['nodes']] = 1

        grid['node_type'][grid['grid_outline']['domain']['nodes']] = 2

        t0 = perf_counter()
        grid['triangle_area'] = triangle_utilities_code.calcuate_triangle_areas(grid['x'], grid['triangles'])
        msg_logger.progress_marker('calculated triangle areas', start_time=t0)
        msg_logger.msg('Finished grid setup', tabs=1)
        return grid


    def is_hindcast3D(self, nc):
        #is zlevel defined then it is 3D
        return  self.params['grid_variables']['zlevel'] is not None

    def write_hydro_model_grid(self):
        # write a netcdf of the grid from first hindcast file
        si =self.shared_info
        output_files = si.output_files
        grid = self.grid

        # write grid file
        output_files['grid'] = output_files['output_file_base'] + '_grid.nc'
        nc = ncdf_util.NetCDFhandler(path.join(output_files['run_output_dir'], output_files['grid'] ), 'w')
        nc.write_global_attribute('Notes', ' all indices are zero based')
        nc.write_global_attribute('created', str(datetime.now().isoformat()))

        nc.write_a_new_variable('x', grid['x'], ('node_dim', 'vector2D'))
        nc.write_a_new_variable('triangles', grid['triangles'], ('triangle_dim', 'vertex'))
        nc.write_a_new_variable('triangle_area', grid['triangle_area'], ('triangle_dim',))
        nc.write_a_new_variable('adjacency', grid['adjacency'], ('triangle_dim', 'vertex'))
        nc.write_a_new_variable('node_type', grid['node_type'], ('node_dim',), attributesDict={'node_types': ' 0 = interior, 1 = island, 2=domain, 3=open boundary'})
        nc.write_a_new_variable('is_boundary_triangle', grid['is_boundary_triangle'], ('triangle_dim',))
        nc.write_a_new_variable('water_depth', si.classes['fields']['water_depth'].data.squeeze(), ('node_dim',))
        nc.close()

        output_files['grid_outline'] = output_files['output_file_base'] + '_grid_outline.json'
        json_util.write_JSON(path.join(output_files['run_output_dir'], output_files['grid_outline']), grid['grid_outline'])


