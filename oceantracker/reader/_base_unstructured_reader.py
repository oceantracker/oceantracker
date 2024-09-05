from oceantracker.shared_info import shared_info as si
from oceantracker.reader._base_all_readers import _BaseReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterTimeChecker as PTC, ParameterListChecker as PLC
import numpy as np
from  oceantracker.util import time_util, numpy_util
import oceantracker.reader.util.hydromodel_grid_transforms as  hydromodel_grid_transforms
from oceantracker.util.numpy_util import ensure_int32_dtype
class _BaseUnstructuredReader(_BaseReader):
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params(
            dimension_map=dict(node=PVC('node', str, doc_str='Nodes in grid', is_required=True)),
        )  # list of normal required dimensions

    # Below are basic variable read methods for any new reader
    # ---------------------------------------------------------


    def read_triangles(self, grid):
        # read nodes in triangles (N by 3) or mix of triangles and quad cells as (N by 4)
        ds = self.dataset
        gm = self.grid_variable_map

        tri = ds.read_variable(gm['triangles']).data
        tri = numpy_util.ensure_int32_dtype(tri)
        if self.params['one_based_indices']:  tri-= 1  # make zero based
        tri = ensure_int32_dtype(tri,missing_value=-1)
        return tri

    def read_water_depth(self, grid):
        ds = self.dataset
        gm = self.grid_variable_map
        water_depth = ds.read_variable(gm['water_depth']).data
        return water_depth



    def read_file_var_as_4D_nodal_values(self, var_name, var_info, nt=None):
        # todo add name to params!!
        # read variable into 4D ( time, node, depth, comp) format
        # assumes same variable order in the file
        d= self.dataset.read_variable(var_name, nt=nt)  # returns xarray
        # get 4D size

        s = var_info['shape4D'].copy()
        time_dim = si.hindcast_info[ 'time_dim']
        s[0] = d.coords[time_dim].size if time_dim in d.dims else 1
        return d.data.reshape(s)

    def set_up_uniform_sigma(self, grid):
        # read z fractions into grid , for later use in vertical regridding, and set up the uniform sigma to be used
        ds = self.dataset
        gm = self.params['grid_variable_map']

        # read first zlevel time step
        zlevel =ds.read_variable(gm['zlevel']).data[0,:,:]

        # use node with thinest top/bot layers as template for all sigma levels
        grid['zlevel_fractions'] = hydromodel_grid_transforms.convert_zlevels_to_fractions(zlevel, grid['bottom_cell_index'], si.settings.z0)

        # get profile with the smallest bottom layer  tickness as basis for first sigma layer
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