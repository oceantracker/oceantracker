from oceantracker.reader._base_reader import _BaseReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
from oceantracker.reader.util.hydromodel_grid_transforms import convert_regular_grid_to_triangles
import  oceantracker.util.time_util as time_util
import numpy as np
from datetime import  datetime
from oceantracker.util.ncdf_util import NetCDFhandler
class GLORYSreaderSurface(_BaseReader):

    def __init__(self, shared_memory_info=None):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({
            'dimension_map': {'time': PVC('time', str),
                              'depth': PVC('depth', str),
                              #'z': PVC(None, str,doc_str='name of dim for vertical layer boundaries'),
                              #'z_water_velocity': PVC('z', str, doc_str='z dimension of water velocity'),
                              #'vector2D': PVC(None, str),
                              #'vector3D': PVC(None, str)
                              },
            'grid_variable_map': {'time': PVC('time', str),
                                  'x': PLC(['longitude', 'latitude'], [str], fixed_len=2),
                                  'zlevel': PVC('zcor', str),
                                  'mask': PVC('mask', str),
                                  'triangles': PVC('SCHISM_hgrid_face_nodes', str),
                                  #'bottom_cell_index': PVC('node_bottom_index', str),
                                  'is_dry_cell': PVC('wetdry_elem', np.int8, doc_str='Time variable flag of when cell is dry, 1= is dry cell')},
            'field_variable_map': {'water_velocity': PLC(['utotal', 'vtotal'], [str], fixed_len=2),
                                   'tide': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                                   'water_depth': PVC('depth', str, doc_str='maps standard internal field name to file variable name'),
                                   #'water_temperature': PVC('temp', str, doc_str='maps standard internal field name to file variable name'),
                                   #'salinity': PVC('salt', str, doc_str='maps standard internal field name to file variable name'),
                                   #'wind_stress': PVC('wind_stress', str, doc_str='maps standard internal field name to file variable name'),
                                   #'bottom_stress': PVC('bottom_stress', str, doc_str='maps standard internal field name to file variable name'),
                                   #'A_Z_profile': PVC('diffusivity', str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                   #'water_velocity_depth_averaged': PLC(['dahv'], [str], fixed_len=2,
                                   #                                     doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
        'water_depth_file': PVC(None, str),

        })

    def is_hindcast3D(self, nc):  return False # only 2D
    def read_time_sec_since_1970(self, nc, file_index=None):
        # time base hours since 1950-01-01 00:00:00
        unit = nc.var_attr('time','units')
        base_date=unit.split('since')[-1].strip()
        d0 = datetime.strptime(base_date,'%Y-%m-%d')
        d0 = np.datetime64(d0).astype('datetime64[s]')

        time = 3600.*nc.read_a_variable(self.params['grid_variable_map']['time'],sel=file_index)
        sec = time_util.datetime64_to_seconds(d0)
        time += sec
        return time

    def read_grid_coords(self, nc, grid):
        gm = self.params['grid_variable_map']
        # get x and y grid

        lat = nc.read_a_variable(gm['x'][1]).astype(np.float64)
        lon = nc.read_a_variable(gm['x'][0]).astype(np.float64)
        #lon -= 90 # todo hack to move ross sea from spanning date line
        #lon[sel] = lon[sel] - 180

        grid['lon'], grid['lat'] = np.meshgrid(lon, lat)
        grid['lon_lat_grid'] =  np.stack(( grid['lon'], grid['lat']),  axis=2)

        s=   grid['lon_lat_grid'].shape
        grid['lon_lat']=   grid['lon_lat_grid'].reshape(s[0]*s[1],s[2])
        grid['hydro_model_cords_in_lat_long'] = True
        grid['x'] = self.convert_lon_lat_to_meters_grid(grid['lon_lat'])

        return grid

    def build_hori_grid(self, nc, grid):

        si = self.shared_info
        # pre-read useful info
        # make land mask from velocity field
        #grid['land_mask']  = nc.read_a_variable(self.params['grid_variable_map']['mask']) == 0

        # give land mak not he same as velo mask, so use
        #u = nc.read_a_variable(self.params['field_variable_map']['water_velocity'][0], sel=0)
        #v = nc.read_a_variable(self.params['field_variable_map']['water_velocity'][1], sel=0)
        # depth seems to give best mask
        depth = nc.read_a_variable(self.params['field_variable_map']['water_depth'])

        grid['land_mask'] = depth > 1.0E36

        grid = super().build_hori_grid(nc, grid)
        return grid

    def read_triangles_as_int32(self, nc, grid):
        # build triangles from regular grid
        grid = convert_regular_grid_to_triangles(grid, grid['land_mask'])
        return grid

    #def preprocess_field_variable(self, nc, name,grid, data):
    #    #todo hack ip make stronger flows
    #    if name=='water_velocity':
    #        data= data*2.
    #    return  data
    def read_open_boundary_data_as_boolean(self, grid):
        # and make this part of the read grid method

        # read hgrid file for open boundary data
        is_open_boundary_node = np.full((grid['land_mask'].shape), False)

        # flag all edges of regular as open boundaries
        # this will pick up most open boundary nodes, but not internal rivers
        is_open_boundary_node[:,[0,-1]] = True
        is_open_boundary_node[[0, -1],:] = True

        # only flag those  as open which are part of the ocean
        is_open_boundary_node = np.logical_and(is_open_boundary_node,~grid['land_mask'])
        #todo write note open boundary data avaible, chose OBC mode param
        s = is_open_boundary_node.shape
        is_open_boundary_node = is_open_boundary_node.reshape((s[0]*s[1],))
        return is_open_boundary_node

    def get_field_params(self, nc, name, crumbs=''):
        # work out if field is 3D ,etc from its map
        # for 2D only
        fmap = self.params['field_variable_map'][name]
        dmap=  self.params['dimension_map']
        if type(fmap) != list: fmap = [fmap]

        time_varying = nc.is_var_dim(fmap[0], dmap['time'])
        f_params = dict(time_varying= time_varying,
                        is3D=False,
                        is_vector= len(fmap) > 1,
                        )
        return f_params
    def read_file_var_as_4D_nodal_values(self,nc, grid, var_name, file_index=None):
        # reformat file variable into 4D time,node,depth, components  form
        si =self.shared_info
        dm = self.params['dimension_map']

        data, data_dims = self.read_field_var(nc, var_name, sel=file_index)

        # add dummy time dim if none
        if  dm['time'] not in data_dims: data = data[np.newaxis,...]
        if  dm['depth'] in data_dims: data = data[:, 0,...] # remove dummy depth dim

        # data is now shaped as (time, row, col, depth)
        # now flatten (time,rows, col, depth)  to  (time,nodes, depth)
        s = data.shape
        data = data.reshape( (s[0],s[1]*s[2])) # this should match flatten in "C" order

        # add dummy depth, vector components axis,
        data = data[:, :, np.newaxis, np.newaxis]

        return data

    def read_dry_cell_data(self, nc, grid,fields,  file_index,is_dry_cell_buffer,buffer_index):
        is_dry_cell_buffer[buffer_index,:] = np.zeros((file_index.size, grid['triangles'].shape[0]),dtype=bool)
        pass

    def read_field_var(self, nc, var_file_name, sel=None):
        # read sel time steps of field variable
        pass
        if nc.is_var(var_file_name):
            # 2D variable in out2d.nc
            return super().read_field_var(nc, var_file_name, sel=sel)
        else:
            # read water depth  variable in another file
            nc_var= NetCDFhandler(self.params['water_depth_file'])
            data = nc_var.read_a_variable(var_file_name, sel=sel)
            data_dims = nc_var.all_var_dims(var_file_name)
            nc_var.close()
            return data, data_dims