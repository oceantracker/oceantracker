from oceantracker.particle_properties._base_particle_properties import CustomParticleProperty
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.shared_info import shared_info as si
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange

class RouseNumber(CustomParticleProperty):
    '''
    calculate seabed Rouse number P, ration of fall velocity to turbulent pumping velocity
    from friction velocity. Default is for sea bed. Requires a "terminal_velocity" "velocity_modfier to be added"
    Can  estimate sea surface Rouse number if requested and   wind_stress variable is present in hydro files.
    '''
    development = True
    def __init__(self):
        super().__init__()
        self.add_default_params(
                terminal_velocity_name=PVC(None,str, doc_str='internal name assigned to user added terminal_velocity "trajectory_modifier class"', is_required=True),
                sea_bed = PVC(True, bool,doc_str=' calculate seabed Rouse number, otherwise nea surface', units='dimension ;less')
                )

    def initial_setup(self):

        super().initial_setup()  # required to get base class set up

        params = self.params
        info = self.info

        if params['terminal_velocity_name'] not in si.class_roles.velocity_modifiers:
            si.msg_logger.msg(f'Cannot find terminal velocity trajectory_modifiers "{params["terminal_velocity_name"]}" needed for Rouse number calc.',
                              hint='User must add this class"', fatal_error=True)

        tv = si.class_roles.velocity_modifiers[params['terminal_velocity_name']]

        if tv.params['variance'] is not None:
            si.msg_logger.msg(f'Rouse number currently only works with constant terminal velocity, not for distribution  with given variance ',
                             fatal_error=True)

        info['terminal_velocity'] = tv.params['value']

        if params['sea_bed']:
            info['mode'] = 1 # sea bed
        else:

            if 'wind_stress' not in si.class_roles.particle_properties:
                si.msg_logger.msg(f'Sea surface Rouse number requires "wind_stress" to be loaded by reader',
                                hint = 'Ensure wind stress file variable is mapped to "wind_stress and "wind_stress" is in reader param "load_fields" list',
                                fatal_error=True)
            info['mode'] = 2  # sea surface

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(requires3D=True)
    def update(self,n_time_step, time_sec,active):
        info = self.info
        part_prop = si.class_roles.particle_properties

        if info['mode'] == 1:
            self._calc_seabed_Rouse(part_prop['friction_velocity'].data,  info['terminal_velocity'],self.data,active)

        elif info['mode'] == 2:
            self._calc_seasurface_Rouse(part_prop['wind_stress'].data, info['terminal_velocity'],si.settings.water_density, self.data, active)

    @staticmethod
    @njitOTparallel
    def _calc_seabed_Rouse(friction_velocity, terminal_velocity, Rouse, active):
        for nn in prange(active.size):
            n = active[nn]
            Rouse[n] = terminal_velocity/0.4/friction_velocity[n]

    @staticmethod
    @njitOTparallel
    def _calc_seasurface_Rouse(wind_stress, terminal_velocity, density, Rouse, active):
        inv_density =1./density
        for nn in prange(active.size):
            n = active[nn]
            friction_velocity = np.sqrt( np.sqrt(wind_stress[n,0]**2 + wind_stress[n,1]**2) * inv_density)
            Rouse[n] = terminal_velocity/0.4/friction_velocity

