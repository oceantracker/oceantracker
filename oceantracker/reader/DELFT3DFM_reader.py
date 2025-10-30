from numba.core.cgutils import false_bit

from oceantracker.reader._base_unstructured_reader import _BaseUnstructuredReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
from  oceantracker.util import time_util, numpy_util
import numpy as np
from oceantracker.util.triangle_utilities import split_quad_cells
from oceantracker.reader.util import  reader_util
from oceantracker.reader.util import  hydromodel_grid_transforms as hg_trans
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange
from oceantracker.shared_info import shared_info as si

class DELFT3DFMreader(_BaseUnstructuredReader):
    development =  True
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params(
        regrid_z_to_sigma_levels=PVC(False, bool,
                       doc_str='much faster 3D runs by re-griding hydo-model fields for S-layer or LSC vertical grids (eg. SCHISM),  into uniform sigma levels on read based on sigma most curve z_interface profile. Some hydo-model are already uniform sigma, so this param is ignored, eg ROMS'),

        variable_signature=PLC(['mesh2d_face_nodes'], str, doc_str='Variable names used to test if file is this format'),
            one_based_indices = PVC(True, bool, doc_str='DELFT 3D has indices starting at 1 not zero'),
            load_fields = PLC(['water_depth'], str, doc_str='always load tide and water depth, for dry cells id 2D'),
            grid_variable_map= dict( time= PVC('time', str),
                        x = PVC('mesh2d_node_x', str, doc_str='x location of nodes'),
                        y = PVC('mesh2d_node_y', str, doc_str='y location of nodes'),
                        x_cell=PVC('mesh2d_face_x', str, doc_str='x location of cell centers'),
                        y_cell=PVC('mesh2d_face_y', str, doc_str='y location of cell center'),
                        z= PVC('mesh2d_interface_z', str,doc_str='Layer edges depths'),
                        z_layer_fixed=PVC('mesh2d_layer_z', str, doc_str='Mid layer z for fixed z grid'),
                        z_layer_LSC =PVC('mesh2d_flowelem_zcc', str),
                        triangles= PVC('mesh2d_face_nodes', str),
                        quad_face_nodes=PVC('mesh2d_face_nodes', str),
                        bottom_interface_index= PVC(None, str),
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
                        'water_depth': PVC('mesh2d_bldepth', str, doc_str='maps standard internal field name to file variable name'),
                        'water_temperature': PVC('mesh2d_tem1', str, doc_str='maps standard internal field name to file variable name'),
                        'salinity': PVC('mesh2d_sa1', str, doc_str='maps standard internal field name to file variable name'),
                        'wind_stress': PLC(None, str, doc_str='maps standard internal field name to file variable name'),
                        'bottom_stress': PLC(['mesh2d_tausx', 'mesh2d_tausy'], str, doc_str='maps standard internal field name to file variable name'),
                        'A_Z_profile': PVC('mesh2d_vicwws', str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                        'water_velocity_depth_averaged': PLC(['mesh2d_ucxa','mesh2d_ucya'], str, fixed_len=2,
                                                doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
                            )

    def initial_setup(self):
        params = self.params

        if params['regrid_z_to_sigma_levels']:
            si.msg_logger.msg('Regridding DELFT3D mixed sigma, fixed z vertical grid not yet implemented, using native vertical grid',
                              hint='disabling vertical regridding ',
                          warning=True)
        params['regrid_z_to_sigma_levels'] = False

        super().initial_setup()

    def add_hindcast_info(self):
        ds_info =  self.dataset.info
        params = self.params
        dm = params['dimension_map']
        fvm= params['field_variable_map']
        gm = params['grid_variable_map']
        info = self.info
        dims = info['dims']

        # tweak varaitions in dims and variable names

        if fvm['water_depth'] not in  ds_info['variables']:  fvm['water_depth'] =  'mesh2d_waterdepth'

        if info['is3D']:
            # sort out z dim and vertical grid size
            if info['z_dim'] not in dims: dims['mesh2d_nInterfaces'] = dims['mesh2d_nLayers'] + 1
            info['z_dim'] = dm['z']

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

            info['num_z_interfaces'] = dims[info['z_dim']]

            if 'mesh2d_layer_sigma' in ds_info['variables']:
                info['vert_grid_type'] = si.vertical_grid_types.Sigma

            elif 'mesh2d_layer_z' in  ds_info['variables']:
                info['vert_grid_type'] = si.vertical_grid_types.Zfixed

            elif 'mesh2d_flowelem_zcc' in  ds_info['variables']:
                # mixed sigma, tide moving z levels, ie LSC type grid
                info['vert_grid_type'] = si.vertical_grid_types.LSC
                if params['regrid_z_to_sigma_levels']:
                    si.msg_logger.msg(
                        'Regridding DELFT3D mixed sigma, fixed z vertical grid not yet implemented, using native vertical grid',
                        hint='disabling vertical regridding ',
                        warning=True)
                params['regrid_z_to_sigma_levels'] = False
            else:
                si.msg_logger.msg('Cannot determine vertical grid type',caller=self, fatal_error=True,
                                  hint='Delft3D FM file needs variables "mesh2d_layer_sigma" and  "mesh2d_interface_sigma" if sigma grid, or "mesh2d_layer_z" and "mesh2d_interface_z" if fixed z level grid')
        # get num nodes in each field
        # is the number of nodes = uniques nodes in the quad mesh
        info['node_dim'] = 'mesh2d_nNodes' if 'mesh2d_nNodes' in dims else 'nmesh2d_node'

        info['num_nodes'] =  dims[info['node_dim']]
        info['cell_dim'] = 'mesh2d_nFaces' if 'mesh2d_nFaces' in dims else 'nmesh2d_face'


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
        params= self.params
        gm = params['grid_variable_map']
        fm = params['field_variable_map']
        info = self.info
        grid = self.grid
        ds = self.dataset


        if info['vert_grid_type'] == si.vertical_grid_types.Sigma:
            grid['sigma_interface'] = ds.read_variable('mesh2d_interface_sigma').data.astype(np.float32) # layer interfaces
            grid['sigma_interface'][0] = -1.  # not sure why this value is 9.96920997e+36??
            grid['sigma_layer'] = ds.read_variable('mesh2d_layer_sigma').data.astype(np.float32)  # layer center
            # shift to be zero at bottom
            grid['sigma_interface'] = 1.+ grid['sigma_interface']
            grid['sigma_layer'] = 1. + grid['sigma_layer']
        elif info['vert_grid_type'] == si.vertical_grid_types.LSC:
            pass
        else:
            # fixed z levels
            grid['z'] = ds.read_variable(gm['z']).data.astype(np.float32)  # layer boundary fractions reversed from negative values
            grid['z_layer_fixed'] = ds.read_variable(gm['z_layer_fixed']).data.astype(np.float32)   # layer center fractions

        super().build_vertical_grid()


    def read_bottom_interface_index(self, grid):
        gm = self.params['grid_variable_map']
        fm = self.params['field_variable_map']
        info =  self.info
        ds = self.dataset

        if info['vert_grid_type'] in [si.vertical_grid_types.Zfixed, si.vertical_grid_types.LSC]:
            # find bottom cell based on nans in a dummy read of mid-layer velocity after it has been converted to nodal values
            u = ds.read_variable(fm['water_velocity'][0], nt=0).data  # from non nans in first hori velocity time step
            u = hg_trans.get_nodal_values_from_weighted_cell_values(u,
                                grid['node_to_quad_cell_map'], grid['quad_cells_per_node'], grid['edge_val_weights'])
            grid['bottom_layer_index'] = self.find_z_index_with_first_non_nan(u[0, :, :])
            bottom_interface_index =  grid['bottom_layer_index'] #  layer 0, maps down to interface 0
        else:
            # bottom cell is the first cell in sigma grid
            bottom_interface_index = np.zeros((info['num_nodes'],),  dtype=np.int32)

        return bottom_interface_index

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

        grid['node_to_quad_cell_map'],grid['quad_cells_per_node'] = hg_trans.get_node_to_cell_map(grid['quad_face_nodes'], grid['x'].shape[0])

        # get weights based on inverse distance between node
        # and data inside quad cell interior

        grid['edge_val_weights'] =hg_trans.calculate_inv_dist_weights_at_node_locations(
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
            data = hg_trans.get_nodal_values_from_weighted_cell_values(
                                        data, grid['node_to_quad_cell_map'], grid['quad_cells_per_node'], grid['edge_val_weights'])

        if var_info['is3D'] and info['layer_dim'] in var_info['dims']:
            if info['vert_grid_type'] == si.vertical_grid_types.Zfixed :
                #  interp fixed z layer values to interfaces, must be done after nodal values
                data = hg_trans.convert_3Dfield_fixed_z_layer_to_fixed_z_interface(
                                    data, grid['z_layer_fixed'], grid['z'], grid['bottom_layer_index'], grid['water_depth'])
                pass
            elif info['vert_grid_type'] == si.vertical_grid_types.LSC:
                data = hg_trans.convert_3Dfield_LSC_layer_to_LSC_interface(data,grid['z_layer_LSC' ],grid['z_interface'],
                                                                           grid['bottom_layer_index'])
                pass
            else:
                # sigma grid
                data = hg_trans. convert_3Dfield_sigma_layer_to_sigma_interface(data, grid['sigma_interface'], grid['sigma_interface'])
                pass

        # add dummy component axis
        data = data[..., np.newaxis]

        return data

    def setup_water_depth_field(self):
        i = self._add_a_reader_field('water_depth')
        i.data = self.read_field_data('water_depth', i)


    def read_z_interface(self, nt):
        params = self.params
        grid = self.grid
        z_layer_cell = self.dataset.read_variable(params['grid_variable_map']['z_layer_LSC'], nt = nt)
        # convert to nodal values
        grid['z_layer_LSC' ] = hg_trans.get_nodal_values_from_weighted_cell_values(
                                        z_layer_cell.data,
                                        grid['node_to_quad_cell_map'],
                                        grid['quad_cells_per_node'],
                                        grid['edge_val_weights'])
        # get tide and water depth ( can not  use ring buffer as time step order may not match)
        tide = self.dataset.read_variable(params['field_variable_map']['tide'], nt = nt)
        tide = tide.data[:,:, np.newaxis]# make 3D
        tide = hg_trans.get_nodal_values_from_weighted_cell_values(
                                        tide,
                                        grid['node_to_quad_cell_map'],
                                        grid['quad_cells_per_node'],
                                        grid['edge_val_weights'])
        water_depth = self.dataset.read_variable(params['field_variable_map']['water_depth'], nt=nt)
        water_depth = water_depth.data[np.newaxis, :, np.newaxis]  # make 3D
        water_depth = hg_trans.get_nodal_values_from_weighted_cell_values(
            water_depth,
            grid['node_to_quad_cell_map'],
            grid['quad_cells_per_node'],
            grid['edge_val_weights'])

        # get interfacial values
        data = np.full((nt.size,) + grid['z_interface' ].shape[1:],np.nan, dtype=np.float32 ) # todo faster make a buffer
        self.find_z_interface_from_layer_values(grid['z_layer_LSC' ],water_depth,
                                            tide, grid['bottom_layer_index'], data)
        # find nodal bottom interface index

        return data

    @staticmethod
    @njitOT
    def find_z_index_with_first_non_nan(data):
        # find cell with the bottom, from first mid-layer velocities not a nan
        n_nodes=data.shape[0]
        n_zs = data.shape[1]
        index_with_first_non_nan = np.full((n_nodes,),n_zs-1, dtype=np.int32)
        for n in range(n_nodes):
            for nz in range(n_zs-1): # loop over depth cells
                if ~np.isnan(data[n, nz]) :# find first non-nan
                    index_with_first_non_nan[n] = nz # note some water depths are <0, land?
                    break

        return index_with_first_non_nan

    @staticmethod
    @njitOTparallel
    def find_z_interface_from_layer_values(zlayer_nodes, water_depth, tide,bottom_layer_index,  z_interface):
        # find cell with the bottom, from first mid-layer velocities not a nan
        # adding one interface layer at top
        #     more exact with layer thicknesses, but these not in file?? so use mean
        for nt in prange(zlayer_nodes.shape[0]): # time loop
            for n in range(zlayer_nodes.shape[1]): # node loop
                for nz in range(bottom_layer_index[n], zlayer_nodes.shape[2]-1):
                    z_interface[nt,n,nz+1] = 0.5*(zlayer_nodes[nt,n,nz] + zlayer_nodes[nt,n,nz+1] )

                z_interface[nt, n, -1 ]  = tide[nt,n, 0]
                z_interface[nt, n, bottom_layer_index[n]] = -water_depth[0, n, 0]

        pass
