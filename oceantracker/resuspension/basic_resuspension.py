# modfiy aspects pof all isActive particles, ie moving and stranded
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
import numpy as np
from oceantracker.resuspension._base_resuspension import _BaseResuspension
from oceantracker.util.numba_util import njitOT, njitOTparallel
from oceantracker.shared_info import  shared_info as si

from numba import  njit

class BasicResuspension(_BaseResuspension):
    '''
    A very basic resupension, resuspend a distance of random walk, with variance equal to the constant vertical eddy viscosity
     '''
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'name': PVC('BasicResuspension',str),
                                 'critical_friction_velocity': PVC(0.,float, min=0.),
                                 })

    def add_required_classes_and_settings(self):
        i = si.add_custom_field('friction_velocity', dict(write_interp_particle_prop_to_tracks_file=False),
                                default_classID='field_friction_velocity')
    # is 3D test of parent
    def check_requirements(self):
        self.check_class_required_fields_prop_etc(requires3D=True)

    def initial_setup(self,**kwargs): pass

    def update(self, nb, time, active):
        # do resupension
        # redsuspend those on bottom and friction velocity exceeds critical value
        part_prop = si.class_roles.particle_properties
        resupend = self.select_particles_to_resupend(active)

        # short cuts to random walk size in dispersion etc
        self.info['resuspension_variance'] = si.core_class_roles.dispersion.info['random_walk_size'][2]

        self.info['number_resupended'] = resupend.shape[0]

        z = part_prop['x'].used_buffer()[:, 2]  # z as view of all of x

        z[resupend] = -part_prop['water_depth'].get_values(resupend) + self.info['resuspension_variance'] * np.abs(np.random.randn(resupend.shape[0]))

        # any z out of bounds will  be fixed by find_depth cell at start of next time step

        part_prop['status'].set_values(si.particle_status_flags.moving, resupend)

