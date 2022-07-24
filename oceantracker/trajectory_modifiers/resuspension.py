# modfiy aspects pof all isActive particles, ie moving and stranded
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
import numpy as np
from oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier


from numba import  njit

class BasicResuspension(_BaseTrajectoryModifier):

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'name': PVC('BasicResuspension',str),
                                 'critical_friction_velocity': PVC(0.,float, min=0.),
                                 })

    # is 3D test of parent
    def check_requirements(self):
        msg_list = self.check_class_required_fields_properties_grid_vars_and_3D(
                        required_props=['friction_velocity', 'status','water_depth'], requires3D=True)
        return msg_list

    def initialize(self,**kwargs):pass

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
        si= self.shared_info
        # redsuspend those on bottom and friction velocity exceeds critical value
        part_prop = si.classes['particle_properties']
        resupend= self.select_particles_to_resupend(active)

        # short cuts to random walk size in dispersion etc
        rz = si.classes['dispersion'].info['rx'][2]

        self.info['number_resupended'] = resupend.shape[0]

        z = part_prop['x'].dataInBufferPtr()[:, 2]  # z as view of all of x

        z[resupend] = -part_prop['water_depth'].get_values(resupend) + rz * np.abs(np.random.randn(resupend.shape[0]))

        # any z out of bounds will  be fixed by find_depth cell at start of next time step

        part_prop['status'].set_values(si.particle_status_flags['moving'], resupend)

