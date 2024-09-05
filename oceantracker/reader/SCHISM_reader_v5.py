from oceantracker.reader.SCHISM_reader import SCHISMreaderNCDF
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
from pathlib import Path as pathlib_Path
from os import  path
import numpy as np
from copy import  deepcopy, copy
from glob import  glob
class SCHISMreaderNCDFv5(SCHISMreaderNCDF):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        # redefine any variable names which differ from older schism format
        self.add_default_params(
            grid_variable_map= { 'zlevel': PVC('zCoordinates', str),
                                  'is_dry_cell': PVC('dryFlagElement', str, doc_str='Time variable flag of when cell is dry, 1= is dry cell')},
            field_variable_map= {'water_velocity': PLC(['horizontalVelX','horizontalVelY', 'verticalVelocity'], str),
                                   'tide': PVC('elevation', str, doc_str='maps standard internal field name to file variable name'),
                                   'water_depth': PVC('depth', str, doc_str='maps standard internal field name to file variable name'),
                                   'water_temperature': PVC('temp', str, doc_str='maps standard internal field name to file variable name'),
                                   'salinity': PVC('salt', str, doc_str='maps standard internal field name to file variable name'),
                                   'wind_stress': PVC('wind_stress', str, doc_str='maps standard internal field name to file variable name'),
                                   'bottom_stress': PVC('bottom_stress', str, doc_str='maps standard internal field name to file variable name'),
                                   'A_Z_profile': PVC('diffusivity', str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                   'water_velocity_depth_averaged': PLC(['dahv'], str,
                                                                        doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
            dimension_map = {'time': PVC('time', str),
                            },
            variable_signature= PLC(['SCHISM_hgrid_node_x', 'horizontalVelX','dryFlagElement'], str, doc_str='Variable names used to test if file is this format'),
                        )







