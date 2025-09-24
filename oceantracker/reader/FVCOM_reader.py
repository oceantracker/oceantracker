from oceantracker.reader._base_unstructured_reader import _BaseUnstructuredReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util import time_util
from oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from datetime import datetime
from oceantracker.reader.util import hydromodel_grid_transforms

from oceantracker.reader.util import reader_util
from oceantracker.shared_info import shared_info as si

#todo add required variables and dimensions lists to sensure
#todo friction velocity from bottom stress magnitude, tauc if present
#todo use A_H and A_V fields in random walk
#todo implement depth average mode using depth average variables in the file

class FVCOMreader(_BaseUnstructuredReader):
    # loads a standard SCHISM netcdf output file with nodal data
    # variable names can be tweaked via maps in shared_params, if non-standard names used
    development = True
    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults
        self.add_default_params(
                dimension_map=dict(
                        node=PVC('node', str, doc_str='Dim oNumber of nodes in triangular grid ie unique triangle vertex node numbers'),
                        all_z_dims=PLC( ['siglay', 'siglev'], str, doc_str='All z dims, used to identify  3D variables'),
                        z=PVC('siglev', str, doc_str='name of dimensions for z layer boundaries '),
                        ),
                field_variable_map= dict(
                        water_velocity= PLC(['u','v','ww'], str, fixed_len=3),
                        water_depth = PVC('h', str,doc_str='maps standard internal field name to file variable name'),
                        tide =PVC('zeta', str,doc_str='maps standard internal field name to file variable name'),
                        water_temperature = PVC('temp', str, doc_str='maps standard internal field name to file variable name'),
                        salinity = PVC('salinity', str, doc_str='maps standard internal field name to file variable name'),
                        wind_velocity = PLC(['uwind_speed', 'vwind_speed'], str, doc_str='maps standard internal field name to file variable name'),
                        bottom_stress = PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                        A_Z_profile = PVC(None, str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                        ),
                grid_variable_map= dict(
                        time=PVC('time', str, doc_str='Name of time variable in hindcast'),
                        x = PVC('lon', str, doc_str='x location of nodes'),
                        y = PVC('lat', str, doc_str='y location of nodes'),
                        z_interface=PVC('zcor', str),
                        triangles =PVC('SCHISM_hgrid_face_nodes', str),
                        bottom_interface_index =PVC('node_bottom_index', str),
                        is_dry_cell = PVC('wetdry_elem', str, doc_str='Time variable flag of when cell is dry, 1= is dry cell')
                        ),
                variable_signature = PLC(['u', 'v', 'zeta'], str,
                                      doc_str='Variable names used to test if file is this format'),
                )

    def add_hindcast_info(self):
        params = self.params
        dm = params['dimension_map']
        fvm = params['field_variable_map']
        gm = params['grid_variable_map']
        info = self.info
        dims = info['dims']

        if info['is3D']:
            # sort out z dim and vertical grid size
            info['z_dim'] = dm['z']
            info['num_z_interfaces'] = info['dims'][info['z_dim']]
            info['all_z_dims'] = dm['all_z_dims']
            info['vert_grid_type'] = si.vertical_grid_types.Slayer

        info['node_dim'] = params['dimension_map']['node']
        info['num_nodes'] = info['dims'][info['node_dim']]


    def build_vertical_grid(self):

        # time invarient z fractions at layer needed for super.build_vertical_grid
        grid = self.grid
        ds = self.dataset
        z = ds.read_variable('siglev').data.astype(np.float32).T
        zlayer = ds.read_variable('siglay').data.astype(np.float32).T
        grid['z_interface_fractions']  = 1. + np.flip(z, axis=1)  # layer boundary fractions
        grid['z_layer_fixed_fractions'] = 1. + np.flip(zlayer, axis=1)  # layer center fractions

        # make distance weighting matrix for triangle center values at nodal points
        grid['cell_center_weights'] = hydromodel_grid_transforms.calculate_inv_dist_weights_at_node_locations(
            grid['x'], grid['x_center'], grid['node_to_tri_map'], grid['tri_per_node'])
        grid['vertical_grid_type'] = 'S-sigma'

        # now do setup
        super().build_vertical_grid()


    def set_up_uniform_sigma(self, grid):
        # for use in Slayer vertical grids
        # get profile with the smallest bottom layer  tickness as basis for first sigma layer
        node_thinest_bot_layer = hydromodel_grid_transforms.find_node_with_smallest_bot_layer(grid['z_interface_fractions'],
                                                                                              grid['bottom_interface_index'])

        # use layer fractions from this node to give layer fractions everywhere
        # in LSC grid this requires stretching a bit to give same number max numb. of depth cells
        nz_bottom = grid['bottom_interface_index'][node_thinest_bot_layer]

        # stretch sigma out to same number of depth cells,
        # needed for LSC grid if node_min profile is not full number of cells
        zf_model = grid['z_interface_fractions'][node_thinest_bot_layer, nz_bottom:]
        nz = grid['z_interface_fractions'].shape[1]
        nz_fractions = nz - nz_bottom
        grid['sigma_interface'] = np.interp(np.arange(nz) / (nz-1), np.arange(nz_fractions) / (nz_fractions-1), zf_model)



    def read_horizontal_grid_coords(self, grid):
        # reader nodal locations
        ds = self.dataset
        gm = self.params['grid_variable_map']

        x = ds.read_variable(gm['x']).data
        y = ds.read_variable(gm['y']).data
        grid['x']  = np.stack((x, y), axis=1).astype(np.float64)

        grid['x_center'] = np.stack((ds.read_variable('lonc').data,
                                     ds.read_variable('latc').data), axis=1).astype(np.float64)


    def read_triangles(self, grid):
        ds = self.dataset
        grid['triangles'] = ds.read_variable('nv').data.T.astype(np.int32) - 1 # convert to zero base index
        grid['quad_cells_to_split'] =  np.full((0,),0, np.int32)


    def read_z_interface(self, nc,grid,fields, file_index, z_interface_buffer, buffer_index):
        # calcuate z_interface from depth fractions, tide and water depth
        # FVCOM has fraction of depth < from free surface, with top value first in z dim of arrAy
        # todo check first value is the bottom or free surface+-, look like free surface??

        # time varying z_interface from fixed water depth fractions and total water depth at nodes
        water_depth = fields['water_depth'].data[:, :, :, 0]
        tide = fields['tide'].data[:, :, :, 0]
        z_interface_buffer[buffer_index, ...] = grid['z_interface_fractions'][np.newaxis, ...]*(tide[buffer_index, :, :]+water_depth) - water_depth

    def read_dry_cell_data(self, nt_index, buffer_index):
        ds = self.dataset
        grid = self.grid

        if 'wet_cells' in ds.info['variables']:
            wet_cells= ds.read_variable('wet_cells', nt=nt_index).data
            grid['is_dry_cell_buffer'][buffer_index,:] = wet_cells != 1
        else:
            # get dry cells from water depth and tide
            fields = self.fields
            reader_util.set_dry_cell_flag_from_tide(grid['triangles'], fields['tide'].data, fields['water_depth'].data,
                                                    si.settings.minimum_total_water_depth, grid['is_dry_cell_buffer'],
                                                    buffer_index)


    def read_file_var_as_4D_nodal_values(self, var_name, var_info, nt=None):
        # read variable into 4D ( time, node, depth, comp) format
        # assumes same variable order in the file
        grid = self.grid
        ds = self.dataset
        data = ds.read_variable(var_name, nt=nt).data

        # first reorder dim to ( time, node, depth, comp), ie swap z and hori
        if var_info['is3D']:
            # flip node and z dims
            data = np.transpose(data, [0, 2, 1] if var_info['time_varying'] else [2, 1] )

        # add time dim if needed
        if not var_info['time_varying']:
            data  = data[np.newaxis, ...]

        # some variables at nodes, some at cell center ( eg u,v,w)
        if 'nele' in var_info['dims']:
            # data is at cell center/element/triangle  move to nodes
            data = hydromodel_grid_transforms.get_nodal_values_from_weighted_cell_values(data, grid['node_to_tri_map'], grid['tri_per_node'], grid['cell_center_weights'])

        # see if z or z water level  in variable and swap z and node dim
        if 'siglay' in var_info['dims']:
            #3D mid layer values
            # convert mid-layer values to values at layer boundaries, ie z_interfaces
            data = hydromodel_grid_transforms.convert_layer_field_to_levels_from_interface_fractions_at_each_node(
                                data, grid['z_layer_fixed_fractions'], grid['z_interface_fractions'])
        elif not 'siglev' in var_info['dims']:
            # 2D field
            data =  data[..., np.newaxis]

        # add dummy vector component to make 4D
        data = data[:, :, :, np.newaxis]

        return data


