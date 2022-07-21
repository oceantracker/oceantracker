import numpy as np
from copy import copy, deepcopy
from oceantracker.util import triangle_utilities_code
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.message_and_error_logging import append_message, GracefulExitError
from oceantracker.util import time_util
from oceantracker.fields.util import fields_util
from os import path, walk
from glob import glob
from oceantracker.util.ncdf_util import NetCDFhandler
from time import perf_counter
from datetime import datetime

from oceantracker.reader._base_reader import BaseReader

class GenericUnstructuredReader(BaseReader):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({ 'dimension_map': {'node': PVC('node', str)}} )

        self.buffer_info ={'n_filled' : None}


    def build_reader(self, reader_build_info):
        si = self.shared_info
        self.reader_build_info = reader_build_info

        fm = si.classes['field_group_manager']

        self.code_timer.start('build_hindcast_reader')
        nc = NetCDFhandler(reader_build_info['sorted_file_info']['names'][0], 'r')

        self.read_hindcast_info(nc)
        si.grid = self._setup_grid(nc,reader_build_info)

        # setup fields
        for name, item in self.params['field_variables'].items():
            if item is None: continue

            #if type(item) == list:
            #    # add vector fields by method
            #    class_params = getattr(self,'read_' + name)(nc, name, setup=True)
            #else:
                # add scalar fields by read_scalar_field
            class_params= self.get_field_variable_info(nc,name)
                #class_params = self.read_scalar_field(nc, name, setup=True)

            i = fm.add_field('from_reader_field', class_params, crumbs = 'Adding field derived from reader field >>> ' + name)
            i.initialize()

            if not i.params['is_time_varying']:
                # if not time dependent read in now, eg water_depth
                i.data[:] = self.read_field_variable_as4D(nc, i)

            # set up depth averaged version if requested
            if name in self.params['field_variables_to_depth_average']:
                # tweak shape to fit depth average of scalar or 3D vector
                p = deepcopy(i.params)
                p['is3D'] = False
                if i.get_number_components() == 3: p['num_components'] = 2
                p['name'] = name + '_depth_average'
                i2 = fm.add_field('depth_averaged_from_reader_field', p, crumbs='Adding depth averaged field, derived from reader field >>> ' + name)
                i2.initialize()

        # get dry cells from total water depth
        si.hindcast_is3D = si.classes['fields']['water_velocity'].is3D()
        nc.close()

        # add total water depth as core field if possible
        if si.grid['zlevel'] is not None or ('tide' in si.classes['fields'] and 'water_depth' in si.classes['fields']):
            params={'name': 'total_water_depth','class_name':'oceantracker.fields.total_water_depth.TotalWaterDepth'}
            i = fm.add_field('derived_from_reader_field', params, crumbs='Adding total water depth derived from  tide and water depth, or zlevel if 3D')
            i.initialize()
        else:
            si.case_log.write_write_warning('No tidal stranding, requires total water depth derived from  tide and water depth, or zlevel if 3D')


        # needed for force read at first time step read to make
        self.buffer_info['n_filled'] = 0
        self.buffer_info['nt_buffer0'] = 0

        self.code_timer.stop('build_hindcast_reader')

    def _setup_grid(self, nc,reader_build_info):

        grid={'x': None, 'triangles': None, 'zlevel' : None,
              'has_open_boundary_data': False}
        # load grid variables
        grid['time'] = np.full((self.params['time_buffer_size'],),0.) # time buffer
        grid['x'] =  self.read_x(nc)

        grid['triangles'] = self.read_triangles(nc)
        grid['nz'] = 1

        if self.params['grid_variables']['zlevel'] is not None:
            grid['zlevel'] = self.read_zlevel(nc,setup=True)
            grid['nz'] = grid['zlevel'].shape[2]

            if self.params['grid_variables']['bottom_cell_index'] is None:
                grid['vertical_grid_type'] = 'Slayer'
            else:
                grid['vertical_grid_type'] = 'LSC'
                grid['bottom_cell_index'] = self.read_bottom_cell_index(nc, num_tri= grid['triangles'].shape[0])

        # dry cell buffer, default is not dry so no cel is blocked from entry
        grid['is_dry_cell'] = np.full((self.params['time_buffer_size'],grid['triangles'].shape[0]), 1,np.int8)

        # split quad cells, find model outline, make adjacency matrix etc
        grid = self._build_grid_attributes(grid)
        grid = self.read_open_boundary_data(grid)
        return grid


    def read_time(self, nc, file_index=None):
        vname=self.params['grid_variables']['time']
        if file_index is None : file_index =np.arange(nc.get_var_shape(vname)[0])

        time = nc.read_a_variable(vname,file_index)

        if self.params['isodate_of_hindcast_time_zero'] is not None:
            time = time + time_util.date_to_seconds(time_util.date_from_iso8601str(self.params['isodate_of_hindcast_time_zero']))
        if self.params['time_zone'] is not None:
            time += self.params['time_zone']*3600.
        return time

    def read_time_variable_grid_variables(self, nc, buffer_index, file_index):
        # read time and  grid vaiables
        grid= self.shared_info.grid
        grid['time'][buffer_index] = self.read_time(nc, file_index=file_index)
        if grid['zlevel'] is not None:
            grid['zlevel'][buffer_index, :] = self.read_zlevel(nc, file_index=file_index)

    def read_triangles(self, nc):
        return nc.read_a_variable(self.params['grid_variables']['triangles'])

    def read_zlevel(self, nc, file_index=None, setup=False):
        var_name = self.params['grid_variables']['zlevel']
        if setup:
            s = list(nc.get_var_shape(var_name))
            s[0] = self.params['time_buffer_size']
            return np.full(s, 0, nc.get_var_dtype(var_name))
        else:
            data = nc.read_a_variable(self.params['grid_variables']['zlevel'], sel=file_index)
            return data

    def read_bottom_cell_index(self, nc, num_tri= None):
        if nc.is_var(self.params['grid_variables']['bottom_cell_index']):
            data = nc.read_a_variable(self.params['grid_variables']['bottom_cell_index'])
        else:
            # Slayer grid, bottom cell is zero
            data = np.zeros((num_tri,),dtype=np.int8)
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

        return grid







