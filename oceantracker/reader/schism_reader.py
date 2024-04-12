from oceantracker.reader._base_reader import _BaseReader
from oceantracker.reader.util import reader_util
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
from oceantracker.util import  time_util
from datetime import  datetime, timedelta
import numpy as np
from oceantracker.util.triangle_utilities import split_quad_cells
import oceantracker.reader.util.hydromodel_grid_transforms as  hydromodel_grid_transforms
from copy import deepcopy
from oceantracker.definitions import node_types

from oceantracker.shared_info import SharedInfo as si

class SCHISMreaderNCDF(_BaseReader):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({
             'grid_variable_map': {'time': PVC('time', str),
                               'x': PLC(['SCHISM_hgrid_node_x', 'SCHISM_hgrid_node_y'], str, fixed_len=2),
                               'zlevel': PVC('zcor', str),
                               'triangles': PVC('SCHISM_hgrid_face_nodes', str),
                               'bottom_cell_index': PVC('node_bottom_index', str),
                               'is_dry_cell': PVC('wetdry_elem', str, doc_str='Time variable flag of when cell is dry, 1= is dry cell')},
            'field_variable_map': {'water_velocity': PLC(['hvel', 'vertical_velocity'], str, fixed_len=2),
                                'tide': PVC('elev', str,doc_str='maps standard internal field name to file variable name'),
                                'water_depth': PVC('depth', str,doc_str='maps standard internal field name to file variable name'),
                                'water_temperature': PVC('temp', str,doc_str='maps standard internal field name to file variable name'),
                                'salinity': PVC('salt', str,doc_str='maps standard internal field name to file variable name'),
                                'wind_stress': PVC('wind_stress', str,doc_str='maps standard internal field name to file variable name'),
                                'bottom_stress': PVC('bottom_stress', str,doc_str='maps standard internal field name to file variable name'),
                                'A_Z_profile':  PVC('diffusivity', str,doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                'water_velocity_depth_averaged': PLC(['dahv'], str,  fixed_len=2,
                                                                     doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
            'hgrid_file_name': PVC(None, str),
             })
        pass

    def is_file_format(self,file_name):
        # check if file matches this file format
        nc = self._open_file(file_name)
        is_file_type= nc.is_var('SCHISM_hgrid_node_x') and (nc.is_var('hvel') or nc.is_var('dahv'))
        nc.close()
        return is_file_type

    # Below are basic variable read methods for any new reader
    #---------------------------------------------------------
    def read_horizontal_grid_coords(self, nc, grid):

        x_var ='SCHISM_hgrid_node_x'
        x =  nc.read_a_variable(x_var)
        y = nc.read_a_variable('SCHISM_hgrid_node_y')
        grid['x'] = np.stack((x,y),axis=1).astype(np.float64)

        # test if lat long
        if nc.is_var_attr(x_var,'units') and 'degree' in nc.var_attr(x_var,'units').lower():
            grid['hydro_model_cords_in_lat_long'] = True

        elif self.detect_lonlat_grid(grid['x']):
            # try auto detection
            grid['hydro_model_cords_in_lat_long'] = True
        else:
            grid['hydro_model_cords_in_lat_long'] = self.params['hydro_model_cords_in_lat_long']

        if grid['hydro_model_cords_in_lat_long']:
            si._setup_lon_lat_to_meters_grid_tranforms(grid['x'])
            grid['lon_lat'] = grid['x'].copy()
            grid['x'] = si._transform_lon_lat_to_meters( grid['lon_lat'])

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


    def number_hindcast_zlayers(self, nc): return nc.dim_size('nSCHISM_vgrid_layers')

    def read_zlevel_as_float32(self, nc, grid,fields, file_index, zlevel_buffer, buffer_index):
        zlevel_buffer[buffer_index,...] = nc.read_a_variable(self.params['grid_variable_map']['zlevel'], sel=file_index).astype(np.float32)


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

        fmap = self.params['field_variable_map']

        f_params = dict(time_varying = nc.is_var_dim(fmap[name][0], 'time'),
                        is3D = nc.is_var_dim(fmap[name][0], 'nSCHISM_vgrid_layers'),
                        is_vector = nc.is_var_dim(fmap[name][0], 'two') or len(fmap[name] ) > 1
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
            grid['bottom_cell_index'] = np.zeros((grid['x'].shape[0],),dtype=np.int32)
            grid['bottom_cell_index'] = 'Slayer'
        self.info['vertical_grid_type'] = vertical_grid_type
        return grid


    def read_file_var_as_4D_nodal_values(self, nc, grid, var_name, file_index=None):
        #todo add name to params!!
        # read variable into 4D ( time, node, depth, comp) format
        # assumes same variable order in the file
        data, data_dims = self.read_field_var(nc , var_name, sel=file_index)
        # get 4d size
        s = [data.shape[0] if 'time' in data_dims else 1,
             nc.dim_size('nSCHISM_hgrid_node'),
             nc.dim_size('nSCHISM_vgrid_layers') if 'nSCHISM_vgrid_layers' in data_dims else 1,
             2  if  'two' in data_dims else 1
             ]
        return data.reshape(s)

    def read_dry_cell_data(self,nc,grid,fields, file_index,is_dry_cell_buffer, buffer_index):
        # calculate dry cell flags, if any cell node is then dry is_dry_cell_buffer=1

        data_added_to_buffer = nc.read_a_variable(self.params['grid_variable_map']['is_dry_cell'], file_index)
        is_dry_cell_buffer[buffer_index, :] = reader_util.append_split_cell_data(grid, data_added_to_buffer, axis=1)


    def set_up_uniform_sigma(self, nc, grid):
        # read z fractions into grid , for later use in vertical regridding, and set up the uniform sigma to be used

        # read first zlevel time step
        zlevel, zlevel_dims =self.read_field_var(nc, self.params['grid_variable_map']['zlevel'], sel=0)

        # use node with thinest top/bot layers as template for all sigma levels
        grid['zlevel_fractions'] = hydromodel_grid_transforms.convert_zlevels_to_fractions(zlevel, grid['bottom_cell_index'], si.settings.z0)

        # get profile with smallest bottom layer  tickness as basis for first sigma layer
        node_thinest_bot_layer = hydromodel_grid_transforms.find_node_with_smallest_bot_layer(grid['zlevel_fractions'],grid['bottom_cell_index'])
        # use layer fractions from this node to give layer fractions everywhere
        # in LSC grid this requires stretching a bit to give same number max numb. of depth cells
        nz_bottom = grid['bottom_cell_index'][node_thinest_bot_layer]

        # stretch sigma out to same number of depth cells,
        # needed for LSC grid if node_min profile is not full number of cells
        zf_model = grid['zlevel_fractions'][node_thinest_bot_layer, nz_bottom:]
        nz = grid['zlevel_fractions'].shape[1]
        nz_fractions = nz - nz_bottom
        grid['sigma'] = np.interp(np.arange(nz) / nz, np.arange(nz_fractions) / nz_fractions, zf_model)

        if False:
            # debug plots sigma
            from matplotlib import pyplot as plt
            sel = np.arange(0, zlevel.shape[0], 100)
            water_depth,junk = self.read_field_var(nc, self.params['field_variable_map']['water_depth'])
            sel=sel[water_depth[sel]> 10]
            index_frac = (np.arange(zlevel.shape[1])[np.newaxis,:] - grid['bottom_cell_index'][sel,np.newaxis]) / (zlevel.shape[1] - grid['bottom_cell_index'][sel,np.newaxis])
            zlevel[zlevel < -1.0e4] = np.nan

            #plt.plot(index_frac.T,zlevel[sel,:].T,'.')
            #plt.show(block=True)
            plt.plot(index_frac.T, grid['zlevel_fractions'][sel, :].T, lw=0.1)
            plt.plot(index_frac.T,grid['zlevel_fractions'][sel, :].T, '.')

            plt.show(block=True)

            pass

        return grid

    def preprocess_field_variable(self, nc,name,grid, data):
        if name =='water_velocity' and data.shape[2] > 1:
            # for 3D schism velocity partial fix for  non-zero hvel at nodes where cells in LSC grid span a change in bottom_cell_index
            data = reader_util.patch_bottom_velocity_to_make_it_zero(data, grid['bottom_cell_index'])
        return data

    def read_open_boundary_data_as_boolean(self, grid):
        # make boolen of whether node is an open boundary node
        # read schisim  hgrid file for open boundary data

        if self.params['hgrid_file_name'] is None:    return  np.full((grid['x'].shape[0],), False)

        hgrid = read_hgrid_file(self.params['hgrid_file_name'])

        is_open_boundary_node = hgrid['node_type'] == 3

        return is_open_boundary_node

def decompose_lines(lines, dtype=np.float64):
    cols= len(lines[0].split())
    out= np.full((len(lines),cols),0,dtype=dtype)
    for n , l in enumerate(lines):
        #print(n,l)
        vals = [float(x) for x in l.split()]
        if len(vals) > out.shape[1]:
            # add new cols if needed
            out = np.stack((out,np.full((len(lines),len(vals) -out.shape[1]),0,dtype=dtype)), axis=1)

        out[n,:] = np.asarray(vals)

    return  out

def read_hgrid_file(file_name):

    d={}
    with open(file_name) as f:
        lines = f.readlines()
    d['file_name'] = lines[0]
    d['n_tri'],  d['n_nodes']= [ int(x) for x in lines[1].split()]

    # node coords
    l0 = 3-1
    vals = decompose_lines(lines[l0: l0 + d['n_nodes']])
    d['x'] = vals[:,1:3]
    l0 = l0+d['n_nodes']

    # triangulation
    vals = decompose_lines(lines[l0: l0 + d['n_tri']],dtype=np.int32)
    d['triangles'] = vals[:, 2:] - 1
    l0 = l0 + d['n_tri']

    # work out node types
    d['node_type'] = np.full((d['n_nodes'],), 0, dtype=np.int32)

    # open boundaries
    d['n_open_boundaries'] = int(lines[l0].split()[0])

    # load segments of open boundaries

    if  d['n_open_boundaries'] > 0:
        l0 += 2
        d['open_boundary_node_segments']=[]
        for nb in range(d['n_open_boundaries']):
            n_nodes =  int(lines[l0].split()[0])
            nodes = np.squeeze(decompose_lines(lines[l0+1: l0 + 1 + n_nodes],dtype=np.int32)) - 1
            d['open_boundary_node_segments'].append(nodes)
            d['node_type'][nodes] = 3
            l0 = l0 + nodes.size + 1

    # land boundaries
    d['n_land_boundaries'] = int(lines[l0].split()[0])

    # load segments of land boundaries
    if d['n_land_boundaries'] > 0:
        l0 += 2
        d['land_boundary_node_segments'] = []
        for nb in range(d['n_open_boundaries']):
            n_nodes = int(lines[l0].split()[0])
            nodes = np.squeeze(decompose_lines(lines[l0 + 1: l0 + 1 + n_nodes], dtype=np.int32)) - 1
            d['land_boundary_node_segments'].append(nodes)
            d['node_type'][nodes] = 1
            l0 = l0 + nodes.size + 1

    return d