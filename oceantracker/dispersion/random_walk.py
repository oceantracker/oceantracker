import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.dispersion._base_dispersion import _BaseTrajectoryModifer
from numba import njit, types as nbtypes
from oceantracker.util.numba_util import njitOT

from random import normalvariate
from oceantracker.util.numba_util import njitOT

class RandomWalk(_BaseTrajectoryModifer):
    # add random walk using velocity modifier
    def __init__(self):
        # set up default params
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'A_H': PVC(0.1,float,min=0.), 'A_V': PVC(0.01,float,min=0.),
                                   } )

    def check_requirements(self):
        si = self.shared_info
        if si.settings['use_A_Z_profile']:
                self.check_class_required_fields_prop_etc(requires3D=True,
                                                            required_props_list=['nz_cell', 'x', 'n_cell'],
                                                          crumbs='random walk with use_A_Z_profile')

    def initial_setup(self):
        si = self.shared_info
        info = self.info
        dt = si.settings['time_step']
        info['random_walk_size'] = np.array((self.calc_walk(self.params['A_H'], dt), self.calc_walk(self.params['A_H'], dt), self.calc_walk(self.params['A_V'], dt)))
        if not si.is3D_run:
            info['random_walk_size'] = info['random_walk_size'][:2]

        info['random_walk_velocity'] = info['random_walk_size'] /si.settings['time_step']  # velocity equivalent of random walk distance

    def calc_walk(self, A_turb, dt):
        # this is variance of particle motion in each vector direction,
        # ( factor of 2 would  be 6 , if wanting 3D isotropic variance, rather than its separate effect on 1D components used above)
        return np.sqrt(2. * np.abs(dt) * np.abs(A_turb))

    # apply random walk
    def update(self, n_time_step,time_sec, active):
        # add up 2D/3D diffusion coeff as random walk done using velocity_modifier
        si= self.shared_info
        part_prop = si.classes['particle_properties']

        if  si.is3D_run:
            self._add_random_walk_velocity3D_modifier_constantAZ(self.info['random_walk_velocity'],
                                                                 active, part_prop['velocity_modifier'].data )
        else:
            self._add_random_walk_velocity2D_modifier_constantAZ(self.info['random_walk_velocity'],
                                                                 active, part_prop['velocity_modifier'].data )

    @staticmethod
    @njitOT
    def _add_random_walk_velocity2D_modifier_constantAZ(random_walk_velocity, active, velocity_modifier):
        for n in active:
            for m in range(2):
                # todo below slow? is allocating memory??, try math.random random.Genetaor.normal  and get 2-3 at same time above?
                velocity_modifier[n,m] += normalvariate(0., random_walk_velocity[m])

    @staticmethod
    @njitOT
    def _add_random_walk_velocity3D_modifier_constantAZ(random_walk_velocity, active, velocity_modifier):
        for n in active:
            for m in range(3):
                # todo below slow? is allocating memory??, try math.random random.Genetaor.normal  and get 2-3 at same time above?
                velocity_modifier[n,m] += normalvariate(0., random_walk_velocity[m])

