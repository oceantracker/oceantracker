import datetime

from oceantracker.reader._base_unstructured_reader import _BaseUnstructuredReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
from oceantracker.reader.util.hydromodel_grid_transforms import convert_regular_grid_to_triangles
from  oceantracker.util import time_util, numpy_util
import numpy as np
from oceantracker.util.triangle_utilities import split_quad_cells
from oceantracker.reader.util import  reader_util
from oceantracker.reader.util import  hydromodel_grid_transforms
from oceantracker.util.numba_util import  njitOT
from oceantracker.shared_info import shared_info as si

class DELF3DFMreader(_BaseUnstructuredReader):
    development =  True
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params(
            variable_signature=PLC(['mesh2d_waterdepth','mesh2d_face_nodes'], str, doc_str='Variable names used to test if file is this format'),
            one_based_indices = PVC(True, bool, doc_str='DELFT 3D has indices starting at 1 not zero'),
            load_fields = PLC(['water_depth'], str, doc_str='always load tide and water depth, for dry cells id 2D'),
            grid_variable_map= dict( time= PVC('time', str),
                        x = PVC('mesh2d_node_x', str, doc_str='x location of nodes'),
                        y = PVC('mesh2d_node_y', str, doc_str='y location of nodes'),
                        x_cell=PVC('mesh2d_face_x', str, doc_str='x location of cell centers'),
                        y_cell=PVC('mesh2d_face_y', str, doc_str='y location of cell center'),
                        z= PVC('mesh2d_interface_z', str,doc_str='Layer edges depths'),
                        z_layer=PVC('mesh2d_layer_z', str, doc_str='Mid layer z'),
                        triangles= PVC('mesh2d_face_nodes', str),
                        quad_face_nodes=PVC('mesh2d_face_nodes', str),
                        bottom_cell_index= PVC(None, str),
                        is_dry_cell=PVC('wetdry_elem', str, doc_str='Time variable flag of when cell is dry, 1= is dry cell')
                            ),
            dimension_map=dict(
                        z = PVC('mesh2d_nInterfaces', str, doc_str='z dim for interfaces'),
                        time=PVC('time', str, doc_str='name of time dimension in files'),
                        node=PVC('mesh2d_nNodes', str, doc_str='name of node  dimension in files'),

                        all_z_dims=PLC(['mesh2d_nInterfaces','mesh2d_nLayers'], str, doc_str='All z dims, used to identify  3D variables'),
                         ),
            field_variable_map= {'water_velocity': PLC(['mesh2d_ucx', 'mesh2d_ucy', 'mesh2d_ww1'], str, fixed_len=3),
                        'tide': PVC('mesh2d_s1', str, doc_str='maps standard internal field name to file variable name'),
                        'water_depth': PVC('mesh2d_node_z', str, doc_str='maps standard internal field name to file variable name'),
                        'water_temperature': PVC('mesh2d_tem1', str, doc_str='maps standard internal field name to file variable name'),
                        'salinity': PVC('mesh2d_sa1', str, doc_str='maps standard internal field name to file variable name'),
                        'wind_stress': PLC(None, str, doc_str='maps standard internal field name to file variable name'),
                        'bottom_stress': PLC(['mesh2d_tausx', 'mesh2d_tausy'], str, doc_str='maps standard internal field name to file variable name'),
                        'A_Z_profile': PVC('mesh2d_vicwws', str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                        'water_velocity_depth_averaged': PLC(['mesh2d_ucxa','mesh2d_ucya'], str, fixed_len=2,
                                                doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
                            )

    def add_hindcast_info(self):

        dm = self.params['dimension_map']
        fvm= self.params['field_variable_map']
        gm = self.params['grid_variable_map']
        info = self.info
        dims = info['dims']

        if info['is3D']:
            # sort out z dim and vertical grid size
            info['z_dim'] = dm['z']
            info['num_z_levels'] = info['dims'][info['z_dim']]
            info['all_z_dims'] = dm['all_z_dims']
            # 2 variants of fixed z layer dimension names
            if 'mesh2d_nInterfaces' in dims:
                info['z_dim'] = 'mesh2d_nInterfaces'
                info['layer_dim'] = 'mesh2d_nLayers'
                info['all_z_dims'] = ['mesh2d_nInterfaces','mesh2d_nLayers']
            else:
                info['z_dim'] = 'nmesh2d_interface'
                info['layer_dim'] = 'nmesh2d_layer'
                info['all_z_dims'] = ['nmesh2d_interface','nmesh2d_layer']

            info['num_z_levels'] = dims[info['z_dim']]
            info['vert_grid_type'] = si.vertical_grid_types.Zfixed if 'mesh2d_interface_z' in info['variables']  else si.vertical_grid_types.Sigma

        # get num nodes in each field
        # is the number of nodes = uniques nodes in the quad mesh

        info['node_dim'] = 'mesh2d_nNodes' if 'mesh2d_nNodes' in dims else 'nmesh2d_node'

        info['num_nodes'] =  dims[info['node_dim']]
        info['cell_dim'] = 'mesh2d_nFaces' if 'mesh2d_nFaces' in dims else 'nmesh2d_face'

        if info['vert_grid_type'] == si.vertical_grid_types.Sigma:
            si.msg_logger.msg('DEFT3D FM not yet tested with sigma vertical grid, only tested to work with fixed z level grid', warning=True)


    def read_horizontal_grid_coords(self, grid):
        # reader nodal locations
        ds = self.dataset
        gm = self.params['grid_variable_map']

        x = ds.read_variable(gm['x']).data
        y = ds.read_variable(gm['y']).data
        grid['x'] = np.stack((x, y), axis=1).astype(np.float64)

    def read_triangles(self, grid):
        # read nodes in triangles (N by 3) or mix of triangles and quad cells as (N by 4)
        ds = self.dataset
        gm = self.params['grid_variable_map']

        tri = ds.read_variable(gm['triangles']).data
        if tri.shape[1] > 4:
            si.msg_logger.msg(
                f'DELFT3D FM-reader currently only works with triangle and quad cells, not cells with {tri.shape[1]} sides',
                fatal_error=True, caller=self)

        sel = np.isnan(tri)
        tri[sel] = 0
        grid['triangles'] = tri.astype(np.int32) - 1 # make zero based


    def read_dry_cell_data(self,nt_index, buffer_index):
        # get dry cells from water depth and tide
        fields = self.fields
        grid= self.grid
        is_dry_cell_buffer = grid['is_dry_cell_buffer']
        mean_water_depth = np.nanmean(fields['water_depth'].data[0,:,0,0][grid['triangles']],axis=1)

        is_dry_cell_buffer[buffer_index,:]=  mean_water_depth < si.settings.minimum_total_water_depth

        reader_util.set_dry_cell_flag_from_tide(grid['triangles'],  fields['tide'].data, fields['water_depth'].data,
                                                si.settings.minimum_total_water_depth, is_dry_cell_buffer, buffer_index)
        pass

    def build_vertical_grid(self):
        # add time invariant vertical grid variables needed for transformations
        # first values in z axis is the top? so flip
        gm = self.params['grid_variable_map']
        fm = self.params['field_variable_map']
        info = self.info
        grid = self.grid
        ds = self.dataset

        if info['vert_grid_type'] == si.vertical_grid_types.Sigma:
            # assumes first value -1 is at the bottom
            grid['sigma'] = ds.read_variable('mesh2d_interface_sigma').data.astype(np.float32) # layer interfaces
            grid['sigma'][0] = -1.  # not sure why this value is 9.96920997e+36??
            grid['sigma_layer'] = ds.read_variable('mesh2d_layer_sigma').data.astype(np.float32)  # layer center
            # shift to be zero at bottom
            grid['sigma'] = 1.+ grid['sigma']
            grid['sigma_layer'] = 1. + grid['sigma_layer']
        else:
            # fixed z levels
            grid['z'] = ds.read_variable(gm['z']).data.astype(np.float32)  # layer boundary fractions reversed from negative values
            grid['z_layer'] = ds.read_variable(gm['z_layer']).data.astype(np.float32)   # layer center fractions

        super().build_vertical_grid()



        # need to add a layer between first given z level and bottom
        grid['bottom_cell_index'] = np.maximum(grid['bottom_cell_index']-1, 0)


    def read_bottom_cell_index(self, grid):
        gm = self.params['grid_variable_map']
        fm = self.params['field_variable_map']
        info =  self.info
        ds = self.dataset

        if info['vert_grid_type'] == si.vertical_grid_types.Zfixed:
            # find bottom cell based on nans in a dummy read of mid-layer velocity after it has been converted to nodal values
            u = ds.read_variable(fm['water_velocity'][0], nt=0).data  # from non nans in first hori velocity time step
            u = hydromodel_grid_transforms.get_nodal_values_from_weighted_data(u,
                                grid['node_to_quad_cell_map'], grid['quad_cells_per_node'], grid['edge_val_weights'])
            bottom_cell_index = self.find_layer_with_first_non_nan(u[0, :, :])
        else:
            # bottom cell is the first cell
            bottom_cell_index = np.zeros((info['num_nodes'],),  dtype=np.int32)

        return bottom_cell_index


    def build_hori_grid(self, grid):

        super().build_hori_grid(grid)

        ds = self.dataset
        gm = self.params['grid_variable_map']

        # read cell centers, where u,v are defined
        xc = ds.read_variable(gm['x_cell']).data
        yc = ds.read_variable(gm['y_cell']).data
        grid['x_cell'] = np.stack((xc,yc),axis=1)

        # setp up node to face map and weights needed
        # to get nodal values from face values
        grid['quad_face_nodes'] = ds.read_variable(gm['quad_face_nodes']).data
        sel = np.isnan(grid['quad_face_nodes'])
        grid['quad_face_nodes'][sel] = 0
        grid['quad_face_nodes'] = grid['quad_face_nodes'].astype(np.int32) - 1

        grid['node_to_quad_cell_map'],grid['quad_cells_per_node'] = hydromodel_grid_transforms.get_node_to_cell_map(grid['quad_face_nodes'], grid['x'].shape[0])

        # get weights based on inverse distance between node
        # and data inside quad cell interior

        grid['edge_val_weights'] =hydromodel_grid_transforms.calculate_inv_dist_weights_at_node_locations(
                                            grid['x'], grid['x_cell'],
                                            grid['node_to_quad_cell_map'], grid['quad_cells_per_node'])

        return grid

    def read_file_var_as_4D_nodal_values(self, var_name, var_info, nt=None):
        # read variable into 4D ( time, node, depth, comp) format
        # assumes same variable order in the file
        ds = self.dataset
        grid = self.grid
        params = self.params
        info = self.info

        data = ds.read_variable(var_name, nt=nt).data

        # add time dim if needed
        if info['time_dim'] not in var_info['dims']: data = data[np.newaxis, ...]

        # add z dim if needed
        if all(x not in var_info['dims'] for x in info['all_z_dims']): data = data[..., np.newaxis]

        # some variables at nodes, some at edge mid points ( eg u,v,w)
        if info['cell_dim'] in var_info['dims']:
            # data is at cell center/element/triangle  move to nodes
            data = hydromodel_grid_transforms.get_nodal_values_from_weighted_data(
                                        data, grid['node_to_quad_cell_map'], grid['quad_cells_per_node'], grid['edge_val_weights'])
        if var_info['is3D'] and info['layer_dim'] in var_info['dims']:
            if info['vert_grid_type'] == si.vertical_grid_types.Zfixed :
                #  interp fixed z layer values to interfaces, must be done after nodal values
                data = hydromodel_grid_transforms.convert_mid_layer_fixedZ_top_bot_layer_values(
                    data, grid['z_layer'], grid['z'], grid['bottom_cell_index'], grid['water_depth'])
            else:
                # sigma grid
                data = hydromodel_grid_transforms. convert_mid_layer_sigma_top_bot_layer_values(data, grid['sigma_layer'], grid['sigma'])

        # add dummy component axis
        data = data[..., np.newaxis]

        return data

    def setup_water_depth_field(self):
        i = self._add_a_reader_field('water_depth')
        i.data = self.read_field_data('water_depth', i) # read time in varient field
        i.data = -i.data   # depth seems to be read as upwards z at node, so rervese z

    @staticmethod
    @njitOT
    def find_layer_with_first_non_nan(data):
        # find cell with the bottom, from first mid-layer velocities not a nan
        n_nodes=data.shape[0]
        n_zlevels = data.shape[1]
        depth_cell_with_bottom = np.full((n_nodes,),n_zlevels-1, dtype=np.int32)
        for n in range(n_nodes):
            for nz in range(n_zlevels-1): # loop over depth cells
                if ~np.isnan(data[n, nz]) :# find first non-nan
                    depth_cell_with_bottom[n] = nz # note some water depths are <0, land?
                    break

        return depth_cell_with_bottom