# modfiy aspects pof all isActive particles, ie moving and stranded
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
import numpy as np
from oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier


from numba import  njit

class BasicResuspension(_BaseTrajectoryModifier):
    # based on
    # Lynch, Daniel R., David A. Greenberg, Ata Bilgili, Dennis J. McGillicuddy Jr, James P. Manning, and Alfredo L. Aretxabaleta.
    # Particles in the coastal ocean: Theory and applications. Cambridge University Press, 2014.
    # Equation  eq 9.26 and 9.28

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'name': PVC('BasicResuspension',str),
                                 'critical_friction_velocity': PVC(0., float, min=0.),
                                 })

    # is 3D test of parent
    def check_requirements(self):
        msg_list = self.check_class_required_fields_prop_etc(
                        required_fields_list=['friction_velocity', 'water_velocity'],
                        required_props_list=['status','water_velocity'], requires3D=True)
        return msg_list

    def initialize(self,**kwargs):
        si = self.shared_info
        info = self.info
        info['number_resupended'] = 0

    def select_particles_to_resupend(self, active):
        # compare to single critical value
        # todo add comparison to  particles critical value from distribution, add new particle property to hold  individual critical values
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        on_bottom = part_prop['status'].compare_all_to_a_value('eq', si.particle_status_flags['on_bottom'], out = self.get_particle_index_buffer())

        # compare to critical friction velocity
        resupend = part_prop['friction_velocity'].find_subset_where(on_bottom, 'gteq',self.params['critical_friction_velocity'], out=self.get_particle_subset_buffer())
        return resupend


    # all particles checked to see if they need status changing
    def update(self, nb, time, active):
        # do resupension
        #todo move 'resuspension_factor' calc to initialise when substeping removed
        self.start_update_timer()
        si= self.shared_info
        info = self.info
        info['resuspension_factor']= 2.0*0.4*si.z0*si.model_substep_timestep/(1. - 2./np.pi)
        info['min_resuspension_jump']  = np.sqrt(info['resuspension_factor']*self.params['critical_friction_velocity'])

        # redsuspend those on bottom and friction velocity exceeds critical value
        part_prop = si.classes['particle_properties']
        resupend = self.select_particles_to_resupend(active)

        self.resuspension_jump(part_prop['friction_velocity'].data, self.info['resuspension_factor'], part_prop['x'].data, resupend)

        #  dont adjust resupension distance for terminal velocity,
        #  Lynch (Particles in the Ocean Book, says dont adjust as a fall velocity  affects prior that particle resuspends)

        # any z out of bounds will  be fixed by find_depth cell at start of next time step
        self.info['number_resupended'] += resupend.shape[0]
        part_prop['status'].set_values(si.particle_status_flags['moving'], resupend)

        self.stop_update_timer()

    @staticmethod
    @njit
    def resuspension_jump(friction_velocity, resuspension_factor, x, sel):
        # add entrainment jump up to particle z, Book: Lynch(2015) book, Particles in the coastal ocean  eq 9.26 and 9.28
        for n in sel:
            x[n, 2] += np.sqrt(resuspension_factor*friction_velocity[n])*np.abs(np.random.randn())

