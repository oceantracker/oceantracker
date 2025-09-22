import numpy as np
from numba import njit
from datetime import datetime
from oceantracker.reader.generic_unstructured_reader import GenericUnstructuredReader
from copy import copy
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util
from oceantracker.reader.util.reader_util import append_split_cell_data
from oceantracker.util.triangle_utilities_code import split_quad_cells
from pyproj import Proj, transform
from oceantracker.util.ncdf_util import NetCDFhandler, Zarrhandler
import xarray as xr
from time import perf_counter
from os import path
import pandas as pd
from oceantracker.reader.util import reader_util


# todo add optional standard feilds by list of internal names, using a stanard feild maping maping
# todo a way to map al stanard feilds but supress reading them unless requested?
class CSreader(GenericUnstructuredReader):
    # loads a standard SCHISM netcdf output file with nodal data
    # variable names can be tweaked via maps in shared_params, if non-standard names used

    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({  # if be used alongside 3D vel
            'hgrid_file_name': PVC(None, str),
            'field_variables': {'water_velocity': PLC(['u', 'v'], [str], fixed_len=2),
                                'water_depth': PVC('dep', str),
                                'tide': PVC('h', str)},
        })
        self.class_doc(description='Reads CS zarr tides files')
        self.clear_default_params(['grid_variables', 'one_based_indices', 'dimension_map'])  # only used in generic reader

    def convert_lon_lat_to_meters_grid(self, crs, lon, lat):
        in_proj = Proj(init='epsg:%s' % 4326)
        out_proj = Proj(init='epsg:%s' % crs)
        x, y = transform(in_proj, out_proj, lon, lat)
        return x, y

    def is_hindcast3D(self, nc):
        return False  # 2D for now

    # def get_number_of_z_interfaces(self, nc):
    #     return 2

    def is_var_in_file_3D(self, nc, var_name_in_file):
        return False

    def is_file_variable_time_varying(self, nc, var_name_in_file):
        if var_name_in_file == 'dep':
            return False
        else:
            return True

    def get_num_vector_components_in_file_variable(self, nc, file_var_name):
        n_comp = 1
        return n_comp

    def read_dry_cell_data(self, nc, file_index, is_dry_cell_buffer, buffer_index):
        # calculate dry cell flags, if any cell node is dry
        grid = self.grid
        si = self.shared_info
        fields = si.classes['fields']

        if self.params['grid_variables'].get('is_dry_cell', None) is None:
            reader_util.set_dry_cell_flag_from_tide(grid['triangles'],
                                                    fields['tide'].data, fields['water_depth'].data,
                                                    si.minimum_total_water_depth, is_dry_cell_buffer, buffer_index)

        else:
            # get dry cells for each triangle allowing for splitting quad cells
            data_added_to_buffer = nc.read_variable(self.params['grid_variables']['is_dry_cell'], file_index)
            is_dry_cell_buffer[buffer_index, :] = append_split_cell_data(grid, data_added_to_buffer, axis=1)

    def assemble_field_components(self, nc, field, buffer_index=None, file_index=None):
        # read scalar fields / join together the components which make vector from component list

        grid = self.grid

        m = 0  # num of vector components read so far
        var_info = field.info['variable_info']
        all_ts = pd.date_range(self.info['file_info']['date_start'][0], self.info['file_info']['date_end'][0], freq=str(self.info['file_info']['hydro_model_time_step']) + 'S')
        time_to_take = all_ts[file_index]
        if var_info['is_time_varying']:
            tide = nc.file_handle.tide.predict(time_to_take)

        for component_info in var_info['component_list']:
            if var_info['is_time_varying']:
                data = tide[component_info['name_in_file']].values
            else:
                data = nc.file_handle[component_info['name_in_file']].values
            data[np.isnan(data)] = 0
            m1 = m + component_info['num_components']

            # get view of where in buffer data is to be placed

            if var_info['is_time_varying']:
                field.data[buffer_index, :, :, m:m1] = data[:, :, np.newaxis, np.newaxis]
            else:
                field.data[0, :, :, m:m1] = data[:, np.newaxis, np.newaxis]

            m += component_info['num_components']

        # return a view of data added to buffer to allow pre-processing
        data_added_to_buffer = field.data[buffer_index, ...] if field.params['is_time_varying'] else field.data[0, ...]
        return data_added_to_buffer

    def additional_setup_and_hindcast_file_checks(self, nc, msg_logger):
        # sort out which velocity etc are there and adjust field variables
        si = self.shared_info
        params = self.params
        fv = params['field_variables']
        si.settings['run_as_depth_averaged'] = True
        fv['water_velocity'] = ['u', 'v']

    def build_grid(self, nc, grid):
        grid = super().build_grid(nc, grid)
        return grid

    def read_time_sec_since_1970(self, nc, file_index=None):

        start_time = time_util.isostr_to_seconds(self.params['start_time'])
        end_time = time_util.isostr_to_seconds(self.params['end_time'])
        time = np.arange(start_time, end_time, self.params['interval'])
        if file_index is None: file_index = np.arange(0, len(time))

        time = time[file_index]

        # if self.params['isodate_of_hindcast_time_zero'] is not None:
        #     time +=  time_util.isostr_to_seconds(self.params['isodate_of_hindcast_time_zero'])

        # if self.params['time_zone'] is not None:
        #     time += self.params['time_zone'] * 3600.
        return time

    def read_nodal_x_as_float64(self, nc):
        x, y = self.convert_lon_lat_to_meters_grid(self.params['EPSG_transform_code'],
                                                   nc.read_variable('lon'),
                                                   nc.read_variable('lat'))
        x = np.stack((x, y), axis=1).astype(np.float64)
        return x

    def read_triangles_as_int32(self, nc):
        data = nc.read_variable('elements')

        # flag quad cells for spliting
        if data.shape[1] == 4 and np.any(data > 0):
            # split quad grids buy making new triangles
            quad_cells_to_split = data[:, 3] > 0
            data = split_quad_cells(data, quad_cells_to_split)
        else:
            quad_cells_to_split = np.full((data.shape[0],), False, dtype=bool)

        data -= 1  # make index zero based

        return data.astype(np.int32), quad_cells_to_split

    def read_open_boundary_data_as_boolean(self, grid):
        # make boolen of whether node is an open boundary node
        # read schisim  hgrid file for open boundary data

        is_open_boundary_node = np.full((grid['x'].shape[0],), False)
        idx = grid['boundary'].values.astype(int)

        open_bnd = idx[grid['dep'][idx] > 1]  # not ideal for now
        is_open_boundary_node[open_bnd] = True

        return is_open_boundary_node

    # def read_open_boundary_data_as_boolean(self, grid):
    #     # make boolen of whether node is an open boundary node
    #     # read schisim  hgrid file for open boundary data
    #     is_open_boundary_node = np.full((grid['x'].shape[0],),False)

    #     if self.params['hgrid_file_name'] is  None:
    #         return is_open_boundary_node

    #     with open(self.params['hgrid_file_name']) as f:lines = f.readlines()

    #     vals= lines[1].split()
    #     n_nodes= int(vals[0])
    #     n_tri = int(vals[1])

    #     n_line_open= n_nodes+n_tri+3 -1 # line with number of open boundries
    #     n_open= int(lines[n_line_open].split()[0])

    #     if n_open > 0:

    #         tri_open_bound_node_list= [ [] for _ in range(grid['triangles'].shape[0]) ]
    #         nl = n_line_open+1
    #         for n in range(n_open):
    #             # get block of open node numbers
    #             nl += 1 # move to line with number of nodes in this open boundary
    #             n_nodes = int(lines[nl].split()[0])
    #             nodes=[]
    #             for n in range(n_nodes):
    #                 nl += 1
    #                 l = lines[nl].strip('\n')
    #                 nodes.append(int(l))
    #             ob_nodes = np.asarray(nodes, dtype=np.int32)-1

    #             is_open_boundary_node[ob_nodes] = True # get zero based node number

    #     return is_open_boundary_node