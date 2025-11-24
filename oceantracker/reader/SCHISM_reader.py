from oceantracker.reader._base_unstructured_reader import _BaseUnstructuredReader
from os import path

from oceantracker.util import time_util
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterTimeChecker as PTC, ParameterListChecker as PLC
import numpy as np
from oceantracker.shared_info import shared_info as si
from oceantracker.reader.util import reader_util
from oceantracker.reader.util import hydromodel_grid_transforms
class SCHISMreader(_BaseUnstructuredReader):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({
            'dimension_map': dict(
                        node=PVC('nSCHISM_hgrid_node', str, doc_str='name of nodes dimension in files'),
                        cell=PVC('nSCHISM_hgrid_face', str, doc_str='name of cell dimension in files'),
                        z=PVC('nSCHISM_vgrid_layers', str, doc_str='name of dimensions for z layer boundaries '),
                        all_z_dims=PLC(['nSCHISM_vgrid_layers'], str, doc_str='All z dims, used to identify  3D variables'),
                        vector2D=PVC('two', str, doc_str='name of dimension names for 2D vectors'),
                        vector3D=PVC(None, str),
                                ),
             'grid_variable_map': dict(
                        time=PVC('time', str, doc_str='Name of time variable in hindcast'),
                        x = PVC('SCHISM_hgrid_node_x', str, doc_str='x location of nodes'),
                        y = PVC('SCHISM_hgrid_node_y', str, doc_str='y location of nodes'),
                        z_interface=PVC('zcor', str),
                        triangles =PVC('SCHISM_hgrid_face_nodes', str),
                        bottom_interface_index =PVC('node_bottom_index', str),
                        is_dry_cell = PVC('wetdry_elem', str, doc_str='Time variable flag of when cell is dry, 1= is dry cell')
                        ),
            'field_variable_map': {'water_velocity': PLC(['hvel', 'vertical_velocity'], str),
                                'tide': PVC('elev', str,doc_str='maps standard internal field name to file variable name'),
                                'water_depth': PVC('depth', str, doc_str='maps standard internal field name to file variable name'),
                                'water_temperature': PVC('temp', str,doc_str='maps standard internal field name to file variable name'),
                                'salinity': PVC('salt', str,doc_str='maps standard internal field name to file variable name'),
                                'wind_stress': PLC(['wind_stress'], str,doc_str='maps standard internal field name to file variable name'),
                                'bottom_stress': PLC(['bottom_stress'], str,doc_str='maps standard internal field name to file variable name'),
                                'A_Z_profile':  PVC('diffusivity', str,doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                'water_velocity_depth_averaged': PLC(['dahv'], str,
                                                doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
            'one_based_indices': PVC(True, bool, doc_str='Schism has indices starting at 1 not zero'),
            'variable_signature': PLC(['elev','depth','wetdry_elem'], str, doc_str='Variable names used to test if file is this format'),
            'hgrid_file_name': PVC(None, str),
             })

        pass

    def decode_time(self, time):
        try:
            # try units approach otherwise use old base_date method
            return super().decode_time(time)
        except  Exception as e:
            # older based date schsim version, ignore time zone
            s = time.attrs['base_date'].split()
            d0 = np.datetime64(f'{int(s[0])}-{int(s[1]):02d}-{int(s[2]):02d}')
            d0 = d0.astype('datetime64[s]').astype(np.float64)
            d0 = d0 + float(s[3])*3600
            t = time.data + d0
            return t

    def initial_setup(self):
        super().initial_setup()
        # use schism min water depth if in file
        if 'minimum_depth' in self.info['variables']:
            si.settings.minimum_total_water_depth = max( float(self.dataset.read_variable('minimum_depth')), .01)
    def add_hindcast_info(self):
        params = self.params
        info = self. info
        ds_info =  self.dataset.info
        dm = params['dimension_map']
        fvm= params['field_variable_map']
        gm = params['grid_variable_map']

        if info['is3D']:
            # sort out z dim and vertical grid size
            info['z_dim'] = dm['z']
            info['num_z_interfaces'] = info['dims'][info['z_dim']]
            info['all_z_dims'] = dm['all_z_dims']
            info['vert_grid_type'] = si.vertical_grid_types.LSC if gm['bottom_interface_index'] in info['variables'] \
                                                                        else si.vertical_grid_types.Slayer

        info['node_dim'] = params['dimension_map']['node']
        info['num_nodes'] = info['dims'][info['node_dim']]


    def read_z_interface(self, nt):
        data = self.dataset.read_variable(self.params['grid_variable_map']['z_interface'], nt = nt)
        return data


    def read_triangles(self, grid):
        # read nodes in triangles (N by 3) or mix of triangles and quad cells as  (N by 4)
        ds = self.dataset
        gm = self.params['grid_variable_map']

        tri = ds.read_variable(gm['triangles']).data
        sel = np.isnan(tri)
        tri[sel] = 0
        tri = tri.astype(np.int32)
        tri -= 1

        grid['triangles'] = tri

    def read_bottom_interface_index(self, grid):
        # time invariant bottom cell index, which varies across grid in LSC vertical grid
        info = self.info
        var_name = self.params['grid_variable_map']['bottom_interface_index']

        if var_name in info['variables']:
            bottom_interface_index=  self.dataset.read_variable(var_name).data - 1
        else:
            # S  grid bottom cell index = zero
            bottom_interface_index = np.zeros((self.info['num_nodes'],), dtype=np.int32)

        return bottom_interface_index

    def read_dry_cell_data(self,nt_index, buffer_index):
        # calculate dry cell flags, if any cell node is then dry is_dry_cell_buffer=1
        grid= self.grid
        is_dry_cell_buffer = grid['is_dry_cell_buffer']
        data_added_to_buffer = self.dataset.read_variable(self.params['grid_variable_map']['is_dry_cell'], nt_index).data
        is_dry_cell_buffer[buffer_index, :] = reader_util.append_split_cell_data(grid, data_added_to_buffer, axis=1)


    def read_open_boundary_data_as_boolean(self, grid):
        # make boolen of whether node is an open boundary node
        # read schisim  hgrid file for open boundary data

        if self.params['hgrid_file_name'] is None:
            return  np.full((grid['x'].shape[0],), False)

        hgrid = read_hgrid_file(self.params['hgrid_file_name'])

        is_open_boundary_node = hgrid['node_type'] == 3

        return is_open_boundary_node

    def set_up_uniform_sigma(self, grid):
        # read z fractions into grid , for later use in vertical regridding, and set up the uniform sigma to be used
        # for use in Slayer ond LSC grids

        ds = self.dataset
        gm = self.params['grid_variable_map']

        # read first z_interface time step
        z_interface =ds.read_variable(gm['z_interface'],[0]).data[0,:,:]

        # use node with thinest top/bot layers as template for all sigma levels
        grid['z_interface_fractions'] = hydromodel_grid_transforms.convert_z_interfaces_to_fractions(z_interface, grid['bottom_interface_index'], si.settings.minimum_total_water_depth)

        # get profile with the smallest bottom layer  tickness as basis for first sigma layer
        node_thinest_bot_layer = hydromodel_grid_transforms.find_node_with_smallest_bot_layer(grid['z_interface_fractions'],grid['bottom_interface_index'])

        # use layer fractions from this node to give layer fractions everywhere
        # in LSC grid this requires stretching a bit to give same number max numb. of depth cells
        nz_bottom = grid['bottom_interface_index'][node_thinest_bot_layer]

        # stretch sigma out to same number of depth cells,
        # needed for LSC grid if node_min profile is not full number of cells
        zf_model = grid['z_interface_fractions'][node_thinest_bot_layer, nz_bottom:]
        nz = grid['z_interface_fractions'].shape[1]
        nz_fractions = nz - nz_bottom
        grid['sigma_interface'] = np.interp(np.arange(nz) / (nz-1), np.arange(nz_fractions) / (nz_fractions-1), zf_model)

        if False:
            # debug plots sigma
            from matplotlib import pyplot as plt
            sel = np.arange(0, z_interface.shape[0], 100)
            water_depth,junk = self.read_field_var(nc, self.params['field_variable_map']['water_depth'])
            sel=sel[water_depth[sel]> 10]
            index_frac = (np.arange(z_interface.shape[1])[np.newaxis,:] - grid['bottom_interface_index'][sel,np.newaxis]) / (z_interface.shape[1] - grid['bottom_interface_index'][sel,np.newaxis])
            z_interface[z_interface < -1.0e4] = np.nan

            #plt.plot(index_frac.T,z_interface[sel,:].T,'.')
            #plt.show(block=True)
            plt.plot(index_frac.T, grid['z_interface_fractions'][sel, :].T, lw=0.1)
            plt.plot(index_frac.T,grid['z_interface_fractions'][sel, :].T, '.')

            plt.show(block=True)

            pass

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

    if not path.isfile(file_name):
        si.msg_logger.msg(f'Cannot find given schsim hgrid file "{file_name}"',
                         hint ='check path', fatal_error=True )
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


