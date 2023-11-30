from oceantracker.reader._base_reader import _BaseReader
from oceantracker.reader.util import reader_util
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
from oceantracker.util import  time_util
from datetime import  datetime, timedelta
import numpy as np
from oceantracker.util.triangle_utilities_code import split_quad_cells
import oceantracker.reader.util.hydromodel_grid_transforms as  hydromodel_grid_transforms


class SCHISMSreaderNCDF(_BaseReader):

    def __init__(self, shared_memory_info=None):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({
             'grid_variable_map': {'time': PVC('time', str),
                               'x': PLC(['SCHISM_hgrid_node_x', 'SCHISM_hgrid_node_y'], [str], fixed_len=2),
                               'zlevel': PVC('zcor', str),
                               'triangles': PVC('SCHISM_hgrid_face_nodes', str),
                               'bottom_cell_index': PVC('node_bottom_index', str),
                               'is_dry_cell': PVC('wetdry_elem', np.int8, doc_str='Time variable flag of when cell is dry, 1= is dry cell')},
            'field_variable_map': {'water_velocity': PLC(['hvel', 'vertical_velocity'], [str], fixed_len=2),
                                'tide': PVC('elev', str,doc_str='maps standard internal field name to file variable name'),
                                'water_depth': PVC('depth', str,doc_str='maps standard internal field name to file variable name'),
                                'water_temperature': PVC('temp', str,doc_str='maps standard internal field name to file variable name'),
                                'salinity': PVC('salt', str,doc_str='maps standard internal field name to file variable name'),
                                'wind_stress': PVC('wind_stress', str,doc_str='maps standard internal field name to file variable name'),
                                'bottom_stress': PVC('bottom_stress', str,doc_str='maps standard internal field name to file variable name'),
                                'A_Z_profile':  PVC('diffusivity', str,doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                'water_velocity_depth_averaged': PLC(['dahv'], [str],  fixed_len=2,
                                                                     doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
            'hgrid_file_name': PVC(None, str),
             })

    # Below are basic variable read methods for any new reader
    #---------------------------------------------------------
    def read_grid_coords(self, nc, grid):
        x_var ='SCHISM_hgrid_node_x'
        x =  nc.read_a_variable(x_var)
        y = nc.read_a_variable('SCHISM_hgrid_node_y')
        grid['x'] = np.stack((x,y),axis=1)

        # test if lat long
        if nc.is_var_attr(x_var,'units') and 'degree' in nc.var_attr(x_var,'units').lower():
            grid['is_lon_lat'] = True

        elif self.detect_lonlat_grid(grid['x']):
            # try auto detection
            grid['is_lon_lat'] = True
        else:
            grid['is_lon_lat'] = self.params['cords_in_lat_long']

        if grid['is_lon_lat']:
            grid['x'] = self.convert_lon_lat_to_meters_grid(grid['x'])


        return  grid

    def read_triangles_as_int32(self, nc, grid):
        grid['triangles'] = nc.read_a_variable('SCHISM_hgrid_face_nodes').astype(np.int32)
        grid['triangles'] -= 1 # make zero based

        # split quad cells aby adding new triangles
        # flag quad cells for splitting if index in 4th column
        if grid['triangles'].shape[1] == 4 :
            # split quad grids buy making new triangles
            grid['quad_cells_to_split'] = np.flatnonzero(grid['triangles'][:, 3] > 0).astype(np.int32)
            grid['triangles'] = split_quad_cells(grid['triangles'], grid['quad_cells_to_split'])
        else:
            grid['quad_cells_to_split'] = np.full((0,), 0, dtype=np.int32)

        return grid

    def is_hindcast3D(self, nc):
        return nc.is_var('hvel')

    def setup_water_velocity(self,nc,grid):
        # tweak to be depth avearged
        fm = self.params['field_variable_map']

        if nc.is_var(fm['water_velocity'][0]):
            # check if vertical vel variable in file
            if not nc.is_var(fm['water_velocity'][1]):
                fm['water_velocity'] = [fm['water_velocity'][0]]
        else:
            # is depth averaged schism run
            fm['water_velocity'] =fm['water_velocity_depth_averaged']


    def number_hindcast_zlayers(self, nc): return nc.dim_size('nSCHISM_vgrid_layers')

    def read_zlevel_as_float32(self, nc, file_index, zlevel_buffer, buffer_index):
        zlevel_buffer[buffer_index,...] = nc.read_a_variable('zcor', sel=file_index).astype(np.float32)

    def read_factional_zlevels(self, nc):
        z_fractiosns = nc.read_a_variable('zcor').astype(np.float32)

    def read_time_sec_since_1970(self, nc, file_index=None):
        var_name=self.params['grid_variable_map']['time']
        time = nc.read_a_variable(var_name, sel=file_index)

        s = nc.var_attr(var_name, 'base_date').split()
        base_date= [ int(x) for x in s[:3] ]
        d0= datetime(*tuple(base_date[:3]))
        d0 = d0 + timedelta(hours = float(s[3]))


        self.info['time_zone'] = float(s[4])/100.

        d0 = np.datetime64(d0).astype('datetime64[s]')
        sec = time_util.datetime64_to_seconds(d0)
        time += sec
        return time

    def get_field_params(self,nc, name, crumbs=''):
        # work out if feild is 3D ,etc
        fmap = self.params['field_variable_map'][name]
        if type(fmap) != list: fmap =[fmap]
        f_params = dict(time_varying = nc.is_var_dim(fmap[0], 'time'),
                        is3D = nc.is_var_dim(fmap[0],'nSCHISM_vgrid_layers'),
                        is_vector = nc.is_var_dim(fmap[0],'two') or len(fmap) > 1
                        )
        return f_params


    def read_bottom_cell_index_as_int32(self, nc, grid):
        # time invariant bottom cell index, which varies across grid in LSC vertical grid
        var_name =self.params['grid_variable_map']['bottom_cell_index']
        if nc.is_var(var_name):
            grid['bottom_cell_index'] = nc.read_a_variable(var_name).astype(np.int32)
            grid['bottom_cell_index'] -= 1 # make zero based index
            vertical_grid_type = 'LSC'
        else:
            # Slayer grid, bottom cell index = zero
            grid['bottom_cell_index'] = np.zeros((self.grid['x'].shape[0],),dtype=np.int32)
            grid['bottom_cell_index'] = 'Slayer'
        self.info['vertical_grid_type'] = vertical_grid_type
        return grid


    def read_file_var_as_4D_nodal_values(self, nc, var_name, file_index=None):
        # read variable into 4D ( time, node, depth, comp) format
        # assumes same variable order in the file
        data = nc.read_a_variable(var_name, sel=file_index)
        # get 4d size
        s = [data.shape[0] if nc.is_var_dim(var_name, 'time') else 1,
             nc.dim_size('nSCHISM_hgrid_node'),
             nc.dim_size('nSCHISM_vgrid_layers') if  nc.is_var_dim(var_name,'nSCHISM_vgrid_layers') else 1,
             2  if  nc.is_var_dim(var_name,'two') else 1
             ]
        return data.reshape(s)

    def read_dry_cell_data(self,nc,file_index,is_dry_cell_buffer, buffer_index):
        # calculate dry cell flags, if any cell node is then dry is_dry_cell_buffer=1
        grid = self.grid
        si = self.shared_info
        data_added_to_buffer = nc.read_a_variable(self.params['grid_variable_map']['is_dry_cell'], file_index)
        is_dry_cell_buffer[buffer_index, :] = reader_util.append_split_cell_data(grid, data_added_to_buffer, axis=1)


    def set_up_uniform_sigma(self, nc, grid):
        # read z fractions into grid , for later use in vertical regridding, and set up the uniform sigma to be used
        si= self.shared_info
        # read first zlevel time step
        zlevel = nc.read_a_variable('zcor', sel=0)

        # use node with thinest top/bot layers as template for all sigma levels

        grid['zlevel_fractions'] = hydromodel_grid_transforms.convert_zlevels_to_fractions(zlevel, grid['bottom_cell_index'], si.z0)
        node_min = hydromodel_grid_transforms.find_node_with_smallest_top_bot_layer(grid['zlevel_fractions'],grid['bottom_cell_index'])
        # use layer fractions from this node to give layer fractions everywhere
        # in LSC grid this requires stretching a bit to give same number max numb. of depth cells
        nz_bottom = grid['bottom_cell_index'][node_min]

        # stretch sigma out to same number of depth cells,
        # needed for LSC grid if node_min profile is not full number of cells
        zf_model = grid['zlevel_fractions'][node_min, nz_bottom:]
        nz = grid['zlevel_fractions'].shape[1]
        nz_fractions = nz - nz_bottom
        grid['sigma'] = np.interp(np.arange(nz) / nz, np.arange(nz_fractions) / nz_fractions, zf_model)

        return grid

    def preprocess_field_variable(self, nc,name, data):
        if name =='water_velocity' and data.shape[2] > 1:
            # for 3D schism velocity partial fix for  non-zero hvel at nodes where cells in LSC grid span a change in bottom_cell_index
            data = reader_util.patch_bottom_velocity_to_make_it_zero(data, self.grid['bottom_cell_index'])
        return data

    def read_open_boundary_data_as_boolean(self, grid):
        # make boolen of whether node is an open boundary node
        # read schisim  hgrid file for open boundary data
        is_open_boundary_node = np.full((grid['x'].shape[0],), False)

        if self.params['hgrid_file_name'] is None:
            return is_open_boundary_node

        with open(self.params['hgrid_file_name']) as f:
            lines = f.readlines()

        vals = lines[1].split()
        n_nodes = int(vals[0])
        n_tri = int(vals[1])

        n_line_open = n_nodes + n_tri + 3 - 1  # line with number of open boundries
        n_open = int(lines[n_line_open].split()[0])

        if n_open > 0:

            tri_open_bound_node_list = [[] for _ in range(grid['triangles'].shape[0])]
            nl = n_line_open + 1
            for n in range(n_open):
                # get block of open node numbers
                nl += 1  # move to line with number of nodes in this open boundary
                n_nodes = int(lines[nl].split()[0])
                nodes = []
                for n in range(n_nodes):
                    nl += 1
                    l = lines[nl].strip('\n')
                    nodes.append(int(l))
                ob_nodes = np.asarray(nodes, dtype=np.int32) - 1

                is_open_boundary_node[ob_nodes] = True  # get zero based node number

        return is_open_boundary_node


def read_hgrid_file(file_name):

    d={}
    with open(file_name) as f:
        lines = f.readlines()

    n_nodes, n_tri = [ int(x) for x in lines[1].split()]

    is_open_boundary_node = np.full((n_nodes,),False)

    n_line_open = n_nodes + n_tri + 3 - 1  # line with number of open boundaries
    n_open = int(lines[n_line_open].split()[0])

    if n_open > 0:

        nl = n_line_open + 1
        for n in range(n_open):
            # get block of open node numbers
            nl += 1  # move to line with number of nodes in this open boundary
            n_open_nodes = int(lines[nl].split()[0])
            open_nodes = []
            for n in range(n_open_nodes):
                nl += 1
                l = lines[nl].strip('\n')
                open_nodes.append(int(l))
            open_nodes = np.asarray(open_nodes, dtype=np.int32) - 1

            is_open_boundary_node[open_nodes] = True  # get zero based node number        with open(self.params['hgrid_file_name']) as f:

    return is_open_boundary_node