# modfiy aspects pof all isActive particles, ie moving and stranded
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
import numpy as np
from oceantracker.resuspension._base_resuspension import _BaseResuspension
from oceantracker.util.numba_util import njitOT

from numba import  njit

class BasicResuspension(_BaseResuspension):
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

    # is 3D test of parent
    def check_requirements(self):
        self.check_class_required_fields_prop_etc(requires3D=True)

    def initial_setup(self, **kwargs):
        si = self.shared_info
        info = self.info
        pass

   
    def select_particles_to_resupend(self, active):
        # compare to single critical value
        # todo add comparison to  particles critical value from distribution, add new particle property to hold  individual critical values
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        on_bottom = part_prop['status'].compare_all_to_a_value('eq', si.particle_status_flags['on_bottom'], out = self.get_partID_buffer('B1'))

        # compare to critical friction velocity
        resupend = part_prop['friction_velocity'].find_subset_where(on_bottom, 'gteq',self.params['critical_friction_velocity'], out=self.get_partID_subset_buffer('B1'))
        return resupend


    # all particles checked to see if they need status changing
    def update(self,time_sec, active):
        # do resupension
        #todo move 'resuspension_factor' calc to initialize() when substeping removed
        #todo is friction velocity up to date?
        self.start_update_timer()
        si= self.shared_info
        info = self.info
        info['resuspension_factor']= 2.0*0.4*si.z0*si.settings['time_step']/(1. - 2./np.pi)
        info['min_resuspension_jump_not_used'] = np.sqrt(info['resuspension_factor']*self.params['critical_friction_velocity'])

        # resuspend those on bottom and friction velocity exceeds critical value
        part_prop = si.classes['particle_properties']
        resuspend = self.select_particles_to_resupend(active)

        self.resuspension_jump(part_prop['friction_velocity'].data, info['resuspension_factor'], part_prop['x'].data, part_prop['water_depth'].data,si.z0, resuspend)

        #  don't adjust resupension distance for terminal velocity,
        #  Lynch (Particles in the Ocean Book, says don't adjust as a fall velocity  affects prior that particle resuspends)

        # any z out of bounds will  be fixed by find_depth cell at start of next time step
        part_prop['status'].set_values(si.particle_status_flags['moving'], resuspend)

        self.stop_update_timer()

    @staticmethod
    @njitOT
    def resuspension_jump(friction_velocity, resuspension_factor, x, water_depth, z0, sel):
        # add entrainment jump up to particle z, Book: Lynch(2015) book, Particles in the coastal ocean  eq 9.26 and 9.28
        for n in sel:
            x[n, 2] = -water_depth[n] + z0 + np.sqrt(resuspension_factor*friction_velocity[n])*np.abs(np.random.randn())

