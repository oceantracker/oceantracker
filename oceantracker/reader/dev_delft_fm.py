from oceantracker.reader._base_reader import _BaseReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
from oceantracker.reader.util.hydromodel_grid_transforms import convert_regular_grid_to_triangles
import  oceantracker.util.time_util as time_util
import numpy as np
from datetime import  datetime,timezone
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util.triangle_utilities import split_quad_cells
from oceantracker.reader.util import  reader_util
from oceantracker.reader.util import  hydromodel_grid_transforms

from oceantracker.shared_info import SharedInfo as si

class DELFTFM(_BaseReader):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({
            'load_fields' : PLC(['water_depth'], [str], doc_str='always load tide and water depth, for dry cells id 2D'),
            'grid_variable_map': {'time': PVC('time', str),
                                  'x': PLC(['mesh2d_node_x', 'mesh2d_node_y'], [str], fixed_len=2),
                                  'x_cell': PLC(['mesh2d_face_x', 'mesh2d_face_y'], [str], fixed_len=2),
                                  'zlevel': PVC(None, str),
                                  'triangles': PVC('mesh2d_face_nodes', str),
                                  'bottom_cell_index': PVC(None, str),
                                  'is_dry_cell': PVC('wetdry_elem', np.int8, doc_str='Time variable flag of when cell is dry, 1= is dry cell')},
            'field_variable_map': {'water_velocity': PLC(['mesh2d_ucx', 'mesh2d_ucy', 'mesh2d_ucz'], [str], fixed_len=3),
                                   'tide': PVC('mesh2d_s1', str, doc_str='maps standard internal field name to file variable name'),
                                   'water_depth': PVC('mesh2d_node_z', str, doc_str='maps standard internal field name to file variable name'),
                                   'water_temperature': PVC('temp', str, doc_str='maps standard internal field name to file variable name'),
                                   'salinity': PVC('salt', str, doc_str='maps standard internal field name to file variable name'),
                                   'wind_stress': PVC('wind_stress', str, doc_str='maps standard internal field name to file variable name'),
                                   'bottom_stress': PVC('bottom_stress', str, doc_str='maps standard internal field name to file variable name'),
                                   'A_Z_profile': PVC('diffusivity', str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                   'water_velocity_depth_averaged': PLC(['mesh2d_ucx','mesh2d_ucy'], [str], fixed_len=2,
                                                                        doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },

        })

    def is_file_format(self,file_name):
        # check if file matches this file format
        ml = si.msg_logger
        nc = NetCDFhandler(file_name,'r')
        is_file_type= nc.is_var('mesh2d_node_x') and nc.is_var('mesh2d_face_nodes')

        mesh2d_face_nodes = nc.read_a_variable('mesh2d_face_nodes')
        if mesh2d_face_nodes.shape[1] > 4:
            ml.msg(f'Reader currently only works with triangle and quad cells, not cells with {mesh2d_face_nodes.shape[1]} sides',
                     fatal_error=True, exit_now= True, caller=self)
        nc.close()
        return is_file_type

    def read_time_sec_since_1970(self, nc, file_index=None):
        var_name = self.params['grid_variable_map']['time']
        time = nc.read_a_variable(var_name, sel=file_index)
        units = nc.var_attr(var_name,'units')

        s= units.split('since ')[-1]
        date_str,time_zone_str= s.rsplit(' ', 1)
        d0 = datetime.fromisoformat(s)
        self.info['time_zone'] =  'TODO decode time zone'

        d0 = np.datetime64(d0).astype('datetime64[s]')
        sec = time_util.datetime64_to_seconds(d0)
        time += sec
        return time

    def read_horizontal_grid_coords(self, nc, grid):

        var_names = self.params['grid_variable_map']['x']
        x = np.stack((nc.read_a_variable(var_names[0]), nc.read_a_variable(var_names[1])), axis=1).astype(np.float64)
        var_names_cell = self.params['grid_variable_map']['x_cell']
        x_cell = np.stack((nc.read_a_variable(var_names_cell[0]), nc.read_a_variable(var_names_cell[1])), axis=1).astype(np.float64)

        if 'degree' in nc.var_attr(var_names[0],'units').lower() :
            grid['hydro_model_cords_in_lat_long'] = True
            grid['lon_lat'] = x.copy()
            si._setup_lon_lat_to_meters_grid_tranforms(grid['lon_lat'])
            grid['x'] = si._transform_lon_lat_to_meters(grid['lon_lat'])
            grid['lon_lat_cell'] = x_cell.copy()
            grid['x_cell'] = si._transform_lon_lat_to_meters(grid['lon_lat_cell'])

        else:
            grid['hydro_model_cords_in_lat_long'] = False
            grid['x'] = x
            grid['x_cell'] = x_cell

        return grid

    def read_triangles_as_int32(self, nc, grid):

        grid['quad_face_nodes'] = nc.read_a_variable(self.params['grid_variable_map']['triangles']).astype(np.int32)
        grid['quad_face_nodes'] -= 1 # make zero based

        # split quad cells aby adding new triangles
        # flag quad cells for splitting if index in 4th column

        # split quad grids buy making new triangles
        # -1000 values are triangles not quad cells < 0 so will be split
        if grid['quad_face_nodes'].shape[1] == 4:
            grid['quad_cells_to_split'] = np.flatnonzero(grid['quad_face_nodes'][:, 3] > 0).astype(np.int32)
            grid['triangles'] = split_quad_cells(grid['quad_face_nodes'], grid['quad_cells_to_split'])
        else:
            grid['triangles'] = grid['quad_face_nodes']
            grid['quad_cells_to_split'] = np.arange(0).astype(np.int32)
        return grid

    def is_hindcast3D(self, nc):

        ml = si.msg_logger
        uname=self.params['field_variable_map']['water_velocity'][0]
        is3D = nc.is_var_dim(uname,'nmesh2d_layer')
        is3D = is3D or nc.is_var_dim(uname,'mesh2d_nLayers')
        if is3D:
            ml.msg('reading DELFT3D 3D hincasts is under development, contact developer for update ',
                     fatal_error=True, exit_now=True, caller=self)
        return is3D
    def setup_water_velocity(self, nc,grid):
        # tweak to be depth averaged
        fm = self.params['field_variable_map']
        var_file_name=fm['water_velocity'][0]

        if si.run_info.is3D_run:#
            # todo 3D not working yet
            #  3D velocity, check if vertical vel file exits
            if self.get_3D_var_file_name(nc,fm['water_velocity'][2]) is not None:
                # drop vertical velocity varaible
                fm['water_velocity'] = fm['water_velocity'][:2]
        else:
            fm['water_velocity'] =fm['water_velocity_depth_averaged']
        pass

    def get_field_params(self,nc, name):
        fmap = self.params['field_variable_map']
        f_params = dict(time_varying=nc.is_var_dim(fmap[name][0], 'time'),
                        is3D=nc.is_var_dim(fmap[name][0], 'mesh2d_nLayers'),
                        is_vector=len(fmap[name]) > 1
                        )
        return f_params

    def read_dry_cell_data(self, nc, grid, fields, file_index, is_dry_cell_buffer, buffer_index):
        # get dry cells from water depth and tide
        # no tide data so set on min water depth?

        mean_water_depth = np.nanmean(fields['water_depth'].data[0,:,0,0][grid['triangles']],axis=1)

        is_dry_cell_buffer[buffer_index,:]=  mean_water_depth < si.settings.minimum_total_water_depth

        reader_util.set_dry_cell_flag_from_tide(grid['triangles'],  fields['tide'].data, fields['water_depth'].data,
                                                si.settings.minimum_total_water_depth, is_dry_cell_buffer, buffer_index)
        pass

    def set_up_uniform_sigma(self,nc, grid):

        pass

    def build_hori_grid(self, nc, grid):

        super().build_hori_grid(nc, grid)

        # setp up node to face map and weights needed
        # to gret nodal values from face values

        grid['node_to_quad_cell_map'],grid['quad_cells_per_node'] = hydromodel_grid_transforms.get_node_to_cell_map(grid['quad_face_nodes'], grid['x'].shape[0])

        # get weights based on inverse distance between node
        # and data inside quad cell interior

        grid['edge_val_weights'] =hydromodel_grid_transforms.calculate_inv_dist_weights_at_node_locations(
                                            grid['x'], grid['x_cell'],
                                            grid['node_to_quad_cell_map'], grid['quad_cells_per_node'])

        return  grid

    def read_file_var_as_4D_nodal_values(self,nc,grid, var_name, file_index=None):
        # read variable into 4D ( time, node, depth, comp) format
        # assumes same variable order in the file

        data = nc.read_a_variable(var_name, sel=file_index)

        # add time dim if needed
        if not nc.is_var_dim(var_name, 'time'):
            data  = data[np.newaxis, ...]

        # see if z or z water level  in variable and swap z and node dim
        if nc.is_var_dim(var_name,'siglay') :
            #3D mid layer values
            # convert mid-layer values to values at layer boundaries, ie zlevels
            data = hydromodel_grid_transforms.convert_layer_field_to_levels_from_depth_fractions_at_each_node(
                                data, grid['zlevel_fractions_layer'], grid['zlevel_fractions'])
        elif not nc.is_var_dim(var_name, 'siglev') :
            # 2D field
            data =    data = data[..., np.newaxis]

        # add dummy vector component to make 4D
        data = data[:, :, :, np.newaxis]

        # some variables at nodes, some at edge mid points ( eg u,v,w)
        if nc.is_var_dim(var_name, 'mesh2d_nFaces'):
            # data is at cell center/element/triangle  move to nodes
            data = hydromodel_grid_transforms.get_nodal_values_from_weighted_data(data, grid['node_to_quad_cell_map'], grid['quad_cells_per_node'], grid['edge_val_weights'])

        return data

    def preprocess_field_variable(self, nc, name,grid, data):


        if name =='water_depth':
            # depth seems to be read as upwards z at node, so revese z
            data = -data
        return data




