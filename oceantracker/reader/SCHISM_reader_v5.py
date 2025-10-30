from oceantracker.reader.SCHISM_reader import SCHISMreader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
from pathlib import Path as pathlib_Path
from os import  path
import numpy as np
from copy import  deepcopy, copy
from glob import  glob
class SCHISMreaderV5(SCHISMreader):

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
