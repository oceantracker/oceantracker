from oceantracker.reader.SCHISM_reader import SCHISMreader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
from pathlib import Path as pathlib_Path
from os import  path
import numpy as np
from copy import  deepcopy, copy
from oceantracker.util.numba_util import njitOT,njitOTparallel,prange
from oceantracker.reader.util import  reader_util

class SCHISMreaderV5(SCHISMreader):
    '''
    New Schsim output format  has variables in different files
    '''
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        # redefine any variable names which differ from older schism format
        self.add_default_params(
            file_mask= PVC('*.nc', str,
                         doc_str='Mask for file names, for Schism 5 default is ``*.nc``,, ie.  all netcdf files, finds all files matching in ``input_dir`` and its sub dirs that match the file_mask pattern'),
            grid_variable_map= dict(z_interface = PVC('zCoordinates', str),
                                is_dry_cell= PVC('dryFlagElement', str, doc_str='Time variable flag of when cell is dry, 1= is dry cell'),
                                 bottom_interface_index = PVC('bottom_index_node', str)),
   
            field_variable_map= {'water_velocity': PLC(['horizontalVelX','horizontalVelY', 'verticalVelocity'], str),
                                   'tide': PVC('elevation', str, doc_str='maps standard internal field name to file variable name'),
                                   'water_depth': PVC('depth', str, doc_str='maps standard internal field name to file variable name'),
                                   'water_temperature': PVC('temp', str, doc_str='maps standard internal field name to file variable name'),
                                   'salinity': PVC('salt', str, doc_str='maps standard internal field name to file variable name'),
                                   'wind_stress': PLC(['wind_stress'], str, doc_str='maps standard internal field name to file variable name'),
                                   'bottom_stress': PLC(['bottom_stress'], str, doc_str='maps standard internal field name to file variable name'),
                                   'A_Z_profile': PVC('diffusivity', str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                   'water_velocity_depth_averaged': PLC(['dahv'], str,
                                                                        doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
            dimension_map = {'time': PVC('time', str),
                            },
            variable_signature= PLC(['depth','elevation', 'dryFlagElement'], str, doc_str='Variable names used to test if file is this format'),
                        )

class SCHISMreader_CSIRO_CCAHPS(SCHISMreader):
    ''' CSIRO Austraiia national model
     https://data.csiro.au/collection/csiro:65669
     '''

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        # redefine any variable names which differ from older schism format
        self.add_default_params(
            file_mask=PVC('*.nc', str,
                          doc_str='Mask for file names, for Schism 5 default is ``*.nc``,, ie.  all netcdf files, finds all files matching in ``input_dir`` and its sub dirs that match the file_mask pattern'),
            grid_variable_map=dict(z_interface=PVC('zCoordinates', str),
                                   is_dry_cell=PVC('wetdry_node', str,
                                                   doc_str='Time variable flag of when cell is dry, 1= is dry cell'),
                                 ),

            field_variable_map={'water_velocity': PLC(['u0', 'v0'], str),
                                'tide': PVC('zos', str,
                                            doc_str='maps standard internal field name to file variable name'),
                                'water_depth': PVC('depth', str,
                                                   doc_str='maps standard internal field name to file variable name'),
                                # 'wind_stress': PLC(['wind_stress'], str, doc_str='maps standard internal field name to file variable name'),
                                #  'bottom_stress': PLC(['bottom_stress'], str, doc_str='maps standard internal field name to file variable name'),
                                },
            dimension_map={'time': PVC('time', str),
                           },
            variable_signature=PLC(['depth', 'zos','wetdry_node'], str, doc_str='Variable names used to test if file is this format'),
        )

    def read_triangles(self, grid):
        # read nodes in triangles (N by 3) or mix of triangles and quad cells as  (N by 3)

        ds = self.dataset
        gm = self.params['grid_variable_map']

        tri = ds.read_variable(gm['triangles']).data

        tri = tri[:,:3] # no quad cells
        sel = np.isnan(tri)

        # unlike standard schism has zero based in index, a missing values in column 4
        tri = tri.astype(np.int32)

        grid['triangles'] = tri

        if False:
            import matplotlib.pyplot as plt
            plt.triplot(grid['x'][:, 0], grid['x'][:, 1], tri)
            plt.show()

    def read_dry_cell_data(self,nt_index, buffer_index):
        # calculate dry cell flags, if any cell node is then dry is_dry_cell_buffer=1
        grid = self.grid
        is_dry_cell_buffer = grid['is_dry_cell_buffer']

        # this model has dry nodes , no dry cells, so fidn cessl with 3 dry nodes
        dry_nodes = self.dataset.read_variable(self.params['grid_variable_map']['is_dry_cell'], nt_index).data

        self.find_dry_cells(grid['triangles'], dry_nodes, is_dry_cell_buffer, buffer_index)


    @staticmethod
    @njitOT
    def find_dry_cells(triangles, dry_nodes,is_dry_cell_buffer, buffer_index):
        # find cells with 3 dry nodes

        for nb in buffer_index:
            # count dry nodes of each cell
            n_dry_nodes_per_cell = 0
            for tri in range(triangles.shape[0]):
                for node in triangles[tri, :3]: # nodes of this triangle
                    n_dry_nodes_per_cell += dry_nodes[nb,node] == 1

                is_dry_cell_buffer[nb,tri] = n_dry_nodes_per_cell == 3



