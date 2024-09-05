from oceantracker.reader._base_unstructured_reader import _BaseUnstructuredReader


from copy import deepcopy
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterTimeChecker as PTC, ParameterListChecker as PLC
import numpy as np
from oceantracker.shared_info import shared_info as si
from oceantracker.reader.util import reader_util

class SCHISMreaderNCDF(_BaseUnstructuredReader):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({
            'dimension_map': dict(
                        node=PVC('nSCHISM_hgrid_node', str, doc_str='name of nodes dimension in files'),
                        z=PVC('nSCHISM_vgrid_layers', str, doc_str='name of dimensions for z layer boundaries '),
                        all_z_dims=PLC(['nSCHISM_vgrid_layers'], str, doc_str='All z dims used to identify  3D variables'),
                        vector2D=PVC('two', str, doc_str='name of dimension names for 2D vectors'),
                        vector3D=PVC(None, str),
                                ),
             'grid_variable_map': dict(
                        time=PVC('time', str, doc_str='Name of time variable in hindcast'),
                        x = PVC('SCHISM_hgrid_node_x', str, doc_str='x location of nodes'),
                        y = PVC('SCHISM_hgrid_node_y', str, doc_str='y location of nodes'),
                        zlevel=PVC('zcor', str),
                        triangles =PVC('SCHISM_hgrid_face_nodes', str),
                        bottom_cell_index =PVC('node_bottom_index', str),
                        is_dry_cell = PVC('wetdry_elem', str, doc_str='Time variable flag of when cell is dry, 1= is dry cell')
                        ),
            'field_variable_map': {'water_velocity': PLC(['hvel', 'vertical_velocity'], str),
                                'tide': PVC('elev', str,doc_str='maps standard internal field name to file variable name'),
                                'water_depth': PVC('depth', str, doc_str='maps standard internal field name to file variable name'),
                                'water_temperature': PVC('temp', str,doc_str='maps standard internal field name to file variable name'),
                                'salinity': PVC('salt', str,doc_str='maps standard internal field name to file variable name'),
                                'wind_stress': PVC('wind_stress', str,doc_str='maps standard internal field name to file variable name'),
                                'bottom_stress': PVC('bottom_stress', str,doc_str='maps standard internal field name to file variable name'),
                                'A_Z_profile':  PVC('diffusivity', str,doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                'water_velocity_depth_averaged': PLC(['dahv'], str,
                                                doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
            'one_based_indices': PVC(True, bool, doc_str='Schism has indices starting at 1 not zero'),
            'variable_signature': PLC(['SCHISM_hgrid_node_x','dahv'], str, doc_str='Variable names used to test if file is this format'),
            'hgrid_file_name': PVC(None, str),
             })

        pass

    def get_hindcast_info(self, catalog):

        dm = self.params['dimension_map']
        fvm= self.params['field_variable_map']

        hi = dict(is3D=  fvm['water_velocity'][0]  in catalog['variables'])

        if hi['is3D']:
            hi['z_dim'] = dm['z']
            hi['num_z_levels'] = catalog['info']['dims'][hi['z_dim']]
            hi['all_z_dims'] = dm['all_z_dims']
            # Only LSC hasbottom_cell_index
            hi['vert_grid_type'] = si.vertical_grid_types.LSC if 'bottom_cell_index' in catalog['variables'] \
                                                                        else si.vertical_grid_types.Slayer
        else:
            hi['z_dim'] = None
            hi['num_z_levels'] = 0
            hi['num_z_levels'] = 0
            hi['all_z_dims'] =  []
            hi['vert_grid_type'] = None

        # get num nodes in each field
        hi['node_dim'] = self.params['dimension_map']['node']
        hi['num_nodes'] =  catalog['info']['dims'][hi['node_dim']]
        return hi

    def read_zlevel(self, nt):
        return self.dataset.read_variable(self.params['grid_variable_map']['zlevel'], nt = nt)


    def read_bottom_cell_index(self, grid):
        # time invariant bottom cell index, which varies across grid in LSC vertical grid
        ds = self.dataset
        gm = self.grid_variable_map
        var_name = gm['bottom_cell_index']
        if var_name in ds.variables:
            bottom_cell_index= ds.read_variable(var_name).data - 1
        else:
            # S  grid bottom cell index = zero
            bottom_cell_index = np.zeros((grid['x'].shape[0],),dtype=np.int32)
        return bottom_cell_index

    def read_dry_cell_data(self,nt_index, buffer_index):
        # calculate dry cell flags, if any cell node is then dry is_dry_cell_buffer=1
        grid= self.grid
        is_dry_cell_buffer = grid['is_dry_cell_buffer']
        data_added_to_buffer = self.dataset.read_variable(self.params['grid_variable_map']['is_dry_cell'], nt_index).data
        is_dry_cell_buffer[buffer_index, :] = reader_util.append_split_cell_data(grid, data_added_to_buffer, axis=1)



    def preprocess_field_variable(self, name,grid, data):
        if name =='water_velocity' and data.shape[2] > 1:
            # for 3D schism velocity partial fix for  non-zero hvel at nodes where cells in LSC grid span a change in bottom_cell_index
            data = reader_util.patch_bottom_velocity_to_make_it_zero(data, grid['bottom_cell_index'])
        return data

    def read_open_boundary_data_as_boolean(self, grid):
        # make boolen of whether node is an open boundary node
        # read schisim  hgrid file for open boundary data

        if self.params['hgrid_file_name'] is None:
            return  np.full((grid['x'].shape[0],), False)

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