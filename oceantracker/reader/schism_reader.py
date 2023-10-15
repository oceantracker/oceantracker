from oceantracker.reader._base_reader import _BaseReader
from oceantracker.reader.util import reader_util
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
from oceantracker.util import  time_util
from datetime import  datetime
import numpy as np
from oceantracker.util.triangle_utilities_code import split_quad_cells

class SCHISMSreaderNCDF(_BaseReader):

    def __init__(self, shared_memory_info=None):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({
            'cords_in_lat_long': PVC(False, bool, doc_str='Convert given nodal lat longs to a UTM metres grid'),
            'grid_variable_map': {'time': PVC('time', str),
                               'x': PLC(['SCHISM_hgrid_node_x', 'SCHISM_hgrid_node_y'], [str], fixed_len=2),
                               'zlevel': PVC('zcor', str),
                               'triangles': PVC('SCHISM_hgrid_face_nodes', str),
                               'bottom_cell_index': PVC('node_bottom_index', str),
                               'is_dry_cell': PVC('wetdry_elem', np.int8, doc_str='Time variable flag of when cell is dry, 1= is dry cell')},
            'field_variable_map': {'water_velocity': PLC(['hvel', 'vertical_velocity'], [str], fixed_len=3),
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
            'dimension_map': {'time': PVC('time', str),
                              'node': PVC('nSCHISM_hgrid_node', str),
                              'z': PVC('nSCHISM_vgrid_layers', str),
                              'z_water_velocity': PVC('nSCHISM_vgrid_layers', str, doc_str='z dimension of water velocity, used to test if hydro model has 3D velocity field'),
                              'vector2D': PVC('two', str),
                              'vector3D': PVC('three', str),
                              },
            'one_based_indices': PVC(True, bool, doc_str='indices in Schism are 1 based'),
            'hgrid_file_name': PVC(None, str),
             })

    # Below are basic variable read methods for any new reader
    #---------------------------------------------------------

    def read_time_sec_since_1970(self, nc, file_index=None):
        var_name=self.params['grid_variable_map']['time']
        time = nc.read_a_variable(var_name, sel=file_index)

        base_date=  [ int(float(x)) for x in nc.var_attr(var_name,'base_date').split()]
        d0= datetime(*tuple(base_date))
        d0 = np.datetime64(d0).astype('datetime64[s]')
        sec = time_util.datetime64_to_seconds(d0)
        time += sec
        return time

    def read_bottom_cell_index(self, nc):
        # time invariant bottom cell index, which varies across grid in LSC vertical grid
        var_name =self.params['grid_variable_map']['bottom_cell_index']
        if nc.is_var(var_name):
            node_bottom_index = nc.read_a_variable(var_name)
            node_bottom_index -= 1 # make zero based index
            vertical_grid_type = 'LSC'
        else:
            # Slayer grid, bottom cell index = zero
            node_bottom_index = np.zeros((self.grid['x'].shape[0],),dtype=np.int32)
            vertical_grid_type = 'Slayer'
        self.info['vertical_grid_type'] = vertical_grid_type
        return node_bottom_index

    def read_triangles(self, nc, grid):
        params = self.params
        var_name = params['grid_variable_map']['triangles']
        triangles = nc.read_a_variable(var_name).astype(np.int32)
        triangles -= 1 # make zero based

        # split quad cells aby adding new triangles
        # flag quad cells for splitting if index in 4th column
        if triangles.shape[1] == 4 :
            # split quad grids buy making new triangles
            grid['quad_cells_to_split'] = np.flatnonzero(triangles[:, 3] > 0)
            grid['triangles'] = split_quad_cells(triangles, grid['quad_cells_to_split'])
        else:
            grid['quad_cells_to_split'] = np.full((0,), 0, dtype=np.int32)

        return grid


    def preprocess_field_variable(self, nc,name, data):
        if name =='water_velocity' and data.shape[2] > 1:
            # for 3D schism velocity partial fix for  non-zero hvel at nodes where cells in LSC grid span a change in bottom_cell_index
            data = reader_util.patch_bottom_velocity_to_make_it_zero(data, self.grid['bottom_cell_index'])
        return data