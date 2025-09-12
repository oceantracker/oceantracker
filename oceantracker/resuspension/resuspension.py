# modfiy aspects pof all isActive particles, ie moving and stranded
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
import numpy as np
from oceantracker.resuspension._base_resuspension import _BaseResuspension
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange

from numba import  njit, prange
from oceantracker.shared_info import shared_info as si

status_on_bottom = int(si.particle_status_flags.on_bottom)
status_moving= int(si.particle_status_flags.moving)

class Resuspension(_BaseResuspension):
    # based on
    # Lynch, Daniel R., David A. Greenberg, Ata Bilgili, Dennis J. McGillicuddy Jr, James P. Manning, and Alfredo L. Aretxabaleta.
    # Particles in the coastal ocean: Theory and applications. Cambridge University Press, 2014.
    # Equation  eq 9.26 and 9.28

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({
                'critical_friction_velocity': PVC(0., float, min=0., doc_str='Critical friction velocity, u_* in m/s defined in terms of bottom stress (this param is not the same as near seabed velocity)'),
                                 })

    def add_required_classes_and_settings(self):
        i = si.add_custom_field('friction_velocity', dict(write_interp_particle_prop_to_tracks_file=False),
                                default_classID='field_friction_velocity')


    def initial_setup(self, **kwargs):
        info = self.info
        #  don't adjust re-suspension distance for terminal velocity,
        #  Lynch (Particles in the Ocean Book, says don't adjust due fall velocity, as it  affects prior that particle resuspends)
        info['resuspension_factor']= 2.0*0.4*si.settings.z0*si.settings.time_step/(1. - 2./np.pi)
        pass




    # all particles checked to see if they need status changing
    def update(self,n_time_step, time_sec, alive):
        # do resupension

        info = self.info
        # resuspend those on bottom and friction velocity exceeds critical value
        part_prop = si.class_roles.particle_properties
        resupend= self.select_particles_to_resupend(alive)
        self._resuspension_jump(part_prop['friction_velocity'].data, part_prop['status'].data,
                                 info['resuspension_factor'],
                                part_prop['x'].data, part_prop['water_depth'].data, si.settings.z0, resupend)


    @staticmethod
    @njitOT
    def _resuspension_jump(friction_velocity, status,
                           resuspension_factor, x, water_depth, z0, sel):
        # add entrainment jump up to particle z, Book: Lynch(2015) book, Particles in the coastal ocean  eq 9.26 and 9.28
        for nn in range(sel.size): # dont used prange as sel is typically  small
            n = sel[nn]
            x[n, 2] = -water_depth[n] + z0 + np.sqrt(resuspension_factor*friction_velocity[n])*np.abs(np.random.randn())
            status[n] = status_moving
