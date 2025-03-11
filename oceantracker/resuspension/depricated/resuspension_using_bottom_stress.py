# modfiy aspects pof all isActive particles, ie moving and stranded
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
import numpy as np
from oceantracker.resuspension._base_resuspension import _BaseResuspension
from oceantracker.util.numba_util import njitOT

from oceantracker.resuspension.resuspension import ResuspensionUsingNearSeaBedVel
from oceantracker.shared_info import shared_info as si

class ResuspensionUsingBottomStress(ResuspensionUsingNearSeaBedVel):
    # only need to redefine how friction velocity is calculated to be from bottom stress field read from hindcast

    # Lynch, Daniel R., David A. Greenberg, Ata Bilgili, Dennis J. McGillicuddy Jr, James P. Manning, and Alfredo L. Aretxabaleta.
    # Particles in the coastal ocean: Theory and applications. Cambridge University Press, 2014.
    # Equation  eq 9.26 and 9.28

    def required_classes_and_settings(self, settings, known_reader_fields, msg_logger):
        required_reader_fields = ['bottom_stress']
        custom_field_params = [dict(name='friction_velocity', class_name='FrictionVelocityFromBottomStress',
                                    requires3D=True, write_interp_particle_prop_to_tracks_file=False)]
        msg_logger.msg('Found bottom stress in hydro-files, using it to calculate friction velocity for particle resuspension', note=True)
        field_settings = {}  # settings for the field instance which affects its itial set up or update, eg use_bottom?_stress for resupension class
        return required_reader_fields, custom_field_params, field_settings



