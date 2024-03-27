import numpy as np
from oceantracker.reader._base_reader import _BaseReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC

from oceantracker.util.triangle_utilities import split_quad_cells, get_quad_nodes
# readers which give calculated velocity fields on regular grids, by
#  mimicking a netcdf  utility NetCDFhandler class


class DummyDataReader(_BaseReader):


    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params(dict(
            input_dir = PVC('dummy_data_dir', str, is_required=False),
            file_mask = PVC(None, str, is_required=True,
                           doc_str='String gives which test to be run, eg "test_single_gyre"'),
            ))

        self.add_default_params({
            'load_fields' : PLC(['water_depth'], [str], doc_str='always load tide and water depth, for dry cells id 2D'),
            'field_variable_map': {
                                   'water_velocity': PLC(['u', 'v', 'w'], [str], fixed_len=3),
                                   'tide': PVC('mesh2d_s1', str, doc_str='maps standard internal field name to file variable name'),
                                   'water_depth': PVC('mesh2d_node_z', str, doc_str='maps standard internal field name to file variable name'),
                                   'water_velocity_depth_averaged': PLC(['mesh2d_ucx','mesh2d_ucy'], [str], fixed_len=2,
                                                                      doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
                        })
        self.dummy_data_class_map = {
                'single_ocean_gyre2D.nc':SingleOceanGyre2D()
                }

    def get_file_list(self):
        return [self.params['file_mask']]
    def is_file_format(self,file_name):
       return file_name in self.dummy_data_class_map

    def read_time_sec_since_1970( self, nc):
        return nc.read_a_variable('time')

    def is_hindcast3D(self, nc):
        return nc.is3D

    def _open_file(self, file_name):
       return  self.dummy_data_class_map[file_name]

    def read_horizontal_grid_coords(self, nc, grid):
        grid['x'] = np.stack((nc.read_a_variable('x'),nc.read_a_variable('y')),axis=1)
        grid['hydro_model_cords_in_lat_long'] = False
        return grid
    
    def read_triangles_as_int32(self, nc, grid):
        grid['quad_cells'] = nc.read_a_variable('quad_cells')
        grid['quad_cells_to_split'] = np.arange(0,grid['quad_cells'].shape[0],dtype=np.int32)
        grid['triangles'] = split_quad_cells(grid['quad_cells'], grid['quad_cells_to_split'])
        return grid

    def get_field_params(self, nc, name):
        return nc.get_field_params(name)

class _BaseDummyNCDF(object):

    def __init__(self):
        self.grid = dict(time = np.arange(0,14*24*3600))
        grid = self.grid
        self.is3D = False

        grid['xi'], grid['yi']= np.meshgrid(np.arange(0,20000,100.),
                            np.arange(0,10000,100.))
        grid['x'] = grid['xi'].ravel()
        grid['y'] = grid['yi'].ravel()
        grid['quad_cells'] = get_quad_nodes(grid['xi'].shape)

        # fields
        self.fields = {}
        fields= self.fields
        n_nodes= grid['x'].size
        # returns    dict(time_varying= True/False,
        #                         is3D=True/False,
        #                         is_vector= True/False,
        #                         )
        fields['depth'] = dict(data = 100.*np.ones((n_nodes,),dtype=np.float32),
                               is3d=False,is_vector=False,time_varying=False)

        pass

    def read_a_variable(self, var_name, sel=None):
        if var_name in self.grid:
            return  self.grid[var_name]
        elif var_name in self.fields:
            return self.fields[var_name].data
        else:
            raise(f'Dummy reader no variable "{var_name}" defined')

    def is_var(self, var_name ):
      return  var_name in self.grid or var_name in self.fields

    def get_field_params(self, name):
        f = self.fields[name]
        pass

    def close(self): pass




class SingleOceanGyre2D(_BaseDummyNCDF):

    def is3D(self): return False







