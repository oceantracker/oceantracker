# ROMS reader that reads  ROMs output varibles used in MOANA MBIE project NZ ROMS model 2022
# where variabel names have changed
from oceantracker.reader.ROMS_reader import ROMSreader
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC, ParameterListChecker as PLC

class ROMSreaderMoanaProjectNZ( ROMSreader):
    development = True
    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults
        self.add_default_params(

                field_variable_map= {'water_velocity': PLC(['u_eastward','v_northward','w'], str, fixed_len=3),
                                    'water_depth': PVC('h', str),
                                    'tide': PVC('zeta', str),
                                    'water_temperature': PVC('temp', str) ,
                                    'bottom_stress': PVC(None, str, doc_str='maps standard internal field name to file variable name'),
                                    'A_Z_profile': PVC(None, str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                    'water_velocity_depth_averaged':PLC(['ubar','vbar'], str, fixed_len=2),
                                    },
                grid_variable_map=dict(
                                    time=PVC('ocean_time', str, doc_str='Name of time variable in hindcast'),
                                    x=PVC('lon_psi', str),
                                    y=PVC('lat_psi', str)),
                dimension_map=dict(  z=PVC('s_w', str, doc_str='name of dimensions for z layer boundaries '),
                            all_z_dims=PLC(['s_w','s_rho'], str, doc_str='All z dims used to identify  3D variables'),
                             row=PVC('eta_psi', str, doc_str='row dim of grid'),
                            col=PVC('xi_psi', str, doc_str='column dim of grid'),
                                      ),

                variable_signature= PLC(['mask_psi','lat_psi','lon_psi','h','zeta','s_w','s_rho'], str,
                                         doc_str='Variable names used to test if file is this format'),
                  )
        pass
    pass
