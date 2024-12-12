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

class DELFTFM(_BaseUnstructuredReader):
    development = True
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
                        time=PVC('time', str, doc_str='name of time dimension in files'),
                        node=PVC('mesh2d_nNodes', str, doc_str='name of nodes dimension in files'),
                        z=PVC('mesh2d_nInterfaces', str, doc_str='name of dimensions for z layer boundaries '),
                        all_z_dims=PLC(['mesh2d_nInterfaces','mesh2d_nLayers'], str, doc_str='All z dims used to identify  3D variables'),
                        cell_dim=PVC('mesh2d_nFaces', str, doc_str='Triangle/quad cell dim'),
                        z_layer_dim=PVC('mesh2d_nLayers', str, doc_str='Number of layers, one less than z values'),
                         ),
            field_variable_map= {'water_velocity': PLC(['mesh2d_ucx', 'mesh2d_ucy', 'mesh2d_ww1'], str, fixed_len=3),
                        'tide': PVC('mesh2d_s1', str, doc_str='maps standard internal field name to file variable name'),
                        'water_depth': PVC('mesh2d_node_z', str, doc_str='maps standard internal field name to file variable name'),
                        'water_temperature': PVC('temp', str, doc_str='maps standard internal field name to file variable name'),
                        'salinity': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                        'wind_stress': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                        'bottom_stress': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                        'A_Z_profile': PVC(None, str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                        'water_velocity_depth_averaged': PLC(['mesh2d_ucx','mesh2d_ucy'], str, fixed_len=2,
                                                doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
                            )

    def get_hindcast_info(self, catalog):

        dm = self.params['dimension_map']
        fvm= self.params['field_variable_map']
        gm = self.params['grid_variable_map']
        hi = dict(is3D=  'mesh2d_nLayers' in catalog['info']['dims'])

        if hi['is3D']:
            hi['z_dim'] = dm['z']
            hi['num_z_levels'] = catalog['info']['dims'][hi['z_dim']]
            hi['all_z_dims'] = dm['all_z_dims']
            # Only LSC hasbottom_cell_index
            hi['vert_grid_type'] = si.vertical_grid_types.Zfixed if 'mesh2d_interface_z' in catalog['variables'] \
                                                                        else si.vertical_grid_types.Sigma
        else:
            hi['z_dim'] = None
            hi['num_z_levels'] = 1
            hi['all_z_dims'] =  []
            hi['vert_grid_type'] = None

        # get num nodes in each field
        # is the number of nodes = uniques nodes in the quad mesh

        hi['node_dim'] = dm['node']
        hi['num_nodes'] =  catalog['info']['dims'][hi['node_dim']]

        if len(catalog['variables'][gm['triangles']]['dims']) > 4:
            si.msg_logger.msg(f'DELFT3D FM-reader currently only works with triangle and quad cells, not cells with {mesh2d_face_nodes.shape[1]} sides',
                   fatal_error=True, caller=self)

        return hi



    def get_field_params(self,nc, name):
        fmap = self.params['field_variable_map']
        f_params = dict(time_varying=nc.is_var_dim(fmap[name][0], 'time'),
                        is3D=nc.is_var_dim(fmap[name][0], 'mesh2d_nLayers'),
                        is_vector=len(fmap[name]) > 1
                        )
        return f_params

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

    def build_vertical_grid(self, grid):
        # add time invariant vertical grid variables needed for transformations
        # first values in z axis is the top? so flip
        gm = self.params['grid_variable_map']
        fm = self.params['field_variable_map']
        ds = self.dataset
        grid['z'] = ds.read_variable(gm['z']).data.astype(np.float32)  # layer boundary fractions reversed from negative values
        grid['z_layer'] =ds.read_variable(gm['z_layer']).data.astype(np.float32)   # layer center fractions

        grid = super().build_vertical_grid(grid)



        # need to add a layer between first given z level and bottom
        grid['bottom_cell_index'] = np.maximum(grid['bottom_cell_index']-1, 0)
        return  grid

    def read_bottom_cell_index(self, grid):
        gm = self.params['grid_variable_map']
        fm = self.params['field_variable_map']
        ds = self.dataset
        # find bottom cell based on nans in a dummy read of mid-layer velocity after it has been converted to nodal values
        u = ds.read_variable(fm['water_velocity'][0], nt=0).data  # from non nans in first hori velocity time step
        u = hydromodel_grid_transforms.get_nodal_values_from_weighted_data(u,
                            grid['node_to_quad_cell_map'], grid['quad_cells_per_node'], grid['edge_val_weights'])

        bottom_cell_index = self.find_layer_with_first_non_nan(u[0, :, :])
        return bottom_cell_index


    def build_hori_grid(self, grid):

        super().build_hori_grid( grid)
        ds = self.dataset
        gm = self.params['grid_variable_map']

        # read cell centers, where u,v are defined
        xc = ds.read_variable(gm['x_cell']).data
        yc = ds.read_variable(gm['y_cell']).data
        grid['x_cell'] = np.stack((xc,yc),axis=1)

        # setp up node to face map and weights needed
        # to get nodal values from face values
        grid['quad_face_nodes'] = ds.read_variable(gm['quad_face_nodes']).data - 1
        grid['quad_face_nodes'] = numpy_util.ensure_int32_dtype(grid['quad_face_nodes'])

        grid['node_to_quad_cell_map'],grid['quad_cells_per_node'] = hydromodel_grid_transforms.get_node_to_cell_map(grid['quad_face_nodes'], grid['x'].shape[0])

        # get weights based on inverse distance between node
        # and data inside quad cell interior

        grid['edge_val_weights'] =hydromodel_grid_transforms.calculate_inv_dist_weights_at_node_locations(
                                            grid['x'], grid['x_cell'],
                                            grid['node_to_quad_cell_map'], grid['quad_cells_per_node'])

        return grid

    def read_file_var_as_4D_nodal_values(self,var_name,field, nt=None):
        # read variable into 4D ( time, node, depth, comp) format
        # assumes same variable order in the file
        ds = self.dataset
        grid = self.grid
        params = self.params
        gm = params['grid_variable_map']
        dm = params['dimension_map']
        info = self.info

        data = ds.read_variable(var_name, nt=nt)
        data_dims =data.dims
        data = data.data
        # add time dim if needed
        if info['time_dim'] not in data_dims: data = data[np.newaxis, ...]

        # add z dim if needed
        if all(x not in data_dims for x in dm['all_z_dims']): data = data[..., np.newaxis]

        # some variables at nodes, some at edge mid points ( eg u,v,w)
        if dm['cell_dim'] in data_dims:
            # data is at cell center/element/triangle  move to nodes
            data = hydromodel_grid_transforms.get_nodal_values_from_weighted_data(
                                        data, grid['node_to_quad_cell_map'], grid['quad_cells_per_node'], grid['edge_val_weights'])
        # must be done after nodal values
        if dm['z_layer_dim'] in data_dims:
            data = hydromodel_grid_transforms.convert_mid_layer_fixedZ_top_bot_layer_values(
                data, grid['z_layer'], grid['z'], grid['bottom_cell_index'], grid['water_depth'])

        # add dummy component axis
        data = data[..., np.newaxis]

        return data

    def preprocess_field_variable(self, name,grid, data):

        if name =='water_depth':
            # depth seems to be read as upwards z at node, so rervese z
            data = -data
        elif name == 'water_velocity' and data.shape[2] > 1:
            # ensure vel zero at sea bed
            data = reader_util.patch_bottom_velocity_to_make_it_zero(data, grid['bottom_cell_index'])
        return data



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