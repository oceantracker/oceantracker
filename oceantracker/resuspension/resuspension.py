# modfiy aspects pof all isActive particles, ie moving and stranded
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
import numpy as np
from oceantracker.resuspension._base_resuspension import BaseResuspension
from oceantracker.util.numba_util import njitOT, njitOTparallel

from numba import  njit, prange
from oceantracker.shared_info import shared_info as si

status_on_bottom = int(si.particle_status_flags.on_bottom)
status_moving= int(si.particle_status_flags.moving)

class Resuspension(BaseResuspension):
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
        self.start_update_timer()
        info = self.info

        # resuspend those on bottom and friction velocity exceeds critical value
        part_prop = si.class_roles.particle_properties

        self.resuspension_jump(part_prop['friction_velocity'].data, part_prop['status'].data,
                                self.params['critical_friction_velocity'],
                               info['resuspension_factor'],
                               part_prop['x'].data, part_prop['water_depth'].data,si.settings.z0, alive)


        self.stop_update_timer()

    @staticmethod
    @njitOT
    def resuspension_jump(friction_velocity, status,
                          critical_friction_velocity,
                          resuspension_factor, x, water_depth, z0, alive):
        # add entrainment jump up to particle z, Book: Lynch(2015) book, Particles in the coastal ocean  eq 9.26 and 9.28
        for n in alive:
            #todo threade prange version give diffent results in tracks only  .2m on average,
            # so slight different if decision when threaded? use threads  and accept change for faster threaded code?
            if status[n] == status_on_bottom and friction_velocity[n] >= critical_friction_velocity:
                # do suspension
                x[n, 2] = -water_depth[n] + z0 + np.sqrt(resuspension_factor*friction_velocity[n])*np.abs(np.random.randn())
                status[n] = status_moving
