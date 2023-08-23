from oceantracker.reader.dev.dev_base_reader import _BaseReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
from oceantracker.util import  time_util
from datetime import  datetime
import numpy as np

from oceantracker.reader.util import reader_util

class SCHISMSreaderNCDF(_BaseReader):

    def __init__(self, shared_memory_info=None):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({
            'cords_in_lat_long': PVC(False, bool, doc_str='Convert given nodal lat longs to a UTM metres grid'),
            'z_var_name' :  PVC('zcor', str, doc_str='Name of z layers variable, if present hindcast is taken as 3D'),
            'z_dim_name': PVC('nSCHISM_vgrid_layers', str, doc_str='Name of z dimension in netcdf file,  used to see if field is 3D'),
            'triangles_var_name': PVC('SCHISM_hgrid_face_nodes', str, doc_str='Name of z dimension in netcdf file,  used to see if field is 3D'),
            'time_dim_name': PVC('time', str, doc_str='Name of time dimension in netcdf file,  used to see if field is time dependent'),
            '2D_dim_name': PVC('two', str, doc_str='Name of 2D vector dimension'),
            'x_var_map': PLC(['SCHISM_hgrid_node_x','SCHISM_hgrid_node_y'], acceptable_types=[str], doc_str='Map to  of x coord variables in file',make_list_unique=True),
            'water_velocity_var_map': PLC(['hvel', 'vertical_velocity'], acceptable_types=[str], doc_str='Map to  of xvariables in velocity vector',make_list_unique=True),
            'one_based_indices': PVC(True, bool, doc_str='indices in Schism are 1 based'),
            'hgrid_file_name': PVC(None, str),
             })

    # Below are basic variable read methods for any new reader
    #---------------------------------------------------------

    def read_time_sec_since_1970(self, nc, file_index=None):
        time = nc.read_a_variable('time', sel=file_index)

        base_date=  [ int(float(x)) for x in nc.var_attr('time','base_date').split()]

        d0= datetime(base_date[0], base_date[1], base_date[2], base_date[3], base_date[4])
        d0 = np.datetime64(d0).astype('datetime64[s]')
        sec = time_util.datetime64_to_seconds(d0)
        time += sec

        if self.params['time_zone'] is not None:
            time += self.params['time_zone'] * 3600.

        return time

    def read_bottom_cell_index(self, nc):
        # time invariant bottom cell index, which varies across grid in LSC vertical grid
        if nc.is_var('node_bottom_index'):
            node_bottom_index = nc.read_a_variable('node_bottom_index')
            node_bottom_index -= 1 # make zero based index
            vertical_grid_type = 'LSC'
        else:
            # Slayer grid, bottom cell index = zero
            node_bottom_index = np.zeros((self.grid['x'].shape[0],),dtype=np.int32)
            vertical_grid_type = 'Slayer'

        return node_bottom_index,  vertical_grid_type

