import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
import oceantracker.reader.util.hydromodel_grid_transforms as  hydromodel_grid_transforms
from oceantracker.reader.util import reader_util
from oceantracker.reader.dev._base_generic_reader import BaseGenericReader
from copy import  deepcopy

from oceantracker.shared_info import shared_info as si

class GenericUnstructuredReader(BaseGenericReader):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params(
                dimension_map=dict(node= PVC('node', str)),
                grid_variable_map =dict( triangles= PVC(None, str)),
             )  # list of normal required dimensions


    def is_file_format(self,file_name):
        # check if file matches this file format
        nc = self._open_file(file_name)
        gm = self.params['grid_variable_map']
        fm  = self.params['field_variable_map']
        dm = self.params['dimension_map']

        is_file_type=  nc.is_dim(dm['time']) and nc.is_dim(dm['node']) and nc.is_var(gm['x'][0]) and nc.is_var(gm['x'][1]) and nc.is_var(fm['tide']) and nc.is_var(fm['water_depth'])
        nc.close()
        return is_file_type


    def is_3D_variable(self,nc, var_name):
        # is variable 3D
        return  nc.is_var_dim(var_name,self.params['dimension_map']['z'])


    def build_hori_grid(self, nc, grid):
        # read nodal values and triangles
         
        ml = si.msg_logger
        params = self.params
        grid_map= params['grid_variable_map']

        for v in grid_map['x'] + [grid_map['triangles'], grid_map['time']]:
            if not nc.is_var(v):
                ml.msg(f'Cannot find variable "{v}" in file "{nc.file_name}" ', crumbs='in grid set', fatal_error=True, caller=self)
                return
        grid =  {}

        # read nodal x's

        grid = self.read_horizontal_grid_coords(nc, grid)
        grid['x'] = grid['x'].astype(np.float64)

        grid = self.read_triangles(nc, grid)
        # ensure np.int32 values
        grid['triangles']=grid['triangles'].astype(np.int32)
        grid['quad_cells_to_split'] = grid['quad_cells_to_split'].astype(np.int32)

        return grid

    def field_var_info(self,nc,file_var_map):
         
        ml = si.msg_logger
        params = self.params
        dim_map= params['dimension_map']

        # get dim sized from  vectors and scalers
        if type(file_var_map) != list : file_var_map = [file_var_map]
        var_list = [v for v in file_var_map if v != None]

        is_vector = len(var_list) > 1
        for v in var_list:
            if not nc.is_var(v):
                ml.msg(f'Cannot find variable "{v}" in file "{nc.file_name}" ', crumbs='in reader set up fields', fatal_error=True, caller=self)
                continue
            if dim_map['vector2D'] in nc.all_var_dims(v) or dim_map['vector3D'] in nc.all_var_dims(v):
                is_vector = True

        out = dict(time_varying=dim_map['time'] in nc.all_var_dims(var_list[0]),
                 is3D= self.is_3D_variable(nc, var_list[0]),
                 is_vector= is_vector)

        return out



    # Below are basic variable read methods for any new reader
    #---------------------------------------------------------


    def read_time_sec_since_1970(self, index=None):
        vname = self.params['grid_variable_map']['time']
        if file_index is None: file_index = np.arange(nc.var_shape(vname)[0])

        time = nc.read_a_variable(vname, sel=file_index)

        if self.params['isodate_of_hindcast_time_zero'] is not None:
            time += self.params['isodate_of_hindcast_time_zero']
        return time

    def read_horizontal_grid_coords(self, nc, grid):
        params= self.params
        var_name = params['grid_variable_map']['x']
        grid['x'] = np.column_stack((nc.read_a_variable(var_name[0]), nc.read_a_variable(var_name[1]))).astype(np.float64)

        if self.params['hydro_model_cords_in_lat_long']:
            grid['x'] = self.convert_lon_lat_to_meters_grid(grid['x'])

        return grid

    def read_triangles(self, nc, grid):
        # return triangulation
        # if triangualur has /quad cells
        params = self.params
        var_name = params['grid_variable_map']['triangles']
        grid['triangles'] = nc.read_a_variable(var_name).astype(np.int32)

        if params['one_based_indices']:  grid['triangles'] -= 1

        # note indices of any triangles neeeding splitting
        grid['quad_cells_to_split'] =  np.full((0,),0, np.int32)

        if self.detect_lonlat_grid(grid['x']):
            # try auto detection
            grid['hydro_model_cords_in_lat_long'] = True
        else:
            grid['hydro_model_cords_in_lat_long'] = self.params['hydro_model_cords_in_lat_long']

        return grid







    def set_up_uniform_sigma(self, nc, grid):
        # read z fractions into grid , for later use in vertical regridding, and set up the uniform sigma to be used
         
        # read first zlevel time step
        zlevel = nc.read_a_variable(self.params['grid_variable_map']['zlevel'], sel=0)
        bottom_cell_index = self.read_bottom_cell_index_as_int32(nc).astype(np.int32)
        # use node with thinest top/bot layers as template for all sigma levels

        node_min, grid['zlevel_fractions'] = hydromodel_grid_transforms.find_node_with_smallest_bot_layer(zlevel, bottom_cell_index, si.settings.z0)

        # use layer fractions from this node to give layer fractions everywhere
        # in LSC grid this requires stretching a bit to give same number max numb. of depth cells
        nz_bottom = bottom_cell_index[node_min]

        # stretch sigma out to same number of depth cells,
        # needed for LSC grid if node_min profile is not full number of cells
        zf_model = grid['zlevel_fractions'][node_min, nz_bottom:]
        nz = grid['zlevel_fractions'].shape[1]
        nz_fractions = nz - nz_bottom
        grid['sigma'] = np.interp(np.arange(nz) / nz, np.arange(nz_fractions) / nz_fractions, zf_model)

        return grid


    def assemble_field_components(self,nc, grid, name, field, file_index=None):
        # read scalar fields / join together the components which make vector from component list
        params = self.params

        s= list(field.data.shape)
        s[0] = 1 if file_index is None else file_index.size
        out  = np.zeros(s,dtype=np.float32) #todo faster make a generic  buffer at start

        m= 0 # num of vector components read so far

        var_names = params['field_variable_map'][name] if type(params['field_variable_map'][name]) ==list  else [params['field_variable_map'][name]]

        for var_name in var_names:
            if var_name is None: continue
            data = self.read_file_var_as_4D_nodal_values(nc, grid, var_name, file_index)
            comp_per_var = data.shape[3]
            m1 = m + comp_per_var
            # get view of where in buffer data is to be placed
            out[:, :, :, m:m1] = data
            m += comp_per_var
        return out

    def read_file_var_as_4D_nodal_values(self,nc, grid, var_name, file_index=None):
        # read variable into 4D ( time, node, depth, comp) format
        # assumes same variable order in the file
        dm = self.params['dimension_map']
        data = nc.read_a_variable(var_name, sel=file_index)
        # get 4d size
        s= [0,0,0,0]
        s[0] = data.shape[0] if nc.is_var_dim(var_name,dm['time']) else 1
        s[1] = nc.dim_size(self.params['dimension_map']['node'])

        # see if z or z water level  in variable
        if  nc.is_var_dim(var_name,dm['z']) :
            s[2] = nc.dim_size(self.params['dimension_map']['z'])

        elif nc.is_var_dim(var_name, dm['z_water_velocity']):
            s[2] = nc.dim_size(self.params['dimension_map']['z_water_velocity'])
        else:
            s[2] = 1

        if nc.is_var_dim(var_name, dm['vector2D']):
            s[3] = 2
        elif  nc.is_var_dim(var_name, dm['vector3D']):
            s[3] = 3
        else:
            s[3] = 1

        return data.reshape(s)


    def read_dry_cell_data(self,nc,grid, fields, file_index,is_dry_cell_buffer, buffer_index):
        # calculate dry cell flags, if any cell node is dry
         

        if self.params['grid_variable_map']['is_dry_cell'] is None:
            if grid['zlevel'] is None and 'tide' in fields and 'water_depth' in fields:
                # calc dry cell from min water depth
                reader_util.set_dry_cell_flag_from_tide( grid['triangles'],
                                                        fields['tide'].data, fields['water_depth'].data,
                                                        si.settings.minimum_total_water_depth, is_dry_cell_buffer,buffer_index)
            else:
                # from bottom zlevel
                reader_util.set_dry_cell_flag_from_zlevel( grid['triangles'],
                                                          grid['zlevel'], grid['bottom_cell_index'],
                                                          si.settings.minimum_total_water_depth, is_dry_cell_buffer,buffer_index)
        else:
            # get dry cells from hydro file for each triangle allowing for splitting quad cells
            self.read_dry_cell_data(self, nc, grid, fields, file_index, is_dry_cell_buffer, buffer_index)

    def read_zlevel_as_float32(self, nc,grid,fields, file_index, zlevel_buffer, buffer_index):
        # read in place
        zlevel_buffer[buffer_index,...] = nc.read_a_variable('zcor', sel=file_index).astype(np.float32)


    # convert, time etc to hindcast/ buffer index
    def time_to_hydro_model_index(self, time_sec):
        #convert date time to global time step in hindcast just before/after when forward/backtracking
        # always move forward through buffer, but file info is always forward in time
         
        fi = self.info['file_info']

        hindcast_fraction= (time_sec - fi['first_time']) / (fi['last_time'] - fi['first_time'])
        nt = (fi['time_steps_in_hindcast'] - 1) *  hindcast_fraction

        # if back tracking round up as moving backwards through buffer, forward round down
        return np.int32(np.floor(nt*si.run_info.model_direction)*si.run_info.model_direction)

    def hydro_model_index_to_buffer_offset(self, nt_hindcast):
        # ring buffer mapping
        return nt_hindcast % self.info['buffer_info']['buffer_size']

    def are_time_steps_in_buffer(self, time_sec):
        # check if next two steps of remaining  hindcast time steps required to run  are in the buffer
         
        bi = self.info['buffer_info']
        model_dir = si.run_info.model_direction

        # get hindcast time step at current time
        nt_hindcast = self.time_to_hydro_model_index(time_sec)

        return  nt_hindcast in bi['time_steps_in_buffer'] and nt_hindcast + model_dir in bi['time_steps_in_buffer']



    def close(self):
       pass